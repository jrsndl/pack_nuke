from .QtCore import QObject, QModelIndex, Qt, QtEnum, Signal, _Anything


class QWidget(QObject):
    def __init__(self, *a, **kw):
        parent = a[0] if a and isinstance(a[0], QObject) else kw.pop('parent', None)
        super().__init__(parent)
        self._fq_visible = True
        self._fq_enabled = True
        self._fq_tooltip = ''

    def setVisible(self, v):
        self._fq_visible = v

    def isVisible(self):
        return self._fq_visible

    def setEnabled(self, v):
        self._fq_enabled = v

    def isEnabled(self):
        return self._fq_enabled

    def setToolTip(self, t):
        self._fq_tooltip = t

    def toolTip(self):
        return self._fq_tooltip

    def setLayout(self, lay):
        self._fq_layout = lay

    def showEvent(self, e):
        pass

    def style(self):
        return _Anything()

    def fontMetrics(self):
        class _FM:
            def height(self):
                return 14
        return _FM()


class QMainWindow(QWidget):
    def setCentralWidget(self, w):
        self._fq_central = w

    def statusBar(self):
        if not hasattr(self, '_fq_sb'):
            self._fq_sb = _Anything()
        return self._fq_sb

    def saveGeometry(self):
        return b'geo'

    def restoreGeometry(self, g):
        return True


class _Layout(QObject):
    def __init__(self, *a):
        super().__init__()
        self.items = []

    def addWidget(self, w, *a):
        self.items.append(w)

    def addLayout(self, l, *a):
        self.items.append(l)

    def addStretch(self, *a):
        pass

    def addSpacing(self, *a):
        pass

    def addRow(self, *a):
        self.items.append(a)


QLayout = _Layout
QHBoxLayout = QVBoxLayout = QGridLayout = QFormLayout = _Layout


class QLabel(QWidget):
    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self._text = text

    def setText(self, t):
        self._text = t

    def text(self):
        return self._text


class QPushButton(QWidget):
    clicked = Signal(bool)
    toggled = Signal(bool)

    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self._text = text
        self._checked = False
        self._checkable = False

    def setCheckable(self, b):
        self._checkable = b

    def setChecked(self, b):
        if b != self._checked:
            self._checked = b
            self.toggled.emit(b)

    def isChecked(self):
        return self._checked

    def click(self):
        self.clicked.emit(False)

    def setMenu(self, m):
        self._menu = m


class QCheckBox(QPushButton):
    pass


class QLineEdit(QWidget):
    textChanged = Signal(str)
    textEdited = Signal(str)
    returnPressed = Signal()
    editingFinished = Signal()

    def __init__(self, text='', parent=None):
        super().__init__(parent)
        self._text = text

    def setText(self, t):
        t = t or ''
        if t != self._text:
            self._text = t
            self.textChanged.emit(t)

    def text(self):
        return self._text

    def displayText(self):
        return self._text

    def user_types(self, t):  # test helper
        self.setText(t)
        self.textEdited.emit(t)


class QPlainTextEdit(QWidget):
    NoWrap = 0

    def __init__(self, *a):
        super().__init__()
        self._lines = []

    def appendHtml(self, h):
        self._lines.append(h)

    def setPlainText(self, t):
        self._lines = [t]

    def toPlainText(self):
        return '\n'.join(self._lines)

    def clear(self):
        self._lines = []

    def verticalScrollBar(self):
        return _Anything()


class QSpinBox(QWidget):
    valueChanged = Signal(int)

    def __init__(self, *a):
        super().__init__()
        self._v, self._min, self._max = 0, 0, 99

    def setRange(self, a, b):
        self._min, self._max = a, b
        self._v = min(max(self._v, a), b)

    def setValue(self, v):
        v = min(max(int(v), self._min), self._max)
        if v != self._v:
            self._v = v
            self.valueChanged.emit(v)

    def value(self):
        return self._v


class QComboBox(QWidget):
    currentTextChanged = Signal(str)
    currentIndexChanged = Signal(int)

    def __init__(self, *a):
        super().__init__()
        self._items = []
        self._idx = -1
        self._edit_text = None

    def addItem(self, text, data=None):
        self._items.append((text, data))
        if self._idx < 0:
            self._set(0)

    def addItems(self, texts):
        for t in texts:
            self.addItem(t)

    def clear(self):
        self._items = []
        self._set(-1)

    def count(self):
        return len(self._items)

    def itemText(self, i):
        return self._items[i][0]

    def _set(self, i):
        if i != self._idx:
            self._idx = i
            self.currentIndexChanged.emit(i)
            self.currentTextChanged.emit(self.currentText())

    def setCurrentIndex(self, i):
        self._set(i)

    def currentIndex(self):
        return self._idx

    def currentText(self):
        if self._edit_text is not None:
            return self._edit_text
        return self._items[self._idx][0] if 0 <= self._idx < len(self._items) else ''

    def setCurrentText(self, t):
        for i, (txt, _d) in enumerate(self._items):
            if txt == t:
                self._edit_text = None
                self._set(i)
                return
        if getattr(self, '_editable', False):
            self._edit_text = t
            self.currentTextChanged.emit(t)

    def currentData(self):
        return self._items[self._idx][1] if 0 <= self._idx < len(self._items) else None

    def setEditable(self, b):
        self._editable = b


class QMenu(QWidget):
    aboutToShow = Signal()

    def addAction(self, text, fn=None):
        return _Anything()

    def addSeparator(self):
        pass

    def exec(self, *a):
        pass

    def clear(self):
        pass


# ------------------------------------------------------------------ item views

class _SelModel(QObject):
    selectionChanged = Signal()

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.rows = []

    def selectedRows(self, col=0):
        m = self.view.model()
        return [QModelIndex(r, 0, m) for r in self.rows]

    def selectedIndexes(self):
        return self.selectedRows()

    def select_rows(self, rows):  # test helper
        self.rows = list(rows)
        self.selectionChanged.emit()


class QAbstractItemView(QWidget):
    SelectRows = 1
    ExtendedSelection = 2
    NoEditTriggers = 0
    doubleClicked = Signal(object)
    customContextMenuRequested = Signal(object)

    def __init__(self, *a):
        super().__init__()
        self._model = None
        self._sel = _SelModel(self)

    def setModel(self, m):
        self._model = m

    def model(self):
        return self._model

    def selectionModel(self):
        return self._sel


class QTableView(QAbstractItemView):
    pass


class QTreeView(QAbstractItemView):
    pass


class QHeaderView:
    Stretch, Interactive, ResizeToContents = 1, 2, 3


class QTableWidgetItem:
    def __init__(self, text=''):
        self._text = str(text)
        self._table = None
        self._check = None
        self._flags = QtEnum(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)

    def text(self):
        return self._text

    def setText(self, t):
        self._text = str(t)
        if self._table is not None:
            self._table.itemChanged.emit(self)

    def setCheckState(self, s):
        self._check = s
        if self._table is not None:
            self._table.itemChanged.emit(self)

    def checkState(self):
        return self._check

    def setFlags(self, f):
        self._flags = f

    def flags(self):
        return self._flags

    def setToolTip(self, t):
        self._tip = t

    def setForeground(self, c):
        self._fg = c

    def font(self):
        from .QtGui import QFont
        return QFont()

    def setFont(self, f):
        pass


class QTableWidget(QAbstractItemView):
    itemChanged = Signal(object)

    def __init__(self, rows=0, cols=0, parent=None):
        super().__init__()
        self._cols = cols
        self._rows = [[None] * cols for _ in range(rows)]
        self._widgets = {}
        self._cur = -1

    def setHorizontalHeaderLabels(self, labels):
        self._labels = labels

    def rowCount(self):
        return len(self._rows)

    def setRowCount(self, n):
        self._rows = self._rows[:n] + [[None] * self._cols for _ in range(n - len(self._rows))]
        self._widgets = {k: v for k, v in self._widgets.items() if k[0] < n}

    def insertRow(self, r):
        self._rows.insert(r, [None] * self._cols)

    def removeRow(self, r):
        del self._rows[r]
        self._widgets = {(rr - (1 if rr > r else 0), c): w for (rr, c), w in self._widgets.items() if rr != r}

    def setItem(self, r, c, item):
        item._table = self
        self._rows[r][c] = item

    def item(self, r, c):
        return self._rows[r][c]

    def setCellWidget(self, r, c, w):
        self._widgets[(r, c)] = w

    def cellWidget(self, r, c):
        return self._widgets.get((r, c))

    def selectedIndexes(self):
        return [QModelIndex(r, 0, self) for r in self._sel.rows]

    def currentRow(self):
        return self._cur

    def setCurrentCell(self, r, c):
        self._cur = r

    def editItem(self, it):
        pass

    def setColumnWidth(self, *a):
        pass


class QListWidgetItem:
    def __init__(self, text=''):
        self._text = text

    def text(self):
        return self._text

    def setForeground(self, c):
        pass


class QListWidget(QWidget):
    currentTextChanged = Signal(str)
    itemDoubleClicked = Signal(object)

    def __init__(self, *a):
        super().__init__()
        self._items = []
        self._cur = -1

    def addItems(self, texts):
        for t in texts:
            self._items.append(QListWidgetItem(t))

    def addItem(self, it):
        self._items.append(it if isinstance(it, QListWidgetItem) else QListWidgetItem(it))

    def clear(self):
        self._items = []
        self._cur = -1
        self.currentTextChanged.emit('')

    def count(self):
        return len(self._items)

    def item(self, i):
        return self._items[i]

    def currentItem(self):
        return self._items[self._cur] if 0 <= self._cur < len(self._items) else None

    def setCurrentRow(self, i):
        if i != self._cur:
            self._cur = i
            self.currentTextChanged.emit(self._items[i].text() if 0 <= i < len(self._items) else '')

    def setCurrentItem(self, it):
        self.setCurrentRow(self._items.index(it))

    def findItems(self, text, flags):
        return [i for i in self._items if i.text() == text]


class QTreeWidgetItem:
    def __init__(self, parent=None, texts=()):
        self.texts = list(texts)
        self.children = []
        if parent is not None:
            parent._add(self)

    def _add(self, child):
        self.children.append(child)

    def setToolTip(self, c, t):
        pass

    def setForeground(self, c, col):
        self.colored = True

    def font(self, c):
        from .QtGui import QFont
        return QFont()

    def setFont(self, c, f):
        pass

    def setExpanded(self, b):
        pass


class QTreeWidget(QAbstractItemView):
    def __init__(self, *a):
        super().__init__()
        self.top = []

    def _add(self, item):
        self.top.append(item)

    def clear(self):
        self.top = []


class QTabWidget(QWidget):
    currentChanged = Signal(int)

    def __init__(self, *a):
        super().__init__()
        self._tabs = []
        self._cur = 0

    def addTab(self, w, title):
        self._tabs.append([w, title])

    def setTabToolTip(self, i, t):
        self._tabs[i].append(t)

    def count(self):
        return len(self._tabs)

    def setTabText(self, i, t):
        self._tabs[i][1] = t

    def tabText(self, i):
        return self._tabs[i][1]

    def setCurrentIndex(self, i):
        if 0 <= i < len(self._tabs) and i != self._cur:
            self._cur = i
            self.currentChanged.emit(i)

    def currentIndex(self):
        return self._cur

    def setCurrentWidget(self, w):
        for i, (tw, _t) in enumerate(self._tabs):
            if tw is w:
                self.setCurrentIndex(i)


class QSplitter(QWidget):
    splitterMoved = Signal(int, int)

    def addWidget(self, w):
        pass

    def sizes(self):
        return [3, 1]


class QGroupBox(QWidget):
    pass


class QScrollArea(QWidget):
    pass


class QProgressBar(QWidget):
    pass


class _Clipboard:
    def __init__(self):
        self._t = ''

    def text(self):
        return self._t

    def setText(self, t):
        self._t = t


class QApplication(QObject):
    _clip = _Clipboard()
    _inst = None

    def __init__(self, *a):
        super().__init__()
        QApplication._inst = self

    @staticmethod
    def clipboard():
        return QApplication._clip

    @staticmethod
    def instance():
        return QApplication._inst

    def exec(self):
        return 0


class QMessageBox:
    Yes, No, Save, Discard, Cancel = 1, 2, 4, 8, 16
    answer = 1
    warnings = []

    @staticmethod
    def question(*a, **k):
        return QMessageBox.answer

    @staticmethod
    def warning(parent, title, text, *a):
        QMessageBox.warnings.append(text)


class QFileDialog:
    @staticmethod
    def getExistingDirectory(*a):
        return ''

    @staticmethod
    def getOpenFileName(*a):
        return '', ''

    @staticmethod
    def getSaveFileName(*a):
        return '', ''


class QInputDialog:
    answer = ('new_place', True)

    @staticmethod
    def getText(*a, **k):
        return QInputDialog.answer


class QSizePolicy:
    Ignored, Fixed, Preferred, Expanding, Minimum = 0, 1, 2, 3, 4
