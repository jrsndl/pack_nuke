"""Table models for the Get Nuke Scripts and Queue tabs (fast with thousands of rows)."""
from __future__ import annotations

import datetime
from typing import Callable, List, Optional, Set

from PySide6 import QtCore

from ..core.copier import human_size
from ..core.versions import ScriptEntry, version_key

SORT_ROLE = QtCore.Qt.UserRole + 1


class _MarkableModel(QtCore.QAbstractTableModel):
    """Common base: column 0 is a 'marked' checkbox."""
    marks_changed = QtCore.Signal()
    headers: List[str] = []

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else len(self.headers)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headers[section]
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.ToolTipRole and section == 0:
            return 'Marked (space toggles the selected rows)'
        return None

    def flags(self, index):
        f = QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.column() == 0:
            f |= QtCore.Qt.ItemIsUserCheckable
        return f

    # subclasses implement
    def is_marked(self, row: int) -> bool:
        raise NotImplementedError

    def _set_mark(self, row: int, value: bool) -> None:
        raise NotImplementedError

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.CheckStateRole and index.column() == 0:
            checked = value == QtCore.Qt.Checked or value == QtCore.Qt.Checked.value or value is True or value == 2
            self._set_mark(index.row(), bool(checked))
            self.dataChanged.emit(index, index, [QtCore.Qt.CheckStateRole])
            self.marks_changed.emit()
            return True
        return False

    def set_marks(self, rows: Optional[List[int]], value: Optional[bool]) -> None:
        """Mark/unmark rows (None = all rows). ``value=None`` toggles."""
        rows = range(self.rowCount()) if rows is None else rows
        for r in rows:
            self._set_mark(r, (not self.is_marked(r)) if value is None else value)
        if self.rowCount():
            self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, 0),
                                  [QtCore.Qt.CheckStateRole])
        self.marks_changed.emit()

    def check_data(self, row: int):
        return QtCore.Qt.Checked if self.is_marked(row) else QtCore.Qt.Unchecked


def _fmt_time(ts: float) -> str:
    if not ts:
        return ''
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')


class ScriptTableModel(_MarkableModel):
    """Found scripts after filtering. Marks are kept per path, so they survive filter changes."""
    headers = ['', 'Name', 'Version', 'Folder', 'Modified', 'Size']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.entries: List[ScriptEntry] = []
        self.unmarked: Set[str] = set()   # keys explicitly unmarked (new rows default to marked)
        self.default_marked = True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else len(self.entries)

    def is_marked(self, row: int) -> bool:
        return self.entries[row].key not in self.unmarked

    def _set_mark(self, row: int, value: bool) -> None:
        key = self.entries[row].key
        if value:
            self.unmarked.discard(key)
        else:
            self.unmarked.add(key)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        e = self.entries[index.row()]
        col = index.column()
        if role == QtCore.Qt.CheckStateRole and col == 0:
            return self.check_data(index.row())
        if role == QtCore.Qt.DisplayRole:
            return ('', e.name, e.version, e.folder, _fmt_time(e.mtime), human_size(e.size) if e.size else '')[col]
        if role == SORT_ROLE:
            return (0 if self.is_marked(index.row()) else 1, e.name.lower(), version_key(e.version),
                    e.folder.lower(), e.mtime, e.size)[col]
        if role == QtCore.Qt.ToolTipRole:
            return e.path
        return None

    def set_entries(self, entries: List[ScriptEntry]) -> None:
        self.beginResetModel()
        self.entries = list(entries)
        self.endResetModel()
        self.marks_changed.emit()

    def append(self, entries: List[ScriptEntry]) -> None:
        if not entries:
            return
        start = len(self.entries)
        self.beginInsertRows(QtCore.QModelIndex(), start, start + len(entries) - 1)
        self.entries.extend(entries)
        self.endInsertRows()
        self.marks_changed.emit()

    def clear(self) -> None:
        self.set_entries([])

    def marked_entries(self) -> List[ScriptEntry]:
        return [e for e in self.entries if e.key not in self.unmarked]


class QueueModel(_MarkableModel):
    headers = ['', 'Name', 'Version', 'Folder', 'Tokens']

    def __init__(self, state, tags_fn: Callable[[str], str], parent=None):
        super().__init__(parent)
        self.state = state
        self.tags_fn = tags_fn
        self._tags_cache = {}

    @property
    def queue(self):
        return self.state.queue

    def rowCount(self, parent=QtCore.QModelIndex()):
        return 0 if parent.isValid() else len(self.queue)

    def is_marked(self, row: int) -> bool:
        return self.queue[row].marked

    def _set_mark(self, row: int, value: bool) -> None:
        self.queue[row].marked = value

    def tags_text(self, path: str) -> str:
        if path not in self._tags_cache:
            self._tags_cache[path] = self.tags_fn(path)
        return self._tags_cache[path]

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        q = self.queue[index.row()]
        col = index.column()
        if role == QtCore.Qt.CheckStateRole and col == 0:
            return self.check_data(index.row())
        if role == QtCore.Qt.DisplayRole:
            if col == 4:
                return self.tags_text(q.path)
            return ('', q.name, q.version, q.folder)[col]
        if role == SORT_ROLE:
            if col == 4:
                return self.tags_text(q.path).lower()
            return (0 if q.marked else 1, q.name.lower(), version_key(q.version), q.folder.lower())[col]
        if role == QtCore.Qt.ToolTipRole:
            return q.path if col != 4 else self.tags_text(q.path)
        return None

    def refresh(self) -> None:
        self.beginResetModel()
        self._tags_cache = {}
        self.endResetModel()
        self.marks_changed.emit()

    def refresh_tokens(self) -> None:
        self._tags_cache = {}
        if self.rowCount():
            self.dataChanged.emit(self.index(0, 4), self.index(self.rowCount() - 1, 4))

    def remove_rows(self, rows: List[int]) -> None:
        for r in sorted(set(rows), reverse=True):
            if 0 <= r < len(self.queue):
                self.beginRemoveRows(QtCore.QModelIndex(), r, r)
                del self.queue[r]
                self.endRemoveRows()
        self.marks_changed.emit()


class SortProxy(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSortRole(SORT_ROLE)
        self.setDynamicSortFilter(False)

    def lessThan(self, left, right):
        a, b = left.data(SORT_ROLE), right.data(SORT_ROLE)
        try:
            return a < b
        except TypeError:
            return str(a) < str(b)
