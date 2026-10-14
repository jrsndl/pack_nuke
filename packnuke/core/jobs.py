"""Job description shared by the GUI (writer) and the farm job (reader).

Package layout::

    <job>/_pack_nuke/settings.json     complete settings used for this package
    <job>/_pack_nuke/job.json          places, timestamp and every script with its tokens
    <job>/_pack_nuke/nuke_files.csv    human readable index of the scripts
    <job>/_pack_nuke/reports/<id>.*    one report per packed script (written by the farm)

Tokens travel as JSON, so nested anatomy (``{project[name]}``) and values containing ':'
(``z:``) survive - the old ``key:value;`` column dropped them.
"""
from __future__ import annotations

import csv
import getpass
import json
import os
import re
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

from . import paths, settings as settings_mod, templates, tokens as tokens_mod
from .tokens import tags_summary

JOB_FOLDER = '_pack_nuke'
JOB_FILE = 'job.json'
SETTINGS_FILE = 'settings.json'
INDEX_FILE = 'nuke_files.csv'
REPORTS_FOLDER = 'reports'
JOB_VERSION = 2


@dataclass
class JobScript:
    id: str
    path: str
    name: str = ''
    version: str = ''
    tags: Dict[str, Any] = field(default_factory=dict)     # script path tags only
    tokens: Dict[str, Any] = field(default_factory=dict)   # everything, for templates


@dataclass
class Job:
    job_name: str
    job_path: str
    timestamp: str
    place_source: str
    place_target: str
    scripts: List[JobScript] = field(default_factory=list)
    created: str = ''
    user: str = ''
    version: int = JOB_VERSION

    def script(self, script_id: str) -> Optional[JobScript]:
        for s in self.scripts:
            if s.id == script_id:
                return s
        return None


def make_script_id(index: int, file_name: str) -> str:
    base = file_name[:-3] if file_name.lower().endswith('.nk') else file_name
    base = re.sub(r'[^A-Za-z0-9._-]+', '_', base)
    return '{:04d}_{}'.format(index, base)


def job_dir(job_path: str) -> str:
    return job_path.replace('\\', '/').rstrip('/') + '/' + JOB_FOLDER


def write_job(job: Job, cfg: Mapping[str, Any]) -> str:
    """Write settings.json, job.json and nuke_files.csv. Returns the _pack_nuke folder."""
    folder = job_dir(job.job_path)
    os.makedirs(folder, exist_ok=True)
    os.makedirs(folder + '/' + REPORTS_FOLDER, exist_ok=True)
    job.created = job.created or time.strftime('%Y-%m-%d %H:%M:%S')
    try:
        job.user = job.user or getpass.getuser()
    except Exception:
        job.user = job.user or ''

    cfg = dict(cfg)
    cfg['job'] = dict(cfg.get('job') or {}, path=job.job_path, name=job.job_name, timestamp=job.timestamp)
    settings_mod.save_settings(cfg, folder + '/' + SETTINGS_FILE)

    tmp = folder + '/' + JOB_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(asdict(job), f, indent=2, ensure_ascii=False)
    os.replace(tmp, folder + '/' + JOB_FILE)

    with open(folder + '/' + INDEX_FILE, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['Id', 'Name', 'Version', 'Full Path', 'Tokens', 'Package', 'Source', 'Target'])
        for s in job.scripts:
            w.writerow([s.id, s.name, s.version, s.path, tags_summary(s.tags), job.job_name,
                        job.place_source, job.place_target])
    return folder


def read_job(folder: str) -> Tuple[Job, Dict[str, Any]]:
    """Read job.json + settings.json from a ``_pack_nuke`` folder."""
    folder = folder.replace('\\', '/').rstrip('/')
    with open(folder + '/' + JOB_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    scripts = [JobScript(**s) for s in data.pop('scripts', [])]
    known = {k: v for k, v in data.items() if k in Job.__dataclass_fields__}
    job = Job(scripts=scripts, **known)
    cfg = settings_mod.load_settings(folder + '/' + SETTINGS_FILE)
    return job, cfg


def read_script_list(path: str) -> List[str]:
    """Nuke script paths from a text file: one per line, blank lines and ``#`` comments ignored."""
    out = []
    with open(path, 'r', encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip().strip('"')
            if line and not line.startswith('#'):
                out.append(paths.norm(line))
    return out


def parse_version(file_name: str, version_regex: str = '') -> str:
    if not version_regex:
        return ''
    try:
        m = re.search(version_regex, file_name)
    except re.error:
        return ''
    if not m:
        return ''
    return m.group(1) if m.re.groups and m.group(1) is not None else m.group(0)


def build_job(cfg: Mapping[str, Any], place_source: str, place_target: str, scripts: List[Any],
              stamp: str = '', job_root: str = '', job_name: str = '', version_regex: str = '') -> Job:
    """Build a Job (package description) - used by the GUI and the command line.

    ``scripts``: paths, or ``(path, version)`` tuples. ``job_root`` / ``job_name`` default to the
    settings templates (job.job_root / job.job_name_default) filled from the source place.
    """
    stamp = stamp or tokens_mod.timestamp()
    base = tokens_mod.place_tokens(cfg, place_source, place_target, stamp)
    job_name = job_name or tokens_mod.job_name(cfg, base)
    job_root = paths.norm(job_root) or tokens_mod.job_root(cfg, base)
    job_path = templates.join_template(job_root, job_name)
    job = Job(job_name=job_name, job_path=job_path, timestamp=stamp,
              place_source=place_source, place_target=place_target)
    for item in scripts:
        path, version = (item if isinstance(item, (tuple, list)) else (item, None))
        path = paths.norm(path)
        name = paths.basename(path)
        if version is None:
            version = parse_version(name, version_regex)
        job.scripts.append(JobScript(
            id=make_script_id(len(job.scripts), name), path=path, name=name, version=version or '',
            tags=tokens_mod.script_tags(cfg, place_source, path),
            tokens=tokens_mod.build_tokens(cfg, place_source, place_target, path, stamp, job_path, job_name)))
    return job
