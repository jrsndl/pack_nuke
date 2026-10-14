"""Pack one Nuke script. Runs inside Nuke: ``nuke -t pack_nuke.py --job-dir <dir> --id <id>``.

Steps:
    1. read job.json + settings.json from the package's ``_pack_nuke`` folder
    2. open the script, record gizmos, optionally convert gizmos to groups
    3. scan file knobs, fonts, OCIO -> build the pack plan (categories, targets, dedup)
    4. copy (parallel, atomic, skip identical), fold results back into the plan
    5. copy the source script, write the relinked package / target scripts
    6. always write the report; exit non-zero when anything failed
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import Any, Dict, List, Optional, Sequence

from ..core import copier, jobs, paths, plan as plan_mod, relink, report, settings as settings_mod, templates

log = logging.getLogger('packnuke')

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_BAD_INPUT = 2


def setup_logging(level: int = logging.INFO) -> None:
    """Log to stdout so Deadline captures it (the old logger had no handler)."""
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-7s %(message)s', '%H:%M:%S'))
    root.addHandler(handler)
    root.setLevel(level)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog='pack_nuke', description='Pack one Nuke script (run with nuke -t).')
    p.add_argument('--job-dir', required=True, help='the package _pack_nuke folder')
    p.add_argument('--id', required=True, help='script id from job.json')
    p.add_argument('--dry-run', action='store_true', help='plan and report only, copy nothing, save nothing')
    p.add_argument('--verbose', action='store_true')
    return p.parse_args(list(argv))


class PackRunner:
    """Orchestrates one script. ``host`` is NukeHost on the farm, a fake in tests."""

    def __init__(self, host, job: jobs.Job, cfg: Dict[str, Any], script: jobs.JobScript,
                 job_folder: str, dry_run: bool = False):
        self.host = host
        self.job = job
        self.cfg = cfg
        self.script = script
        self.job_folder = job_folder
        self.dry_run = dry_run
        self.plan: Optional[plan_mod.PackPlan] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.written: Dict[str, str] = {}
        self.tokens: Dict[str, Any] = dict(script.tokens)
        self.tokens.setdefault('job', paths.norm(job.job_path))
        self.tokens.setdefault('job_name', job.job_name)
        self.tokens.setdefault('timestamp', job.timestamp)
        self.tokens.setdefault('place_source', job.place_source)
        self.tokens.setdefault('place_target', job.place_target)
        self.stats: Dict[str, Any] = {}

    def run(self) -> int:
        t0 = time.time()
        try:
            self._run()
        except templates.TemplateError as e:
            self.errors.append(str(e))
            log.error('%s', e)
        except Exception as e:  # report whatever happened
            self.errors.append('{}: {}'.format(type(e).__name__, e))
            log.exception('Packing failed')
        finally:
            self.stats['seconds'] = round(time.time() - t0, 1)
            self._write_report()
        return EXIT_FAILED if self.errors else EXIT_OK

    def _run(self) -> None:
        cfg = self.cfg
        src = paths.norm(self.script.path)
        log.info('Packing %s (id %s)', src, self.script.id)
        self.host.open_script(src)

        gizmos = self.host.scan_gizmos()
        if settings_mod.special(cfg, 'gizmos').get('to_groups') and gizmos:
            for msg in self.host.convert_gizmos_to_groups():
                log.info('%s', msg)
                if msg.startswith('failed'):
                    self.warnings.append(msg)

        scan = self.host.scan()
        scan.gizmos = gizmos
        self.plan = plan_mod.build_plan(scan, cfg, self.tokens)
        p = self.plan
        self._log_plan()

        if self.dry_run:
            log.info('Dry run: nothing copied or saved.')
            return

        # copy
        want_hash = bool((cfg.get('hashes') or {}).get('hashes_generate'))
        copy_cfg = cfg.get('copy') or {}
        tasks = [copier.CopyTask(c.src, c.dst, c.size) for c in p.copies]
        total_bytes = sum(t.size for t in tasks)
        log.info('Copying %d files (%s) with %s threads%s', len(tasks), copier.human_size(total_bytes),
                 copy_cfg.get('threads', 8), ', hashing' if want_hash else '')
        step = max(1, len(tasks) // 20)

        def on_result(res, done, total):
            if res.status == 'error':
                log.error('copy failed: %s -> %s: %s', res.task.src, res.task.dst, res.error)
            if done % step == 0 or done == total:
                log.info('Progress: %d%% (%d/%d files)', int(done * 100 / max(total, 1)), done, total)

        t0 = time.time()
        results = copier.run_copies(tasks, int(copy_cfg.get('threads', 8)),
                                    bool(copy_cfg.get('skip_identical', True)), want_hash, on_result)
        plan_mod.apply_copy_results(p, results)
        self.stats.update({
            'copy_seconds': round(time.time() - t0, 1),
            'files_copied': sum(1 for r in results if r.status == 'copied'),
            'files_skipped': sum(1 for r in results if r.status == 'skipped'),
            'files_failed': sum(1 for r in results if r.status == 'error'),
            'bytes_total': total_bytes,
        })
        log.info('Copy finished in %.1f s: %d copied, %d already identical, %d failed',
                 self.stats['copy_seconds'], self.stats['files_copied'], self.stats['files_skipped'],
                 self.stats['files_failed'])

        # scripts
        ns = cfg['nuke_scripts']
        if ns['source'].get('copy', True):
            dst = paths.norm(templates.format_template(ns['source']['path'], self.tokens, strict=True))
            res = copier.copy_one(copier.CopyTask(src, dst), skip_identical=False)
            if res.status == 'error':
                self.errors.append('source script copy failed: {}'.format(res.error))
            else:
                self.written['source'] = dst
                log.info('Source script copied to %s', dst)
        for which in ('package', 'target'):
            if not ns[which].get('copy', True):
                continue
            spec = relink.compute_relink(p, cfg, self.tokens, which)
            self.warnings.extend(spec.warnings)
            self.warnings.extend(self.host.apply_relink(spec))
            self.host.save_script_as(spec.save_path)
            self.written[which] = spec.save_path
            log.info('%s script saved to %s (%d knobs relinked%s)', which.capitalize(), spec.save_path,
                     len(spec.ops), ', relative to ' + spec.project_dir if spec.relative else '')

        # errors
        for item in p.items:
            for e in item.errors:
                msg = '{} {} ({}): {}'.format(item.kind, item.node, item.knob, e)
                if msg not in self.errors:
                    self.errors.append(msg)
        if (cfg.get('packing') or {}).get('fail_on_missing'):
            for item in p.items:
                if item.status == plan_mod.ST_MISSING:
                    self.errors.append('missing: {} {} ({})'.format(item.node, item.knob, item.source))

    def _log_plan(self) -> None:
        p = self.plan
        counts: Dict[str, int] = {}
        for item in p.items:
            counts[item.status] = counts.get(item.status, 0) + 1
        log.info('Plan: %d items %s, %d unique files to copy', len(p.items),
                 ', '.join('{}={}'.format(k, v) for k, v in sorted(counts.items())), len(p.copies))
        for item in p.items:
            if item.status in (plan_mod.ST_MISSING, plan_mod.ST_UNCATEGORIZED, plan_mod.ST_ERROR):
                log.warning('%-13s %s %s.%s %s (%s)', item.status, item.kind, item.node, item.knob, item.source,
                            item.reason)
            else:
                log.debug('%-13s %s %s.%s %s', item.status, item.kind, item.node, item.knob, item.source)
        for w in p.warnings:
            log.warning('%s', w)
        for e in p.errors:
            log.error('%s', e)
        self.warnings.extend(p.warnings)

    def _write_report(self) -> None:
        summary = {
            'id': self.script.id,
            'script': self.script.path,
            'job': self.job.job_name,
            'ok': not self.errors,
            'dry_run': self.dry_run,
            'errors': self.errors,
            'warnings': self.warnings,
            'written': self.written,
            'stats': self.stats,
        }
        try:
            out = report.write_report(self.job_folder + '/' + jobs.REPORTS_FOLDER, self.script.id,
                                      self.plan, self.tokens, summary)
            log.info('Report: %s', out['csv'])
        except Exception:
            log.exception('Writing the report failed')
        if self.errors:
            log.error('Packing finished with %d error(s):', len(self.errors))
            for e in self.errors:
                log.error('  %s', e)
        else:
            log.info('Packing finished OK.')


def main(argv: Optional[Sequence[str]] = None, host=None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    setup_logging(logging.DEBUG if args.verbose else logging.INFO)
    job_folder = paths.norm(args.job_dir)
    try:
        job, cfg = jobs.read_job(job_folder)
    except (OSError, ValueError, settings_mod.SettingsError) as e:
        log.critical('Cannot read job from %s: %s', job_folder, e)
        return EXIT_BAD_INPUT
    problems = settings_mod.errors_only(settings_mod.validate(cfg))
    if problems:
        for msg in problems:
            log.critical('settings: %s', msg)
        return EXIT_BAD_INPUT
    script = job.script(args.id)
    if script is None:
        log.critical('Script id %s is not in %s/%s', args.id, job_folder, jobs.JOB_FILE)
        return EXIT_BAD_INPUT
    if host is None:
        from ..nuke_io.host import NukeHost
        host = NukeHost()
    return PackRunner(host, job, cfg, script, job_folder, dry_run=args.dry_run).run()
