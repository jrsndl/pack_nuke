"""Path templates: ``{job}/{SHOT}/{category}``, with nested anatomy like ``{project[name]}``.

One formatter for everything. ``strict=True`` raises :class:`TemplateError` listing every
missing token (farm side, so a bad template fails loudly). ``strict=False`` leaves missing
tokens in place as ``{token}`` (GUI previews).
"""
from __future__ import annotations

import string
from typing import Any, Dict, Iterable, List, Mapping, Set, Tuple


class TemplateError(KeyError):
    def __init__(self, template: str, missing: Iterable[str]):
        self.template = template
        self.missing = sorted(set(missing))
        super().__init__('Template "{}" is missing tokens: {}'.format(template, ', '.join(self.missing)))

    def __str__(self):  # KeyError would add quotes otherwise
        return self.args[0]


class _Missing:
    """Placeholder for a missing token; renders back as ``{name}``."""

    def __init__(self, name: str, sink: Set[str]):
        self._name = name
        self._sink = sink
        sink.add(name)

    def __getitem__(self, key):
        self._sink.discard(self._name)
        return _Missing('{}[{}]'.format(self._name, key), self._sink)

    def __getattr__(self, key):
        if key.startswith('_'):
            raise AttributeError(key)
        self._sink.discard(self._name)
        return _Missing('{}.{}'.format(self._name, key), self._sink)

    def __format__(self, spec):
        return '{' + self._name + '}'

    def __str__(self):
        return '{' + self._name + '}'


class _Formatter(string.Formatter):
    def __init__(self, sink: Set[str]):
        super().__init__()
        self._sink = sink

    def get_value(self, key, args, kwargs):
        if isinstance(key, int):
            return super().get_value(key, args, kwargs)
        if key in kwargs:
            return kwargs[key]
        return _Missing(key, self._sink)

    def get_field(self, field_name, args, kwargs):
        try:
            return super().get_field(field_name, args, kwargs)
        except (KeyError, IndexError, AttributeError, TypeError):
            self._sink.add(field_name)
            return _Missing(field_name, set()), field_name


def format_template(template: str, tokens: Mapping[str, Any], strict: bool = True) -> str:
    """Fill a template. Backslashes are converted to forward slashes."""
    if template is None:
        return ''
    missing: Set[str] = set()
    result = _Formatter(missing).vformat(str(template), (), dict(tokens))
    if missing and strict:
        raise TemplateError(template, missing)
    return result.replace('\\', '/')


def missing_tokens(template: str, tokens: Mapping[str, Any]) -> List[str]:
    missing: Set[str] = set()
    _Formatter(missing).vformat(str(template or ''), (), dict(tokens))
    return sorted(missing)


def template_fields(template: str) -> List[str]:
    """Top level field names used by a template."""
    out = []
    for _lit, field, _spec, _conv in string.Formatter().parse(template or ''):
        if field:
            root = field.split('[', 1)[0].split('.', 1)[0]
            if root not in out:
                out.append(root)
    return out


def join_template(root: str, top: str) -> str:
    """``root/top`` or just ``root`` when ``top`` is empty."""
    root = (root or '').rstrip('/')
    top = (top or '').strip('/')
    return root + '/' + top if top else root


# ---------------------------------------------------------------- nested dict helpers

def flatten(data: Mapping[str, Any], prefix: str = '', sep: str = '.') -> List[Tuple[str, Any]]:
    """``{'project': {'name': 'X'}}`` -> ``[('project.name', 'X')]``."""
    out: List[Tuple[str, Any]] = []
    for k, v in data.items():
        key = '{}{}{}'.format(prefix, sep, k) if prefix else str(k)
        if isinstance(v, Mapping) and v:
            out.extend(flatten(v, key, sep))
        else:
            out.append((key, v))
    return out


def unflatten(pairs: Iterable[Tuple[str, Any]], sep: str = '.') -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in pairs:
        parts = [p for p in str(key).split(sep) if p != '']
        if not parts:
            continue
        cur = out
        for p in parts[:-1]:
            nxt = cur.get(p)
            if not isinstance(nxt, dict):
                nxt = {}
                cur[p] = nxt
            cur = nxt
        cur[parts[-1]] = value
    return out


def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> Dict[str, Any]:
    """Recursive merge; values from ``override`` win. Inputs are not modified."""
    out: Dict[str, Any] = {}
    for k, v in base.items():
        out[k] = deep_merge(v, {}) if isinstance(v, Mapping) else v
    for k, v in override.items():
        if isinstance(v, Mapping) and isinstance(out.get(k), Mapping):
            out[k] = deep_merge(out[k], v)
        elif isinstance(v, Mapping):
            out[k] = deep_merge(v, {})
        else:
            out[k] = v
    return out
