"""Filtering of found Nuke scripts: name pattern, path substring, version regex, first/last N.

Filtering is done per folder (versions of one script live in one folder) and works on an
in-memory list, so changing any filter is instant and never rescans the disk.
"""
from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Tuple


@dataclass
class ScriptEntry:
    path: str          # full path, forward slashes
    folder: str
    name: str
    size: int = 0
    mtime: float = 0.0
    version: str = ''  # filled by filtering

    @property
    def key(self) -> str:
        return self.path.lower()


@dataclass
class VersionFilter:
    name_patterns: str = '*.nk'   # fnmatch patterns separated by ';'
    contains: str = ''            # substrings separated by ';' (any must match), case-insensitive
    version_regex: str = ''       # group 1 = version
    first_enabled: bool = False
    first_n: int = 1
    last_enabled: bool = True
    last_n: int = 1
    _rx: Optional['re.Pattern[str]'] = field(default=None, repr=False, compare=False)
    error: str = field(default='', compare=False)

    def compile(self) -> bool:
        self.error = ''
        self._rx = None
        if self.version_regex:
            try:
                self._rx = re.compile(self.version_regex)
            except re.error as e:
                self.error = 'Version regex: {}'.format(e)
                return False
        return True

    def _patterns(self) -> List[str]:
        pats = [p.strip().lower() for p in re.split(r'[;,]', self.name_patterns or '') if p.strip()]
        return pats or ['*.nk']

    def _contains(self) -> List[str]:
        return [c.strip().replace('\\', '/').lower() for c in (self.contains or '').split(';') if c.strip()]

    def entry_passes(self, entry: ScriptEntry) -> Optional[str]:
        """Name/contains/version checks for one entry. Returns the version string or None."""
        name = entry.name.lower()
        if not any(fnmatch.fnmatchcase(name, p) for p in self._patterns()):
            return None
        subs = self._contains()
        if subs:
            low = entry.path.lower()
            if not any(s in low for s in subs):
                return None
        if self._rx is not None:
            m = self._rx.search(entry.name)
            if not m:
                return None
            return m.group(1) if self._rx.groups >= 1 and m.group(1) is not None else m.group(0)
        return ''

    def filter_folder(self, entries: Iterable[ScriptEntry]) -> List[ScriptEntry]:
        """Apply all checks plus first/last N to the entries of one folder."""
        passed: List[Tuple[ScriptEntry, str]] = []
        for e in entries:
            v = self.entry_passes(e)
            if v is not None:
                passed.append((e, v))
        passed.sort(key=lambda ev: (version_key(ev[1]), ev[0].name.lower()))
        if self.first_enabled or self.last_enabled:
            keep = set()
            n = len(passed)
            if self.first_enabled:
                keep.update(range(min(max(self.first_n, 0), n)))
            if self.last_enabled:
                keep.update(range(n - min(max(self.last_n, 0), n), n))
            passed = [ev for i, ev in enumerate(passed) if i in keep]
        out = []
        for e, v in passed:
            e.version = v
            out.append(e)
        return out


def version_key(version: str):
    """Numeric-aware sort key: v9 < v10."""
    return [(0, int(t), '') if t.isdigit() else (1, 0, t.lower()) for t in re.findall(r'\d+|\D+', version or '')]
