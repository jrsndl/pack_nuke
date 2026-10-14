"""Token (anatomy) building for a Nuke script, shared by the GUI and the farm job.

Token sources, later ones win:
    1. source place ``anatomy`` (may be nested: ``{project[name]}``)
    2. ``place_source``, ``place_target``, ``timestamp``
    3. script path tags of the source place (``SHOT``, ``TASK``, ...)
    4. ``script_path``, ``script_dir``, ``script_name``, ``script_file``
    5. ``job_name`` and ``job`` (full job folder) once known
"""
from __future__ import annotations

import copy
import datetime
from typing import Any, Dict, Mapping, Optional

from . import filters, paths, templates


def timestamp(now: Optional[datetime.datetime] = None) -> str:
    """UTC time plus the local UTC offset for humans: ``YYMMDD_HHMM_0200`` / ``..._-0500``.

    A positive offset has no sign (kept compatible with existing ``job_name_check`` regexes).
    """
    now = now or datetime.datetime.now(datetime.timezone.utc)
    utc = now.astimezone(datetime.timezone.utc).strftime('%y%m%d_%H%M_')
    offset = now.astimezone().strftime('%z').replace('+', '')
    return utc + offset


def place_tokens(settings: Mapping[str, Any], place_source: str, place_target: str,
                 stamp: str) -> Dict[str, Any]:
    place = (settings.get('places') or {}).get(place_source) or {}
    tokens: Dict[str, Any] = copy.deepcopy(place.get('anatomy') or {})
    tokens.update({'place_source': place_source, 'place_target': place_target, 'timestamp': stamp})
    return tokens


def script_tags(settings: Mapping[str, Any], place_source: str, script_path: str) -> Dict[str, str]:
    place = (settings.get('places') or {}).get(place_source) or {}
    if not place.get('use_script_path_tags'):
        return {}
    return filters.eval_path_tags(place.get('script_path_tags') or [], script_path)


def script_tokens(script_path: str) -> Dict[str, str]:
    p = paths.norm(script_path)
    file_name = paths.basename(p)
    name = file_name[:-3] if file_name.lower().endswith('.nk') else file_name
    return {'script_path': p, 'script_dir': paths.dirname(p), 'script_file': file_name, 'script_name': name}


def job_name(settings: Mapping[str, Any], tokens: Mapping[str, Any], strict: bool = False) -> str:
    return templates.format_template(settings['job'].get('job_name_default', ''), tokens, strict=strict)


def job_root(settings: Mapping[str, Any], tokens: Mapping[str, Any], strict: bool = False) -> str:
    return paths.norm(templates.format_template(settings['job'].get('job_root', ''), tokens, strict=strict))


def build_tokens(settings: Mapping[str, Any], place_source: str, place_target: str, script_path: str,
                 stamp: str, job_folder: Optional[str] = None, job_name_value: Optional[str] = None
                 ) -> Dict[str, Any]:
    """All tokens for one script. ``job``/``job_name`` are filled in when given."""
    tokens = place_tokens(settings, place_source, place_target, stamp)
    tokens.update(script_tags(settings, place_source, script_path))
    tokens.update(script_tokens(script_path))
    if job_name_value:
        tokens['job_name'] = job_name_value
    if job_folder:
        tokens['job'] = paths.norm(job_folder)
    return tokens


def tags_summary(tags: Mapping[str, Any]) -> str:
    """One-line ``KEY=value; KEY=value`` text for table cells."""
    return '; '.join('{}={}'.format(k, v) for k, v in templates.flatten(dict(tags)))
