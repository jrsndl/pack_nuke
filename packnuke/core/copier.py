"""Copy engine: exact file lists, parallel, safe for several farm jobs writing the same
shared folder at once, and every failure is reported.

* No shell, no robocopy/rsync parsing - one code path on every OS.
* Files are written to a temporary name and atomically renamed, so a half-copied file is
  never mistaken for a complete one, and two jobs copying the same font/OCIO file at the
  same time can't corrupt it.
* ``skip_identical``: an existing target with the same size and mtime is left alone
  (``copy2`` preserves mtime), which makes re-running a job cheap.
* Optional hashing is computed while copying, so each source byte is read once.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

CHUNK = 8 * 1024 * 1024
MTIME_TOLERANCE = 2.0  # FAT/SMB timestamps can be rounded to 2 s


def file_hash(path: str) -> str:
    h = hashlib.blake2b()
    with open(path, 'rb') as f:
        while True:
            block = f.read(CHUNK)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def combined_hash(hashes: Iterable[Optional[str]]) -> str:
    hs = [h for h in hashes if h]
    if not hs:
        return ''
    return hashlib.blake2b(''.join(hs).encode('ascii')).hexdigest()


@dataclass
class CopyTask:
    src: str
    dst: str
    size: int = 0


@dataclass
class CopyResult:
    task: CopyTask
    status: str               # 'copied' | 'skipped' | 'error'
    error: str = ''
    hash: Optional[str] = None
    seconds: float = 0.0


def identical(src: str, dst: str) -> bool:
    try:
        s, d = os.stat(src), os.stat(dst)
    except OSError:
        return False
    return s.st_size == d.st_size and abs(s.st_mtime - d.st_mtime) <= MTIME_TOLERANCE


def _copy_with_hash(src: str, dst: str) -> str:
    h = hashlib.blake2b()
    with open(src, 'rb') as fi, open(dst, 'wb') as fo:
        while True:
            block = fi.read(CHUNK)
            if not block:
                break
            h.update(block)
            fo.write(block)
    shutil.copystat(src, dst)
    return h.hexdigest()


def copy_one(task: CopyTask, skip_identical: bool = True, want_hash: bool = False,
             retries: int = 2) -> CopyResult:
    t0 = time.time()
    src, dst = task.src, task.dst
    try:
        if not os.path.isfile(src):
            return CopyResult(task, 'error', error='source file not found', seconds=time.time() - t0)
        if os.path.normcase(os.path.abspath(src)) == os.path.normcase(os.path.abspath(dst)):
            return CopyResult(task, 'skipped', hash=file_hash(src) if want_hash else None,
                              seconds=time.time() - t0)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if skip_identical and identical(src, dst):
            return CopyResult(task, 'skipped', hash=file_hash(src) if want_hash else None,
                              seconds=time.time() - t0)
    except OSError as e:
        return CopyResult(task, 'error', error=str(e), seconds=time.time() - t0)

    last_error = ''
    for attempt in range(retries + 1):
        tmp = '{}.pnpart.{}.{}'.format(dst, os.getpid(), threading.get_ident())
        try:
            digest = None
            if want_hash:
                digest = _copy_with_hash(src, tmp)
            else:
                shutil.copy2(src, tmp)
            try:
                os.replace(tmp, dst)
            except OSError:
                # another job may hold / have just written the same file
                if identical(src, dst):
                    _remove(tmp)
                    return CopyResult(task, 'skipped', hash=digest, seconds=time.time() - t0)
                raise
            return CopyResult(task, 'copied', hash=digest, seconds=time.time() - t0)
        except OSError as e:
            last_error = '{}: {}'.format(type(e).__name__, e)
            _remove(tmp)
            if attempt < retries:
                time.sleep(1.0 + attempt)
    return CopyResult(task, 'error', error=last_error, seconds=time.time() - t0)


def _remove(path: str) -> None:
    try:
        os.remove(path)
    except OSError:
        pass


def run_copies(tasks: List[CopyTask], threads: int = 8, skip_identical: bool = True,
               want_hash: bool = False,
               on_result: Optional[Callable[[CopyResult, int, int], None]] = None) -> List[CopyResult]:
    """Copy all tasks; results are returned in task order."""
    results: List[Optional[CopyResult]] = [None] * len(tasks)
    if not tasks:
        return []
    done = 0
    with ThreadPoolExecutor(max_workers=max(1, int(threads)), thread_name_prefix='pncopy') as pool:
        futures = {pool.submit(copy_one, t, skip_identical, want_hash): i for i, t in enumerate(tasks)}
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                res = fut.result()
            except Exception as e:  # never lose a result
                res = CopyResult(tasks[i], 'error', error='{}: {}'.format(type(e).__name__, e))
            results[i] = res
            done += 1
            if on_result:
                on_result(res, done, len(tasks))
    return [r for r in results if r is not None]


def human_size(size: float) -> str:
    size = float(size or 0)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024 or unit == 'TB':
            return '{:.0f} {}'.format(size, unit) if unit == 'B' else '{:.2f} {}'.format(size, unit)
        size /= 1024.0
    return '{:.2f} TB'.format(size)
