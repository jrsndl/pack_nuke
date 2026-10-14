"""settings.json: defaults, loading, migration and validation.

``load_settings`` always returns a complete dictionary (defaults deep-merged under the
file content), so the rest of the code never has to guard against missing keys.
"""
from __future__ import annotations

import copy
import json
import os
import re
from typing import Any, Dict, List, Mapping, Tuple

from . import filters, templates

SCHEMA_VERSION = 3
PLATFORMS = ('Windows', 'Linux', 'Darwin')


class SettingsError(Exception):
    pass


DEFAULT_CATEGORY = {
    'path': {
        'root_template': '{job}/{category}',
        'root_template_relink': '{job}/{category}',
        'top_folder': '{node}',
        'top_folder_relink': '{node}',
    },
    'filter_options': {
        'skip_disconnected': True,
        'skip_disabled': True,
        'combine_filters': 'AND',
    },
    'filters': [],
}

# Built-in categories: fixed names, no filters (what they hold is decided by the scan).
SPECIAL_CATEGORIES = ('fonts', 'gizmos', 'ocio')
SPECIAL_DEFAULTS: Dict[str, Dict[str, Any]] = {
    'fonts': {'special': 'fonts', 'enabled': True,
              'path': {'root_template': '{job}/_shared', 'root_template_relink': '{job}/_shared',
                       'top_folder': 'fonts', 'top_folder_relink': 'fonts'},
              'filter_options': {'skip_disconnected': True, 'skip_disabled': True}},
    'gizmos': {'special': 'gizmos', 'enabled': True, 'to_groups': False,
               'path': {'root_template': '{job}/_shared', 'root_template_relink': '{job}/_shared',
                        'top_folder': 'gizmos', 'top_folder_relink': 'gizmos'},
               'filter_options': {'skip_disconnected': True, 'skip_disabled': True}},
    'ocio': {'special': 'ocio', 'enabled': True, 'relative': True, 'max_files': 5000,
             'path': {'root_template': '{job}/_shared', 'root_template_relink': '{job}/_shared',
                      'top_folder': 'ocio', 'top_folder_relink': 'ocio'},
             'filter_options': {}},
}
_PATH_KEYS = ('root_template', 'root_template_relink', 'top_folder', 'top_folder_relink')


def is_special(name: str) -> bool:
    return name in SPECIAL_CATEGORIES


def media_categories(cfg: Mapping[str, Any]) -> Dict[str, Any]:
    """Regular (filter based) categories, in order."""
    return {k: v for k, v in (cfg.get('categories') or {}).items() if not is_special(k)}


def special(cfg: Mapping[str, Any], kind: str) -> Dict[str, Any]:
    """A built-in category as one flat dict: enabled, root_template..., skip_*, and its extras."""
    cat = templates.deep_merge(SPECIAL_DEFAULTS[kind], (cfg.get('categories') or {}).get(kind) or {})
    flat = {k: v for k, v in cat.items() if k not in ('path', 'filter_options')}
    flat.update(cat.get('path') or {})
    flat.update(cat.get('filter_options') or {})
    return flat

DEFAULTS: Dict[str, Any] = {
    'schema_version': SCHEMA_VERSION,
    'job': {
        'job_name_default': '{place_source}2{place_target}_{timestamp}',
        'job_name_check': '',
        'job_root': '',
    },
    'nuke_scripts': {
        'source': {'copy': True, 'path': '{job}/{script_name}_source.nk'},
        'package': {
            'copy': True,
            'path': '{job}/{script_name}_package.nk',
            'relative': True,
            'relative_custom_project': False,
            'relative_custom_project_template': '{job}',
            'relative_above_script': 0,
        },
        'target': {
            'copy': False,
            'path': '{job}/{script_name}_target.nk',
            'path_relink': '{job}/{script_name}_target.nk',
            'relative': True,
            'relative_custom_project': False,
            'relative_custom_project_template': '{job}',
            'relative_above_script': 0,
        },
    },
    'hashes': {'hashes_generate': False},
    'copy': {'threads': 8, 'skip_identical': True},
    'packing': {
        'category_match': 'all',       # 'all' = copy to every matching category, 'first' = first match only
        'fail_on_missing': False,      # missing source files fail the farm job
        'mark_nodes': True,            # colour relinked nodes in the packaged scripts
        'include_write_nodes': False,  # Write-type nodes are outputs and are skipped by default
    },
    'places': {},
    'categories': {},
    'nuke': {p: '' for p in PLATFORMS},
    'deadline': {p: '' for p in PLATFORMS},
    'deadline_python': {p: '' for p in PLATFORMS},
    'deadline_job': {
        'pool': '',
        'group': '',
        'priority': 50,
        'department': '',
        'LimitGroups': '',
        'comment': '',
    },
}

DEFAULT_PLACE = {
    'anatomy': {},
    'use_script_path_tags': False,
    'script_path_tags': [],
}

DEFAULT_PATH_TAG = {
    'name': 'TAG',
    'source': filters.SOURCE_FILE_NAME,
    'search': '',
    'replace': '',
    'lowercase': False,
    'uppercase': False,
}

WRITE_CLASSES = ('Write', 'WriteGeo', 'DeepWrite', 'WriteTank', 'Precomp')


def defaults() -> Dict[str, Any]:
    return copy.deepcopy(DEFAULTS)


def migrate(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Bring an older settings dict up to the current schema (non-destructive copy)."""
    data = copy.deepcopy(dict(data))
    # v2 -> v3: top level fonts / gizmos / ocio sections become built-in categories
    cats = data.setdefault('categories', {}) or {}
    data['categories'] = cats
    for kind in SPECIAL_CATEGORIES:
        old = data.pop(kind, None)
        if isinstance(old, dict) and kind not in cats:
            new: Dict[str, Any] = {'special': kind, 'path': {}, 'filter_options': {}}
            for k, v in old.items():
                if k in _PATH_KEYS:
                    new['path'][k] = v
                elif k in ('skip_disconnected', 'skip_disabled'):
                    new['filter_options'][k] = v
                elif k not in ('subfolders',):
                    new[k] = v
            cats[kind] = new
    for cat in (data.get('categories') or {}).values():
        for flt in cat.get('filters') or []:
            if 'source' in flt:
                flt['source'] = filters.canonical_source(flt['source'])
    for place in (data.get('places') or {}).values():
        place.pop('is_source', None)
        place.pop('is_target', None)
        for tag in place.get('script_path_tags') or []:
            if 'source' in tag:
                tag['source'] = filters.canonical_source(tag['source'])
    data['schema_version'] = SCHEMA_VERSION
    return data


def complete(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Migrate and deep-merge defaults under ``data``."""
    data = migrate(data)
    out = templates.deep_merge(defaults(), data)
    # built-in categories always exist, after the regular ones
    cats = {k: v for k, v in out['categories'].items() if not is_special(k)}
    for kind in SPECIAL_CATEGORIES:
        cats[kind] = templates.deep_merge(SPECIAL_DEFAULTS[kind], out['categories'].get(kind) or {})
        cats[kind]['special'] = kind
        cats[kind].pop('filters', None)
    out['categories'] = cats
    for name, place in list(out['places'].items()):
        out['places'][name] = templates.deep_merge(DEFAULT_PLACE, place)
    return out


def load_settings(path: str) -> Dict[str, Any]:
    if not path or not os.path.isfile(path):
        raise SettingsError('Settings file not found: {}'.format(path))
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise SettingsError('Settings file {} is not valid JSON: {}'.format(path, e))
    except OSError as e:
        raise SettingsError('Cannot read settings file {}: {}'.format(path, e))
    if not isinstance(data, dict):
        raise SettingsError('Settings file {} must contain a JSON object'.format(path))
    return complete(data)


def save_settings(data: Mapping[str, Any], path: str) -> None:
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        f.write('\n')
    os.replace(tmp, path)


def platform_value(section: Mapping[str, Any], system: str) -> str:
    value = (section or {}).get(system) or ''
    return str(value).replace('\\', '/')


# ------------------------------------------------------------------ validation

Issue = Tuple[str, str]  # (level 'error'|'warning', message)


def validate(data: Mapping[str, Any]) -> List[Issue]:
    """Check a complete settings dict. Returns a list of (level, message)."""
    issues: List[Issue] = []

    def err(msg):
        issues.append(('error', msg))

    def warn(msg):
        issues.append(('warning', msg))

    def check_regex(where, pattern):
        if pattern:
            e = filters.regex_error(pattern)
            if e:
                err('{}: invalid regular expression "{}" ({})'.format(where, pattern, e))

    places = data.get('places') or {}
    if len(places) < 2:
        err('At least two places are required in "places" (found {}).'.format(len(places)))
    for pname, place in places.items():
        if not isinstance(place.get('anatomy', {}), dict):
            err('places.{}.anatomy must be an object'.format(pname))
        for i, tag in enumerate(place.get('script_path_tags') or []):
            where = 'places.{}.script_path_tags[{}] ({})'.format(pname, i, tag.get('name'))
            check_regex(where, tag.get('search'))
            if tag.get('source') not in (filters.SOURCE_FILE_NAME, filters.SOURCE_FILE_PATH):
                err('{}: source must be "File Name" or "File Path"'.format(where))
            rep = tag.get('replace') or ''
            if re.search(r'(?<!\\)/\d', rep) and '\\' not in rep:
                warn('{}: replace "{}" looks like a typo for a group reference "\\1"'.format(where, rep))
            if re.search(r'\{\d+-\d+\}', tag.get('search') or ''):
                warn('{}: "{{a-b}}" is not a regex quantifier, use "{{a,b}}"'.format(where))

    check_regex('job.job_name_check', data['job'].get('job_name_check'))

    for cname, cat in (data.get('categories') or {}).items():
        for key in ('root_template', 'root_template_relink'):
            if not (cat.get('path') or {}).get(key):
                err('categories.{}.path.{} is empty'.format(cname, key))
        if is_special(cname):
            continue
        combine = str((cat.get('filter_options') or {}).get('combine_filters', 'AND')).upper()
        if combine not in ('AND', 'OR'):
            err('categories.{}.filter_options.combine_filters must be AND or OR'.format(cname))
        for i, flt in enumerate(cat.get('filters') or []):
            where = 'categories.{}.filters[{}]'.format(cname, i)
            if flt.get('source') not in filters.SOURCES:
                err('{}: unknown source "{}" (use one of {})'.format(where, flt.get('source'), ', '.join(filters.SOURCES)))
            if flt.get('source') != filters.SOURCE_NODE_CLASS:
                check_regex(where, flt.get('search'))
    if not media_categories(data):
        warn('No categories defined, the built-in default category will be used.')

    if data['packing'].get('category_match') not in ('all', 'first'):
        err('packing.category_match must be "all" or "first"')
    try:
        if int(data['copy'].get('threads', 8)) < 1:
            err('copy.threads must be at least 1')
    except (TypeError, ValueError):
        err('copy.threads must be a number')
    try:
        int(data['deadline_job'].get('priority', 50))
    except (TypeError, ValueError):
        err('deadline_job.priority must be a number')
    return issues


def errors_only(issues: List[Issue]) -> List[str]:
    return [m for lvl, m in issues if lvl == 'error']
