"""Regex/class filters used by categories and by script path tags.

All matching is None-safe: a regex that doesn't match, or has no capture group, never
raises. Invalid regular expressions are reported by settings validation, before any
packing starts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Mapping, Optional, Tuple

SOURCE_FILE_NAME = 'File Name'
SOURCE_FILE_PATH = 'File Path'
SOURCE_NODE_CLASS = 'Node Class'
SOURCE_KNOB_NAME = 'Knob Name'
SOURCES = (SOURCE_FILE_NAME, SOURCE_FILE_PATH, SOURCE_NODE_CLASS, SOURCE_KNOB_NAME)
# names used by older settings files
SOURCE_ALIASES = {'Full Path': SOURCE_FILE_PATH, 'Path': SOURCE_FILE_PATH, 'Class': SOURCE_NODE_CLASS}


def canonical_source(source: str) -> str:
    return SOURCE_ALIASES.get(source, source)


@lru_cache(maxsize=512)
def compile_regex(pattern: str) -> 're.Pattern[str]':
    return re.compile(pattern)


def regex_error(pattern: str) -> Optional[str]:
    try:
        compile_regex(pattern)
        return None
    except re.error as e:
        return str(e)


def first_group(match: 're.Match[str]') -> str:
    """Group 1 if the regex has groups, else the whole match."""
    if match.re.groups >= 1 and match.group(1) is not None:
        return match.group(1)
    return match.group(0)


# ------------------------------------------------------------------ category filters

@dataclass
class FilterResult:
    hit: bool
    value: Optional[str]


def eval_filter(flt: Mapping[str, Any], subject: Mapping[str, str]) -> FilterResult:
    """Evaluate one category filter against a subject.

    ``subject`` has keys 'File Name', 'File Path', 'Node Class', 'Knob Name'.

    * regex sources: value = first group (or whole match). Hit = matched; when ``check``
      is non-empty, hit = value is in check (case-insensitive).
    * Node Class: ``search`` is a space separated class list; value = the class.
    * ``invert`` flips the hit.
    """
    source = canonical_source(flt.get('source', SOURCE_FILE_NAME))
    search = flt.get('search', '') or ''
    check = [str(c).lower() for c in (flt.get('check') or [])]
    text = subject.get(source, '') or ''

    if source == SOURCE_NODE_CLASS:
        classes = search.split()
        value = text if text in classes else None
        hit = value is not None
    else:
        m = compile_regex(search).search(text) if search else None
        value = first_group(m) if m else None
        if check:
            hit = value is not None and value.lower() in check
        else:
            hit = m is not None

    if flt.get('invert'):
        hit = not hit
    return FilterResult(hit, value)


def match_category(category: Mapping[str, Any], subject: Mapping[str, str],
                   disabled: bool, disconnected: bool) -> Tuple[bool, Dict[str, str], str]:
    """Does an item belong to a category? Returns (matched, tokens, reason)."""
    opts = category.get('filter_options') or {}
    if opts.get('skip_disconnected') and disconnected:
        return False, {}, 'disconnected'
    if opts.get('skip_disabled') and disabled:
        return False, {}, 'disabled'
    filters = category.get('filters') or []
    if not filters:
        return True, {}, ''
    tokens: Dict[str, str] = {}
    hits = 0
    for flt in filters:
        res = eval_filter(flt, subject)
        if res.hit:
            hits += 1
            name = flt.get('token_name')
            if name and res.value is not None:
                tokens[name] = res.value
    combine = str(opts.get('combine_filters', 'AND')).upper()
    ok = hits == len(filters) if combine == 'AND' else hits > 0
    return ok, tokens, '' if ok else 'filters'


# ------------------------------------------------------------------ script path tags

def eval_path_tag(tag: Mapping[str, Any], full_path: str) -> Optional[str]:
    """Evaluate one ``script_path_tags`` entry against a Nuke script path.

    ``replace`` uses regex expansion (``\\1``) of a match anchored at the start (like the
    original tool); otherwise group 1 / the whole match of a search.
    """
    search = tag.get('search') or ''
    if not search:
        return None
    try:
        rx = compile_regex(search)
    except re.error:
        return None
    full_path = full_path.replace('\\', '/')
    source = canonical_source(tag.get('source', SOURCE_FILE_NAME))
    text = full_path.rsplit('/', 1)[-1] if source == SOURCE_FILE_NAME else full_path

    result = None
    replace = tag.get('replace')
    if replace:
        m = rx.match(text)
        if m:
            try:
                result = m.expand(replace)
            except (re.error, IndexError):
                result = None
    if result is None:
        m = rx.search(text)
        if m:
            result = first_group(m)
    if result is not None:
        if tag.get('lowercase'):
            result = result.lower()
        if tag.get('uppercase'):
            result = result.upper()
    return result


def eval_path_tags(tags: List[Mapping[str, Any]], full_path: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for tag in tags or []:
        name = tag.get('name')
        if not name:
            continue
        value = eval_path_tag(tag, full_path)
        if value is not None:
            out[name] = value
    return out
