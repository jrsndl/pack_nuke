"""Path helpers. All paths inside Pack Nuke use forward slashes."""
from __future__ import annotations

import posixpath
import re
from typing import Optional

_ABS_RE = re.compile(r'^(?:[A-Za-z]:)?/')


def norm(path: Optional[str]) -> str:
    """Forward slashes, collapsed duplicate slashes (UNC prefix kept), no trailing slash."""
    if not path:
        return ''
    p = str(path).replace('\\', '/')
    unc = p.startswith('//')
    p = re.sub(r'/{2,}', '/', p)
    if unc:
        p = '/' + p
    if len(p) > 1 and p.endswith('/') and not re.match(r'^[A-Za-z]:/$', p):
        p = p.rstrip('/')
        if not p:
            p = '/'
    return p


def is_absolute(path: str) -> bool:
    """True for ``C:/x``, ``/x`` and ``//server/share`` style paths."""
    return bool(_ABS_RE.match(norm(path)))


def join(*parts: str) -> str:
    """Join path parts with '/', skipping empty parts."""
    clean = [norm(p) for p in parts if p not in (None, '')]
    if not clean:
        return ''
    out = clean[0]
    for p in clean[1:]:
        out = out.rstrip('/') + '/' + p.lstrip('/')
    return out


def dirname(path: str) -> str:
    return posixpath.dirname(norm(path))


def basename(path: str) -> str:
    return posixpath.basename(norm(path))


def _anchor(path: str) -> str:
    """Return the root a path lives on: drive letter, UNC server/share, or '/'."""
    p = norm(path)
    m = re.match(r'^([A-Za-z]:)/', p)
    if m:
        return m.group(1).lower()
    m = re.match(r'^//([^/]+)/([^/]+)', p)
    if m:
        return ('//' + m.group(1) + '/' + m.group(2)).lower()
    return '/'


def relpath(path: str, start: str) -> Optional[str]:
    """Relative path from directory ``start`` to ``path``, component-wise.

    Returns None when the two paths live on different drives/shares and a relative
    path is impossible. Comparison of the anchor is case-insensitive (Windows).
    """
    p, s = norm(path), norm(start)
    if not p or not s:
        return None
    if _anchor(p) != _anchor(s):
        return None
    # strip the anchor and compare the rest component by component
    def parts(x: str):
        x = re.sub(r'^([A-Za-z]:)?/+', '', x)
        return [c for c in x.split('/') if c and c != '.']
    pp, sp = parts(p), parts(s)
    i = 0
    while i < len(pp) and i < len(sp) and pp[i].lower() == sp[i].lower():
        i += 1
    rel = ['..'] * (len(sp) - i) + pp[i:]
    return '/'.join(rel) if rel else '.'


def is_within(path: str, folder: str) -> bool:
    """True when ``path`` is ``folder`` or inside it (component-wise, case-insensitive)."""
    r = relpath(path, folder)
    return r is not None and not r.startswith('..')


def safe_name(text: str) -> str:
    """Make a string safe to use as a single folder/file name."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', str(text)).strip() or '_'
