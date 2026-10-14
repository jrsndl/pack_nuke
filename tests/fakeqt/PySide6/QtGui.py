from .QtCore import QObject, Signal, _Anything


class QIcon:
    def __init__(self, *a):
        pass


class QColor:
    def __init__(self, *a):
        self.args = a


class QFont(_Anything):
    def setBold(self, b):
        self.bold = b


class QKeySequence:
    Copy, Paste, Delete = 'copy', 'paste', 'delete'

    def __init__(self, *a):
        self.a = a


class QShortcut(QObject):
    activated = Signal()

    def __init__(self, seq=None, parent=None, **kw):
        super().__init__(parent, **kw)
        self.seq = seq

    def setContext(self, c):
        pass


class QFontDatabase:
    FixedFont = 1

    @staticmethod
    def systemFont(x):
        return QFont()


class QDesktopServices:
    opened = []

    @staticmethod
    def openUrl(u):
        QDesktopServices.opened.append(u)
