"""Deadline submission (no Qt, so it can be reused by an Ayon integration).

Each script becomes one CommandLine job running ``nuke -t pack_nuke.py --job-dir .. --id ..``;
all jobs of one package share a Deadline batch name. Jobs are submitted with job/plugin info
files (``deadlinecommand <job.info> <plugin.info>``), which avoids command line quoting problems.
"""
from __future__ import annotations

import os
import platform
import re
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

from ..core import jobs, settings as settings_mod


@dataclass
class SubmitResult:
    script_id: str
    ok: bool
    job_id: str = ''
    output: str = ''
    error: str = ''
    command: Optional[List[str]] = None


def system_name() -> str:
    return platform.system()


def check_executables(cfg: Mapping[str, Any], system: Optional[str] = None) -> List[str]:
    system = system or system_name()
    problems = []
    for key, label in (('deadline', 'Deadline command'), ('nuke', 'Nuke executable'),
                       ('deadline_python', 'pack_nuke.py for the farm')):
        value = settings_mod.platform_value(cfg.get(key) or {}, system)
        if not value:
            problems.append('{} is not set for {} (settings: {}.{})'.format(label, system, key, system))
        elif key != 'deadline_python' and not os.path.isfile(value):
            # pack_nuke.py is a farm path and may not be visible from this machine, so it is not checked
            problems.append('{} not found: {}'.format(label, value))
    return problems


def farm_arguments(cfg: Mapping[str, Any], job_folder: str, script_id: str,
                   system: Optional[str] = None) -> List[str]:
    py = settings_mod.platform_value(cfg.get('deadline_python') or {}, system or system_name())
    return ['-t', py, '--job-dir', job_folder, '--id', script_id]


def job_info(cfg: Mapping[str, Any], job: jobs.Job, script: jobs.JobScript) -> Dict[str, str]:
    dj = cfg.get('deadline_job') or {}
    info = {
        'Plugin': 'CommandLine',
        'Name': '{} | {}'.format(job.job_name, script.id),
        'BatchName': job.job_name,
        'Priority': str(int(dj.get('priority', 50))),
        'OutputDirectory0': jobs.job_dir(job.job_path),
    }
    for key, name in (('pool', 'Pool'), ('group', 'Group'), ('department', 'Department'),
                      ('LimitGroups', 'LimitGroups'), ('comment', 'Comment')):
        if dj.get(key):
            info[name] = str(dj[key])
    return info


def plugin_info(cfg: Mapping[str, Any], job: jobs.Job, script: jobs.JobScript,
                system: Optional[str] = None) -> Dict[str, str]:
    system = system or system_name()
    nuke_exe = settings_mod.platform_value(cfg.get('nuke') or {}, system)
    arguments = subprocess.list2cmdline(farm_arguments(cfg, jobs.job_dir(job.job_path), script.id, system))
    return {'Executable': nuke_exe, 'Arguments': arguments, 'Shell': 'default', 'ShellExecute': 'False'}


def write_submission_files(cfg: Mapping[str, Any], job: jobs.Job, script: jobs.JobScript,
                           system: Optional[str] = None) -> Tuple[str, str]:
    """Job/plugin info files in <pkg>/_pack_nuke/deadline/ (no command line quoting issues,
    and the exact submission stays in the package for debugging)."""
    folder = jobs.job_dir(job.job_path) + '/deadline'
    os.makedirs(folder, exist_ok=True)
    out = []
    for suffix, data in (('job', job_info(cfg, job, script)), ('plugin', plugin_info(cfg, job, script, system))):
        path = '{}/{}_{}.info'.format(folder, script.id, suffix)
        with open(path, 'w', encoding='utf-8', newline='\n') as f:
            for k, v in data.items():
                f.write('{}={}\n'.format(k, str(v).replace('\n', ' ')))
        out.append(path)
    return out[0], out[1]


def build_command(cfg: Mapping[str, Any], job: jobs.Job, script: jobs.JobScript,
                  system: Optional[str] = None) -> List[str]:
    system = system or system_name()
    dl = settings_mod.platform_value(cfg.get('deadline') or {}, system)
    job_file, plugin_file = write_submission_files(cfg, job, script, system)
    return [dl, job_file, plugin_file]


def run_command(cmd: List[str], timeout: float = 120) -> subprocess.CompletedProcess:
    kwargs = {'stdout': subprocess.PIPE, 'stderr': subprocess.PIPE, 'text': True, 'timeout': timeout}
    if os.name == 'nt':
        kwargs['creationflags'] = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    return subprocess.run(cmd, **kwargs)


def submit_script(cfg: Mapping[str, Any], job: jobs.Job, script: jobs.JobScript,
                  system: Optional[str] = None) -> SubmitResult:
    cmd = build_command(cfg, job, script, system)
    try:
        proc = run_command(cmd)
    except (OSError, subprocess.SubprocessError) as e:
        return SubmitResult(script.id, False, error=str(e), command=cmd)
    out = (proc.stdout or '').strip()
    err = (proc.stderr or '').strip()
    m = re.search(r'JobID=(\S+)', out)
    ok = proc.returncode == 0 and m is not None
    if not ok and not err:
        err = 'deadlinecommand returned {}{}'.format(proc.returncode, '' if m else ', no JobID in output')
    return SubmitResult(script.id, ok, job_id=m.group(1) if m else '', output=out, error=err, command=cmd)
