import inspect


class QtEnum(int):
    @property
    def value(self):
        return int(self)

    def __or__(self, other):
        return QtEnum(int(self) | int(other))

    __ror__ = __or__


class _Ns:
    """Namespace whose unknown attributes are unique enum ints."""
    _known = {}
    _counter = [1000]

    def __init__(self, **known):
        self.__dict__.update({k: QtEnum(v) for k, v in known.items()})

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        self._counter[0] += 1
        v = QtEnum(self._counter[0])
        setattr(self, name, v)
        return v


Qt = _Ns(DisplayRole=0, EditRole=2, ToolTipRole=3, ForegroundRole=9, CheckStateRole=10, UserRole=256,
         Unchecked=0, Checked=2, Horizontal=1, Vertical=2, AscendingOrder=0, ItemIsSelectable=1,
         ItemIsEditable=2, ItemIsUserCheckable=16, ItemIsEnabled=32, Key_Space=32)


def Slot(*_a, **_k):
    return lambda f: f


class BoundSignal:
    def __init__(self, owner):
        self._owner = owner
        self._slots = []

    def connect(self, fn, *_a):
        self._slots.append(fn)
        return True

    def disconnect(self, *_a):
        self._slots = []

    def emit(self, *args):
        if getattr(self._owner, '_signals_blocked', False):
            return
        prev = QObject._current_sender
        QObject._current_sender = self._owner
        try:
            for fn in list(self._slots):
                _call(fn, args)
        finally:
            QObject._current_sender = prev


def _call(fn, args):
    if isinstance(fn, BoundSignal):
        return fn.emit(*args)
    try:
        sig = inspect.signature(fn)
        params = [p for p in sig.parameters.values() if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        has_var = any(p.kind == p.VAR_POSITIONAL for p in sig.parameters.values())
        if not has_var:
            args = args[:len(params)]
    except (TypeError, ValueError):
        pass
    return fn(*args)


class Signal:
    def __init__(self, *types, **kw):
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, owner):
        if obj is None:
            return self
        key = '_sig_' + self.name
        bs = obj.__dict__.get(key)
        if bs is None:
            bs = BoundSignal(obj)
            obj.__dict__[key] = bs
        return bs


class _Anything:
    """Absorbs any call/attribute (layout calls, cosmetics)."""

    def __init__(self, *a, **k):
        pass

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return _Anything()

    def __call__(self, *a, **k):
        return _Anything()

    def __iter__(self):
        return iter(())


class QObject:
    destroyed = Signal()
    _current_sender = None

    def sender(self):
        return QObject._current_sender

    def __init__(self, parent=None, *a, **kw):
        self._signals_blocked = False
        self._parent = parent
        for k, v in kw.items():  # signal connections passed as kwargs
            sig = getattr(self, k, None)
            if isinstance(sig, BoundSignal):
                sig.connect(v)

    def blockSignals(self, b):
        old = getattr(self, '_signals_blocked', False)
        self._signals_blocked = b
        return old

    def setObjectName(self, n):
        self._name = n

    def objectName(self):
        return getattr(self, '_name', '')

    def parent(self):
        return getattr(self, '_parent', None)

    def __getattr__(self, name):
        # absorb Qt-style API (camelCase or a few known lower-case names); typos in our own
        # snake_case attributes still raise
        if not name.startswith('_') and (any(c.isupper() for c in name) or name in KNOWN_LOWER):
            return _Anything()
        raise AttributeError('{} has no attribute {}'.format(type(self).__name__, name))


KNOWN_LOWER = {'show', 'hide', 'update', 'resize', 'close', 'raise_', 'repaint', 'style', 'font', 'palette',
               'layout', 'header', 'viewport', 'move', 'adjustSize', 'activateWindow'}


class QTimer(QObject):
    timeout = Signal()

    def setSingleShot(self, b):
        pass

    def setInterval(self, ms):
        pass

    def start(self, *a):
        self.timeout.emit()  # fire immediately in tests

    def stop(self):
        pass


class QThread(QObject):
    finished = Signal()

    def start(self):
        self._running = True
        try:
            self.run()
        finally:
            self._running = False
        self.finished.emit()

    def isRunning(self):
        return getattr(self, '_running', False)

    def wait(self, *a):
        return True


class QModelIndex:
    def __init__(self, row=-1, col=-1, model=None, ptr=None):
        self._r, self._c, self._m, self._p = row, col, model, ptr

    def isValid(self):
        return self._r >= 0 and self._m is not None

    def row(self):
        return self._r

    def column(self):
        return self._c

    def internalPointer(self):
        return self._p

    def model(self):
        return self._m

    def data(self, role=0):
        return self._m.data(self, role) if self._m else None


QPersistentModelIndex = QModelIndex


class QAbstractItemModel(QObject):
    dataChanged = Signal()
    modelReset = Signal()
    rowsInserted = Signal()
    layoutChanged = Signal()

    def beginResetModel(self):
        pass

    def endResetModel(self):
        self.modelReset.emit()

    def beginInsertRows(self, *a):
        pass

    def endInsertRows(self):
        self.rowsInserted.emit()

    def beginRemoveRows(self, *a):
        pass

    def endRemoveRows(self):
        pass

    def createIndex(self, r, c, ptr=None):
        return QModelIndex(r, c, self, ptr)

    def hasIndex(self, r, c, parent=QModelIndex()):
        return 0 <= r < self.rowCount(parent) and 0 <= c < self.columnCount(parent)

    def index(self, r, c, parent=QModelIndex()):
        return QModelIndex(r, c, self) if self.hasIndex(r, c, parent) else QModelIndex()

    def flags(self, index):
        return QtEnum(Qt.ItemIsEnabled | Qt.ItemIsSelectable)


class QAbstractTableModel(QAbstractItemModel):
    pass


class QSortFilterProxyModel(QAbstractItemModel):
    def setSourceModel(self, m):
        self._src = m

    def sourceModel(self):
        return self._src

    def setSortRole(self, r):
        pass

    def setDynamicSortFilter(self, b):
        pass

    def rowCount(self, parent=QModelIndex()):
        return self._src.rowCount()

    def columnCount(self, parent=QModelIndex()):
        return self._src.columnCount()

    def mapToSource(self, idx):
        return QModelIndex(idx.row(), idx.column(), self._src) if idx.isValid() else QModelIndex()

    def data(self, idx, role=0):
        return self._src.data(self.mapToSource(idx), role)


class QSettings(QObject):
    IniFormat = 1
    _stores = {}

    def __init__(self, path='', fmt=None, parent=None):
        super().__init__(parent)
        self._d = QSettings._stores.setdefault(path, {})

    def setFallbacksEnabled(self, b):
        pass

    def value(self, k, default=None):
        return self._d.get(k, default)

    def setValue(self, k, v):
        self._d[k] = v if isinstance(v, (bytes, QByteArray)) else (str(v) if not isinstance(v, str) else v)

    def contains(self, k):
        return k in self._d

    def sync(self):
        pass


class QByteArray(bytes):
    pass


class QUrl:
    @staticmethod
    def fromLocalFile(p):
        return p


class QProcess(QObject):
    NotRunning = 0
    MergedChannels = 1
    readyReadStandardOutput = Signal()
    finished = Signal()

    def state(self):
        return 0

    def start(self, *a):
        self.started_with = a


QCoreApplication = QObject


class _QBA(bytes):
    def data(self):
        return bytes(self)
