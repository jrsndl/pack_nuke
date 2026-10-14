"""File sequence handling: one implementation for printf (``%04d``), hash (``####``) and
stereo view (``%V`` / ``%v``) notation.

Files on disk are matched with an exact regular expression built from the pattern
(digits only, padding respected) instead of a glob, so ``plate.####.exr`` never picks up
``plate.v2.0001.exr`` or ``plate.0001_old.exr``.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from . import paths

# frame token: %d, %4d, %04d, or a run of hashes
FRAME_TOKEN_RE = re.compile(r'%0?(\d*)d|#+')
VIEW_TOKEN_RE = re.compile(r'%[vV]')


@dataclass(frozen=True)
class FramePattern:
    prefix: str
    token: str
    suffix: str
    padding: int  # 0 = unpadded (%d)

    @property
    def regex(self) -> 're.Pattern[str]':
        if self.padding > 0:
            digits = r'(?:\d{%d}|[1-9]\d{%d,})' % (self.padding, self.padding)
        else:
            digits = r'\d+'
        return re.compile('^' + re.escape(self.prefix) + r'(?P<frame>-?' + digits + ')'
                          + re.escape(self.suffix) + '$', re.IGNORECASE if os.name == 'nt' else 0)

    def printf(self) -> str:
        pad = '%0{}d'.format(self.padding) if self.padding > 0 else '%d'
        return self.prefix + pad + self.suffix

    def frame_name(self, frame: int) -> str:
        if self.padding > 0:
            num = ('-' if frame < 0 else '') + str(abs(frame)).zfill(self.padding)
        else:
            num = str(frame)
        return self.prefix + num + self.suffix


def parse_frame_pattern(file_name: str) -> Optional[FramePattern]:
    """Find the (last) frame token in a file name. Returns None for single files."""
    matches = list(FRAME_TOKEN_RE.finditer(file_name))
    if not matches:
        return None
    m = matches[-1]
    token = m.group(0)
    if token.startswith('#'):
        padding = len(token)
    else:
        padding = int(m.group(1)) if m.group(1) else 0
    return FramePattern(file_name[:m.start()], token, file_name[m.end():], padding)


def has_views(path: str) -> bool:
    return bool(VIEW_TOKEN_RE.search(path))


def expand_views(path: str, views: Iterable[str]) -> List[Tuple[Optional[str], str]]:
    """Expand ``%V`` (full view name) and ``%v`` (first letter) for every view.

    Returns ``[(view, path), ...]``; ``[(None, path)]`` when the path has no view token.
    """
    if not has_views(path):
        return [(None, path)]
    out = []
    seen = set()
    for view in views or []:
        p = path.replace('%V', view).replace('%v', view[:1].lower())
        if p not in seen:
            seen.add(p)
            out.append((view, p))
    return out


def list_sequence(pattern_path: str) -> List[Tuple[int, str, int]]:
    """Existing frames of a sequence pattern path as ``(frame, path, size)``, sorted by frame.

    One ``scandir`` per folder; on Windows sizes come with the listing (no extra stat).
    """
    pattern_path = paths.norm(pattern_path)
    folder, name = os.path.split(pattern_path)
    fp = parse_frame_pattern(name)
    if fp is None:
        return []
    rx = fp.regex
    found = []
    try:
        with os.scandir(folder) as it:
            for entry in it:
                m = rx.match(entry.name)
                if m and entry.is_file():
                    try:
                        size = entry.stat().st_size
                    except OSError:
                        size = 0
                    found.append((int(m.group('frame')), folder + '/' + entry.name, size))
    except OSError:
        return []
    found.sort()
    return found


@dataclass
class ResolvedFiles:
    files: List[str]
    sizes: List[int]
    frames: List[int]
    is_sequence: bool
    views: List[str]

    @property
    def total_size(self) -> int:
        return sum(self.sizes)


def resolve_files(pattern_path: str, views: Iterable[str] = ()) -> ResolvedFiles:
    """Every existing file a (possibly sequence / stereo) path refers to, in stable order."""
    pattern_path = paths.norm(pattern_path)
    fp = parse_frame_pattern(paths.basename(pattern_path))
    files: List[str] = []
    sizes: List[int] = []
    frames: List[int] = []
    used_views: List[str] = []
    seen = set()
    for view, p in expand_views(pattern_path, views):
        if fp is not None:
            for frame, f, size in list_sequence(p):
                if f not in seen:
                    seen.add(f)
                    files.append(f)
                    sizes.append(size)
                    frames.append(frame)
        elif p not in seen and os.path.isfile(p):
            seen.add(p)
            files.append(p)
            try:
                sizes.append(os.path.getsize(p))
            except OSError:
                sizes.append(0)
        if view is not None:
            used_views.append(view)
    return ResolvedFiles(files, sizes, sorted(set(frames)), fp is not None, used_views)


def clean_name(file_name: str) -> str:
    """File name without the frame token: ``plate.%04d.exr`` -> ``plate.exr``."""
    fp = parse_frame_pattern(file_name)
    if fp is None:
        return file_name
    return fp.prefix.rstrip('._-') + fp.suffix


def frame_ranges(frames: Iterable[int]) -> str:
    """Compact frame list: ``1001-1050,1052-1100``."""
    fr = sorted(set(frames))
    if not fr:
        return ''
    out = []
    start = prev = fr[0]
    for f in fr[1:]:
        if f == prev + 1:
            prev = f
            continue
        out.append(str(start) if start == prev else '{}-{}'.format(start, prev))
        start = prev = f
    out.append(str(start) if start == prev else '{}-{}'.format(start, prev))
    return ','.join(out)


def group_by_folder(files: Iterable[str]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for f in files:
        d, n = os.path.split(f)
        out.setdefault(d, []).append(n)
    return out
