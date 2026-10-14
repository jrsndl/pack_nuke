"""Small reusable widgets and helpers."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any, Callable, Iterable, List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from . import help as help_texts


# ------------------------------------------------------------------ layout helpers

def hbox(*items, margins=0, spacing=6) -> QtWidgets.QHBoxLayout:
    lay = QtWidgets.QHBoxLayout()
    lay.setContentsMargins(margins, margins, margins, margins)
    lay.setSpacing(spacing)
    for it in items:
        if it is None:
            lay.addStretch(1)
        elif isinstance(it, int):
            lay.addSpacing(it)
        elif isinstance(it, QtWidgets.QLayout):
            lay.addLayout(it)
        else:
            lay.addWidget(it)
    return lay


def vbox(*items, margins=0, spacing=6) -> QtWidgets.QVBoxLayout:
    lay = QtWidgets.QVBoxLayout()
    lay.setContentsMargins(margins, margins, margins, margins)
    lay.setSpacing(spacing)
    for it in items:
        if it is None:
            lay.addStretch(1)
        elif isinstance(it, QtWidgets.QLayout):
            lay.addLayout(it)
        else:
            lay.addWidget(it)
    return lay


def button(text: str, slot: Optional[Callable] = None, tip: str = '', icon: str = '',
           object_name: str = '') -> QtWidgets.QPushButton:
    b = QtWidgets.QPushButton(text)
    if icon:
        b.setIcon(QtGui.QIcon(icon))
    tip = tip or help_texts.tip(text)
    if tip:
        b.setToolTip(tip)
    if object_name:
        b.setObjectName(object_name)
    if slot is not None:
        b.clicked.connect(lambda _checked=False: slot())
    return b


def label(text: str, object_name: str = '', tip: str = '') -> QtWidgets.QLabel:
    lbl = QtWidgets.QLabel(text)
    if object_name:
        lbl.setObjectName(object_name)
    tip = tip or help_texts.tip(text)
    if tip:
        lbl.setToolTip(tip)
    return lbl


def hint(text: str) -> QtWidgets.QLabel:
    lbl = label(text, 'hint')
    lbl.setWordWrap(True)
    f = lbl.font()
    f.setPointSizeF(max(6.0, f.pointSizeF() - 1))   # smaller hint text, set in code, not in the style sheet
    lbl.setFont(f)
    lbl.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
    return lbl


def set_status_label(lbl: QtWidgets.QLabel, ok: bool, text: str) -> None:
    lbl.setObjectName('ok' if ok else 'bad')
    lbl.setText(text)
    lbl.style().unpolish(lbl)
    lbl.style().polish(lbl)


def bold_group_titles(root: QtWidgets.QWidget) -> None:
    """Bold group box titles, set in code (a font-weight in the style sheet makes Qt mis-measure the
    title). The bold font is not inherited by the group contents: direct children get the normal font."""
    for box in root.findChildren(QtWidgets.QGroupBox):
        normal = QtGui.QFont(box.font())
        normal.setBold(False)
        bold = QtGui.QFont(normal)
        bold.setBold(True)
        box.setFont(bold)
        for child in box.findChildren(QtWidgets.QWidget, options=QtCore.Qt.FindDirectChildrenOnly):
            if not isinstance(child, QtWidgets.QGroupBox):
                child.setFont(normal)


class Debouncer(QtCore.QObject):
    """Call ``fn`` once, ``ms`` after the last ``trigger()``."""

    def __init__(self, fn: Callable[[], None], ms: int = 200, parent=None):
        super().__init__(parent)
        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(ms)
        self._timer.timeout.connect(fn)

    def trigger(self, *_args) -> None:
        self._timer.start()


class PathEdit(QtWidgets.QWidget):
    """Line edit + browse button. ``mode``: 'dir', 'open' or 'save'."""
    changed = QtCore.Signal(str)

    def __init__(self, mode: str = 'dir', file_filter: str = 'All files (*)', placeholder: str = '',
                 parent=None):
        super().__init__(parent)
        self.mode = mode
        self.file_filter = file_filter
        self.edit = QtWidgets.QLineEdit()
        self.edit.setPlaceholderText(placeholder)
        self.btn = QtWidgets.QPushButton()
        self.btn.setIcon(QtGui.QIcon(':/images/folder.png'))
        self.btn.setToolTip('Browse...')
        self.btn.setFixedWidth(34)
        self.btn.clicked.connect(self.browse)
        self.edit.textChanged.connect(self.changed.emit)
        self.setLayout(hbox(self.edit, self.btn))

    def text(self) -> str:
        return self.edit.text().strip().replace('\\', '/')

    def setText(self, text: str) -> None:
        self.edit.setText(text or '')

    def browse(self) -> None:
        start = self.text()
        if self.mode == 'dir':
            p = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select folder', start)
        elif self.mode == 'save':
            p, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save as', start, self.file_filter)
        else:
            p, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Select file', start, self.file_filter)
        if p:
            self.setText(p.replace('\\', '/'))


# ------------------------------------------------------------------ OS helpers

def reveal(path: str) -> None:
    """Show a file in Explorer/Finder, or open a folder."""
    if not path or not os.path.exists(path):
        return
    native = os.path.normpath(path)
    try:
        if sys.platform.startswith('win'):
            if os.path.isdir(native):
                subprocess.Popen(['explorer', native])
            else:
                subprocess.Popen(['explorer', '/select,', native])
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', '-R', native])
        else:
            subprocess.Popen(['xdg-open', native if os.path.isdir(native) else os.path.dirname(native)])
    except OSError:
        pass


def open_path(path: str) -> None:
    if path and os.path.exists(path):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))


def ask(parent, title: str, text: str,
        buttons=QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        default=QtWidgets.QMessageBox.No):
    return QtWidgets.QMessageBox.question(parent, title, text, buttons, default)


# ------------------------------------------------------------------ clipboard (JSON payloads)

CLIP_KEY = 'packnuke'


def clip_put(kind: str, payload: Any) -> None:
    QtWidgets.QApplication.clipboard().setText(json.dumps({CLIP_KEY: kind, 'data': payload}, indent=1))


def clip_get(kind: str) -> Any:
    try:
        data = json.loads(QtWidgets.QApplication.clipboard().text())
    except (ValueError, TypeError):
        return None
    if isinstance(data, dict) and data.get(CLIP_KEY) == kind:
        return data.get('data')
    return None


def clip_text() -> str:
    return QtWidgets.QApplication.clipboard().text()


# ------------------------------------------------------------------ table helpers

def selected_rows(view: QtWidgets.QAbstractItemView) -> List[int]:
    """Selected source-model rows of a view (works through a proxy model)."""
    sel = view.selectionModel()
    if sel is None:
        return []
    model = view.model()
    rows = set()
    for idx in sel.selectedRows() or sel.selectedIndexes():
        if isinstance(model, QtCore.QSortFilterProxyModel):
            idx = model.mapToSource(idx)
        rows.add(idx.row())
    return sorted(rows)


def first_selected_row(view: QtWidgets.QAbstractItemView) -> Optional[int]:
    """First selected row in *view order* (source row)."""
    sel = view.selectionModel()
    if sel is None:
        return None
    idxs = sel.selectedRows() or sel.selectedIndexes()
    if not idxs:
        return None
    idx = sorted(idxs, key=lambda i: i.row())[0]
    model = view.model()
    if isinstance(model, QtCore.QSortFilterProxyModel):
        idx = model.mapToSource(idx)
    return idx.row()


def configure_table(view: QtWidgets.QTableView, stretch_col: Optional[int] = None) -> None:
    view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
    view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
    view.setAlternatingRowColors(True)
    view.setSortingEnabled(True)
    view.verticalHeader().setVisible(False)
    view.verticalHeader().setDefaultSectionSize(22)
    view.horizontalHeader().setHighlightSections(False)
    view.horizontalHeader().setSectionsMovable(True)
    view.setWordWrap(False)
    view.setTextElideMode(QtCore.Qt.ElideMiddle)
    if stretch_col is not None:
        view.horizontalHeader().setSectionResizeMode(stretch_col, QtWidgets.QHeaderView.Stretch)


class KeyValueTable(QtWidgets.QTableWidget):
    """Read-only two column table (token inspector)."""

    def __init__(self, headers=('Token', 'Value'), parent=None):
        super().__init__(0, 2, parent)
        self.setHorizontalHeaderLabels(list(headers))
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(22)
        self.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setAlternatingRowColors(True)
        self.setWordWrap(False)
        copy_sc = QtGui.QShortcut(QtGui.QKeySequence.Copy, self)
        copy_sc.setContext(QtCore.Qt.WidgetShortcut)
        copy_sc.activated.connect(self.copy_selection)

    def set_pairs(self, pairs: Iterable, highlight: Iterable[str] = ()) -> None:
        hl = set(highlight)
        pairs = list(pairs)
        self.setRowCount(len(pairs))
        for r, (k, v) in enumerate(pairs):
            ki = QtWidgets.QTableWidgetItem(str(k))
            vi = QtWidgets.QTableWidgetItem('' if v is None else str(v))
            vi.setToolTip(vi.text())
            if k in hl:
                f = ki.font()
                f.setBold(True)
                ki.setFont(f)
            self.setItem(r, 0, ki)
            self.setItem(r, 1, vi)

    def copy_selection(self) -> None:
        rows = sorted({i.row() for i in self.selectedIndexes()})
        lines = ['{}\t{}'.format(self.item(r, 0).text(), self.item(r, 1).text()) for r in rows]
        QtWidgets.QApplication.clipboard().setText('\n'.join(lines))


# ------------------------------------------------------------------ JSON tree (type preserving)

class _Node:
    def __init__(self, key: Any, value: Any, parent: Optional['_Node'] = None):
        self.key = key
        self.parent = parent
        self.children: List['_Node'] = []
        self.kind = type(value)
        self.value = None
        if isinstance(value, dict):
            for k, v in value.items():
                self.children.append(_Node(k, v, self))
        elif isinstance(value, list):
            for i, v in enumerate(value):
                self.children.append(_Node(i, v, self))
        else:
            self.value = value

    def row(self) -> int:
        return self.parent.children.index(self) if self.parent else 0

    def to_python(self) -> Any:
        if self.kind is dict:
            return {c.key: c.to_python() for c in self.children}
        if self.kind is list:
            return [c.to_python() for c in self.children]
        return self.value


def parse_typed(text: str, kind: type, old: Any) -> Any:
    """Convert edited text back to the original JSON type. Raises ValueError."""
    t = text.strip()
    if kind is bool:
        if t.lower() in ('1', 'true', 'yes', 'on'):
            return True
        if t.lower() in ('0', 'false', 'no', 'off'):
            return False
        raise ValueError('expected true/false')
    if kind is int:
        return int(t)
    if kind is float:
        return float(t)
    if kind is type(None):
        if t in ('', 'null'):
            return None
        try:
            return json.loads(t)
        except ValueError:
            return text
    return text


class JsonTreeModel(QtCore.QAbstractItemModel):
    """Editable JSON tree; edits keep the original value type (true stays a bool)."""
    edited = QtCore.Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root = _Node('root', {})

    def load(self, data: Any) -> None:
        self.beginResetModel()
        self._root = _Node('root', data)
        self.endResetModel()

    def to_python(self) -> Any:
        return self._root.to_python()

    def _node(self, index: QtCore.QModelIndex) -> _Node:
        return index.internalPointer() if index.isValid() else self._root

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()
        node = self._node(parent)
        if row < len(node.children):
            return self.createIndex(row, column, node.children[row])
        return QtCore.QModelIndex()

    def parent(self, index=QtCore.QModelIndex()):
        if not index.isValid():
            return QtCore.QModelIndex()
        node = index.internalPointer()
        p = node.parent
        if p is None or p is self._root:
            return QtCore.QModelIndex()
        return self.createIndex(p.row(), 0, p)

    def rowCount(self, parent=QtCore.QModelIndex()):
        if parent.column() > 0:
            return 0
        return len(self._node(parent).children)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 3

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return ('Key', 'Value', 'Type')[section]
        return None

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        node = index.internalPointer()
        col = index.column()
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            if col == 0:
                return str(node.key)
            if col == 1:
                if node.kind in (dict, list):
                    return '' if role == QtCore.Qt.EditRole else '{} items'.format(len(node.children))
                if node.kind is bool:
                    return 'true' if node.value else 'false'
                return '' if node.value is None else str(node.value)
            if col == 2:
                return {dict: 'object', list: 'array', bool: 'bool', int: 'int', float: 'float',
                        str: 'string', type(None): 'null'}.get(node.kind, node.kind.__name__)
        if role == QtCore.Qt.ForegroundRole and col == 2:
            return QtGui.QColor('#8a8a8a')
        if role == QtCore.Qt.ToolTipRole and col == 1 and node.kind not in (dict, list):
            return str(node.value)
        return None

    def flags(self, index):
        f = super().flags(index)
        if index.isValid() and index.column() == 1 and index.internalPointer().kind not in (dict, list):
            f |= QtCore.Qt.ItemIsEditable
        return f

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role != QtCore.Qt.EditRole or index.column() != 1:
            return False
        node = index.internalPointer()
        try:
            node.value = parse_typed(str(value), node.kind, node.value)
            if node.kind is type(None):
                node.kind = type(node.value)
        except ValueError as e:
            QtWidgets.QMessageBox.warning(None, 'Invalid value', 'Expected {}: {}'.format(node.kind.__name__, e))
            return False
        self.dataChanged.emit(index, index)
        self.edited.emit()
        return True
