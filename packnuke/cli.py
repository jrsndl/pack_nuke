"""Command line front end: pack Nuke scripts without the GUI.

    python pack_nuke_cli.py --preset bcv048 --source bc --target out sh010_comp_v003.nk
    python pack_nuke_cli.py --settings settings.json --source bc --target out --list scripts.txt --mode write

Prints the package root (job folder) on stdout - and nothing else, so it can be captured:

    for /f "delims=" %p in ('python pack_nuke_cli.py ...') do set PKG=%p

Everything else (progress, problems) goes to stderr. Exit codes: 0 ok, 1 packing / submission
failed, 2 bad input or the pre-submit check found problems.

Same building blocks as the GUI: settings or a preset (embedded settings), places, job name
and folder from the settings templates, the same checks, Deadline submission or a local run.
"""
from __future__ import annotations

import argparse
import configparser
import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .core import jobs, paths, preflight, settings as settings_mod
from .farm import deadline

log = logging.getLogger('packnuke.cli')

EXIT_OK, EXIT_FAILED, EXIT_BAD_INPUT = 0, 1, 2
MODES = ('submit', 'local', 'write')


def app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return paths.norm(os.path.dirname(sys.executable))
    return paths.norm(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog='pack_nuke_cli',
        description='Pack Nuke scripts from the command line. Prints the package root folder on stdout.',
        epilog='Example: pack_nuke_cli.py --preset bcv048 --source bc --target out --list scripts.txt')
    src = p.add_mutually_exclusive_group()
    src.add_argument('--preset', help='preset name (from the presets folder) or path to a preset .json')
    src.add_argument('--settings', help='path to a settings.json (default: settings.json next to the app)')
    p.add_argument('--presets-folder', help='presets folder (default: presets_folder from settings.ini)')
    p.add_argument('scripts', nargs='*', help='Nuke script(s) to pack')
    p.add_argument('--list', action='append', default=[], metavar='FILE',
                   help='text file with one Nuke script path per line (# comments allowed); repeatable')
    p.add_argument('--source', help='source place (default: from the preset)')
    p.add_argument('--target', help='target place (default: from the preset)')
    p.add_argument('--job-root', help='override the job root folder (default: settings job.job_root)')
    p.add_argument('--job-name', help='override the job name (default: settings job.job_name_default)')
    p.add_argument('--version-regex', help='regex for the version shown in nuke_files.csv (default: from the preset)')
    p.add_argument('--mode', choices=MODES, default='submit',
                   help='submit = Deadline (default), local = run nuke -t here one script after another, '
                        'write = only create the package job files')
    p.add_argument('--check', action='store_true', help='only run the checks and print the package root')
    p.add_argument('--json', action='store_true', help='print a JSON summary on stdout instead of the root')
    p.add_argument('-v', '--verbose', action='store_true')
    p.add_argument('-q', '--quiet', action='store_true', help='only errors on stderr')
    return p.parse_args(list(argv))


def setup_logging(verbose: bool, quiet: bool) -> None:
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(logging.Formatter('%(levelname)-7s %(message)s'))
    root.addHandler(h)
    root.setLevel(logging.ERROR if quiet else (logging.DEBUG if verbose else logging.INFO))


# ------------------------------------------------------------------ settings / preset

def ini_presets_folder(folder: str) -> str:
    """presets_folder from settings.ini (QSettings INI, [General] section)."""
    ini = os.path.join(folder, 'settings.ini')
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        cp.read(ini, encoding='utf-8')
        value = cp.get('General', 'presets_folder', fallback='').strip().strip('"')
    except (configparser.Error, OSError, UnicodeDecodeError):
        value = ''
    return paths.norm(value) or paths.join(folder, 'presets')


def resolve_preset(name_or_path: str, presets_folder: str) -> str:
    if os.path.isfile(name_or_path):
        return paths.norm(name_or_path)
    name = name_or_path[:-5] if name_or_path.lower().endswith('.json') else name_or_path
    return paths.join(presets_folder, name + '.json')


def load_config(args: argparse.Namespace) -> Tuple[Dict[str, Any], Dict[str, Any], str]:
    """Returns (settings, preset gui values, description of the source)."""
    folder = app_dir()
    if args.preset:
        presets = paths.norm(args.presets_folder) if args.presets_folder else ini_presets_folder(folder)
        path = resolve_preset(args.preset, presets)
        if not os.path.isfile(path):
            raise settings_mod.SettingsError('Preset not found: {} (presets folder {})'.format(path, presets))
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        gui = data.get('gui') or {}
        if isinstance(data.get('settings'), dict):
            return settings_mod.complete(data['settings']), gui, 'preset {}'.format(path)
        legacy = data.get('settings_file') or ''
        log.warning('Preset %s has no embedded settings; using its settings file %s', path, legacy)
        return settings_mod.load_settings(legacy), gui, 'preset {} -> {}'.format(path, legacy)
    path = paths.norm(args.settings) if args.settings else paths.join(folder, 'settings.json')
    return settings_mod.load_settings(path), {}, 'settings {}'.format(path)


def collect_scripts(args: argparse.Namespace) -> List[str]:
    scripts = [paths.norm(os.path.abspath(s)) for s in args.scripts]
    for lst in args.list:
        scripts.extend(jobs.read_script_list(lst))
    seen, out = set(), []
    for s in scripts:
        if s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out


# ------------------------------------------------------------------ actions

def run_local(cfg: Dict[str, Any], job: jobs.Job) -> int:
    nuke_exe = settings_mod.platform_value(cfg.get('nuke') or {}, deadline.system_name())
    if not nuke_exe or not os.path.isfile(nuke_exe):
        log.error('Nuke executable not found: %s (settings nuke.%s)', nuke_exe, deadline.system_name())
        return EXIT_BAD_INPUT
    entry = paths.join(app_dir(), 'pack_nuke.py')
    failed = 0
    for i, script in enumerate(job.scripts, 1):
        log.info('[%d/%d] packing %s', i, len(job.scripts), script.path)
        cmd = [nuke_exe, '-t', entry, '--job-dir', jobs.job_dir(job.job_path), '--id', script.id]
        try:
            proc = subprocess.run(cmd, stdout=sys.stderr, stderr=subprocess.STDOUT)
            code = proc.returncode
        except OSError as e:
            log.error('Cannot run Nuke: %s', e)
            code = -1
        if code != 0:
            failed += 1
            log.error('%s failed (exit code %s), see %s/%s/%s.csv', script.id, code, jobs.job_dir(job.job_path),
                      jobs.REPORTS_FOLDER, script.id)
    log.info('Local packing: %d ok, %d failed.', len(job.scripts) - failed, failed)
    return EXIT_FAILED if failed else EXIT_OK


def run_submit(cfg: Dict[str, Any], job: jobs.Job, results: List[Dict[str, Any]]) -> int:
    failed = 0
    for script in job.scripts:
        res = deadline.submit_script(cfg, job, script)
        results.append({'id': script.id, 'ok': res.ok, 'job_id': res.job_id, 'error': res.error})
        if res.ok:
            log.info('Submitted %s -> Deadline job %s', script.id, res.job_id)
        else:
            failed += 1
            log.error('Submitting %s failed: %s', script.id, res.error or res.output)
    log.info('Deadline: %d submitted, %d failed.', len(job.scripts) - failed, failed)
    return EXIT_FAILED if failed else EXIT_OK


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    setup_logging(args.verbose, args.quiet)

    try:
        cfg, gui, source = load_config(args)
    except (settings_mod.SettingsError, OSError, ValueError) as e:
        log.error('%s', e)
        return EXIT_BAD_INPUT
    log.info('Settings from %s', source)

    place_source = args.source or gui.get('place_source') or ''
    place_target = args.target or gui.get('place_target') or ''
    if not place_source or not place_target:
        log.error('Source and target place are required (--source / --target); places in the settings: %s',
                  ', '.join(cfg.get('places') or {}) or '-')
        return EXIT_BAD_INPUT
    try:
        scripts = collect_scripts(args)
    except OSError as e:
        log.error('Cannot read script list: %s', e)
        return EXIT_BAD_INPUT

    job = jobs.build_job(cfg, place_source, place_target, scripts, job_root=args.job_root or '',
                         job_name=args.job_name or '',
                         version_regex=args.version_regex or gui.get('search_version_regex') or '')
    problems = preflight.check_job(cfg, job)
    if args.mode == 'submit':
        problems.extend(deadline.check_executables(cfg))
    summary: Dict[str, Any] = {'package_root': job.job_path, 'job_name': job.job_name,
                               'place_source': place_source, 'place_target': place_target,
                               'mode': 'check' if args.check else args.mode,
                               'scripts': [{'id': s.id, 'path': s.path} for s in job.scripts],
                               'problems': problems, 'submitted': []}

    def finish(code: int) -> int:
        summary['exit_code'] = code
        if args.json:
            print(json.dumps(summary, indent=2))
        elif code != EXIT_BAD_INPUT:
            print(job.job_path)
        sys.stdout.flush()
        return code

    if problems:
        for p in problems:
            log.error('check: %s', p)
        return finish(EXIT_BAD_INPUT)
    log.info('Check OK: %d script(s), package %s', len(job.scripts), job.job_path)
    if args.check:
        return finish(EXIT_OK)

    try:
        folder = jobs.write_job(job, cfg)
    except OSError as e:
        log.error('Writing job files failed: %s', e)
        return finish(EXIT_FAILED)
    log.info('Job files written to %s', folder)

    if args.mode == 'write':
        return finish(EXIT_OK)
    if args.mode == 'local':
        return finish(run_local(cfg, job))
    return finish(run_submit(cfg, job, summary['submitted']))


if __name__ == '__main__':
    sys.exit(main())
