# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'pack_nuke.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFrame,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMainWindow, QPushButton, QSizePolicy, QSpacerItem,
    QSpinBox, QStatusBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QTextEdit, QTreeView, QVBoxLayout,
    QWidget)
import ui_images_rc

class Ui_pack_gui(object):
    def setupUi(self, pack_gui):
        if not pack_gui.objectName():
            pack_gui.setObjectName(u"pack_gui")
        pack_gui.resize(800, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(pack_gui.sizePolicy().hasHeightForWidth())
        pack_gui.setSizePolicy(sizePolicy)
        pack_gui.setMinimumSize(QSize(800, 600))
        pack_gui.setAcceptDrops(True)
        icon = QIcon()
        icon.addFile(u":/images/folder.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        pack_gui.setWindowIcon(icon)
        pack_gui.setAutoFillBackground(False)
        pack_gui.setStyleSheet(u"QLabel\n"
"{\n"
"    font-size: 10pt;\n"
"}\n"
"\n"
"QCheckBox\n"
"{\n"
"    font-size: 10pt;\n"
"}\n"
"\n"
"QRadioButton\n"
"{\n"
"    font-size: 10pt;\n"
"}\n"
"\n"
"\n"
"\n"
"QListView:item:hover\n"
"{\n"
" border-style: none; \n"
" background-color: #4d4d4d;\n"
"}\n"
"\n"
"QGroupBox\n"
"{\n"
"    font-weight: bold;\n"
"    border: 1px solid gray; \n"
"    border-radius: 8px;\n"
"    margin-top: 6px;\n"
"   /* border-top-left-radius: 3px;\n"
"    border-top-right-radius: 3px;*/\n"
"}\n"
"\n"
"QGroupBox::title\n"
"{\n"
"   /* background-color: transparent;*/\n"
"   /* subcontrol-position: top left;*/\n"
"    \n"
"    subcontrol-origin: margin;\n"
"    padding:0px 5px;\n"
"}\n"
"\n"
"\n"
"QToolTip\n"
"{\n"
"     border: 0px solid black;\n"
"     background-color: #ffa02f;\n"
"     padding: 0px;\n"
"     border-radius: 2px;\n"
"     opacity: 100;\n"
"	font-size: 16px;\n"
"}\n"
"\n"
"QWidget\n"
"{\n"
"    color: #b1b1b1;\n"
"    background-color: #323232;\n"
"	font-size: 10pt;\n"
"\n"
"}\n"
"\n"
"QWidget:item:h"
                        "over\n"
"{\n"
"    background-color: gray;\n"
"}\n"
"\n"
"\n"
"QWidget:item:selected\n"
"{\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"}\n"
"\n"
"QMenuBar::item\n"
"{\n"
"    background: transparent;\n"
"}\n"
"\n"
"QMenuBar::item:selected\n"
"{\n"
"    background: transparent;\n"
"    border: 1px solid #ffaa00;\n"
"}\n"
"\n"
"QMenuBar::item:pressed\n"
"{\n"
"    background: #444;\n"
"    border: 1px solid #000;\n"
"    background-color: QLinearGradient(\n"
"        x1:0, y1:0,\n"
"        x2:0, y2:1,\n"
"        stop:1 #212121,\n"
"        stop:0.4 #343434/*,\n"
"        stop:0.2 #343434,\n"
"        stop:0.1 #ffaa00*/\n"
"    );\n"
"    margin-bottom:-1px;\n"
"    padding-bottom:1px;\n"
"}\n"
"\n"
"QMenu\n"
"{\n"
"    border: 1px solid #000;\n"
"}\n"
"\n"
"QMenu::item\n"
"{\n"
"    padding: 2px 20px 2px 20px;\n"
"}\n"
"\n"
"QMenu::item:selected\n"
"{\n"
"    color: #000000;\n"
"}\n"
"\n"
"QWidget:disabled\n"
"{\n"
"    color: #404040;\n"
"    b"
                        "ackground-color: #323232;\n"
"}\n"
"\n"
"QAbstractItemView\n"
"{\n"
"   /* background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4d4d4d, stop: 0.1 #646464, stop: 1 #5d5d5d);*/\n"
"  background-color: #4d4d4d\n"
"}\n"
"\n"
"QTextWidget\n"
"{\n"
"    background-color: #4d4d4d\n"
"}\n"
"\n"
"QWidget:focus\n"
"{\n"
"    /*border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);*/\n"
"}\n"
"\n"
"QLineEdit\n"
"{\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4d4d4d, stop: 0 #646464, stop: 1 #5d5d5d);\n"
"    padding: 1px;\n"
"    border-style: solid;\n"
"    border: 1px solid #1e1e1e;\n"
"    border-radius: 2;\n"
"    padding-left: 16px;\n"
"\n"
"}\n"
"\n"
"QPushButton\n"
"{\n"
"    color: #b1b1b1;\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);\n"
"    border-width: 1px;\n"
"    border-color: #1e1e1e;\n"
"    bo"
                        "rder-style: solid;\n"
"    border-radius: 4;\n"
"    padding: 3px;\n"
"    font-size: 16px;\n"
"    padding-left: 5px;\n"
"    padding-right: 5px;\n"
"	outline: 0;\n"
"}\n"
"\n"
"QPushButton:pressed\n"
"{\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);\n"
"}\n"
"\n"
"QPushButton:checked\n"
"{\n"
"	\n"
"	background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #946223, stop: 0.1 #905f22, stop: 0.5 #885a20, stop: 0.9 #80551e, stop: 1 #7d531e);\n"
"}\n"
"\n"
"QPushButton:focus\n"
"{\n"
"\n"
"}\n"
"\n"
"QComboBox\n"
"{\n"
"    selection-background-color: #ffaa00;\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #565656, stop: 0.1 #525252, stop: 0.5 #4e4e4e, stop: 0.9 #4a4a4a, stop: 1 #464646);\n"
"    border-style: solid;\n"
"    border: 1px solid #1e1e1e;\n"
"    border-radius: 2;\n"
"	padding-left: 16px;\n"
"\n"
"\n"
"}\n"
"\n"
"QComboBox:hover,QPushButton"
                        ":hover\n"
"{\n"
"    border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"}\n"
"\n"
"\n"
"QComboBox:on\n"
"{\n"
"    padding-top: 3px;\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2d2d2d, stop: 0.1 #2b2b2b, stop: 0.5 #292929, stop: 0.9 #282828, stop: 1 #252525);\n"
"    selection-background-color: #ffaa00;\n"
"}\n"
"\n"
"QComboBox QAbstractItemView\n"
"{\n"
"    border: 2px solid darkgray;\n"
"    /*selection-background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);*/\n"
"    selection-background-color: #ffa02f;\n"
"}\n"
"\n"
"QComboBox::drop-down\n"
"{\n"
"     subcontrol-origin: padding;\n"
"     subcontrol-position: top right;\n"
"     width: 15px;\n"
"\n"
"     border-left-width: 0px;\n"
"     border-left-color: darkgray;\n"
"     border-left-style: solid; /* just a single line */\n"
"     border-top-right-radius: 3px; /* same radius as the QComboBox */\n"
"     border-bottom-right-ra"
                        "dius: 3px;\n"
" }\n"
"\n"
"QComboBox::down-arrow\n"
"{\n"
"     image: url(:images/down_arrow.png);\n"
"}\n"
"\n"
"/*\n"
"QComboBox::up-arrow\n"
"{\n"
"     image: url(:images/up_arrow.png);\n"
"}\n"
"*/\n"
"QGroupBox:focus\n"
"{\n"
"  border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"}\n"
"\n"
"QTextEdit:focus\n"
"{\n"
"    border: 2px solid QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"}\n"
"\n"
"QScrollBar:horizontal {\n"
"     border:  solid #222222;\n"
"     background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0.0 #121212, stop: 0.2 #282828, stop: 1 #484848);\n"
"     height: 7px;\n"
"     margin: 0px 16px 0 16px;\n"
"}\n"
"\n"
"QScrollBar::handle:horizontal\n"
"{\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ffa02f, stop: 0.5 #d7801a, stop: 1 #ffa02f);\n"
"      min-height: 20px;\n"
"      border-radius: 2px;\n"
"}\n"
"\n"
"QScrollBar::add-line:horizontal {\n"
"      border: 1"
                        "px solid #1b1b19;\n"
"      border-radius: 2px;\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"      width: 14px;\n"
"      subcontrol-position: right;\n"
"      subcontrol-origin: margin;\n"
"}\n"
"\n"
"QScrollBar::sub-line:horizontal {\n"
"      border: 1px solid #1b1b19;\n"
"      border-radius: 2px;\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"      width: 14px;\n"
"     subcontrol-position: left;\n"
"     subcontrol-origin: margin;\n"
"}\n"
"\n"
"QScrollBar::right-arrow:horizontal, QScrollBar::left-arrow:horizontal\n"
"{\n"
"      border: 1px solid black;\n"
"      width: 1px;\n"
"      height: 1px;\n"
"      background: white;\n"
"}\n"
"\n"
"QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal\n"
"{\n"
"      background: none;\n"
"}\n"
"\n"
"QScrollBar:vertical\n"
"{\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0, stop: 0.0 #121212, stop: 0.2 #282828, stop"
                        ": 1 #484848);\n"
"      width: 7px;\n"
"      margin: 16px 0 16px 0;\n"
"      border: 1px solid #222222;\n"
"}\n"
"\n"
"QScrollBar::handle:vertical\n"
"{\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 0.5 #d7801a, stop: 1 #ffa02f);\n"
"      min-height: 20px;\n"
"      border-radius: 2px;\n"
"}\n"
"\n"
"QScrollBar::add-line:vertical\n"
"{\n"
"      border: 1px solid #1b1b19;\n"
"      border-radius: 2px;\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #ffa02f, stop: 1 #d7801a);\n"
"      height: 14px;\n"
"      subcontrol-position: bottom;\n"
"      subcontrol-origin: margin;\n"
"}\n"
"\n"
"QScrollBar::sub-line:vertical\n"
"{\n"
"      border: 1px solid #1b1b19;\n"
"      border-radius: 2px;\n"
"      background: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d7801a, stop: 1 #ffa02f);\n"
"      height: 14px;\n"
"      subcontrol-position: top;\n"
"      subcontrol-origin: margin;\n"
"}\n"
"\n"
"QScrollBar::up-arrow:vertical, QScrollB"
                        "ar::down-arrow:vertical\n"
"{\n"
"      border: 1px solid black;\n"
"      width: 1px;\n"
"      height: 1px;\n"
"      background: white;\n"
"}\n"
"\n"
"\n"
"QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical\n"
"{\n"
"      background: none;\n"
"}\n"
"\n"
"QTextEdit\n"
"{\n"
"    background-color: #242424;\n"
"}\n"
"\n"
"QPlainTextEdit\n"
"{\n"
"    background-color: #242424;\n"
"}\n"
"\n"
"QHeaderView::section\n"
"{\n"
"    /*           table headers */\n"
"\n"
"    /*background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #616161, stop: 0.5 #505050, stop: 0.6 #434343, stop:1 #656565);*/\n"
"    background-color: #242424;\n"
"    color: white;\n"
"    padding-left: 4px;\n"
"    border: 1px solid #6c6c6c;\n"
"}\n"
"\n"
"QCheckBox:disabled\n"
"{\n"
"color: #414141;\n"
"}\n"
"\n"
"QDockWidget::title\n"
"{\n"
"    text-align: center;\n"
"    spacing: 3px; /* spacing between items in the tool bar */\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #323232, stop: 0.5 #24"
                        "2424, stop:1 #323232);\n"
"}\n"
"\n"
"QDockWidget::close-button, QDockWidget::float-button\n"
"{\n"
"    text-align: center;\n"
"    spacing: 1px; /* spacing between items in the tool bar */\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #323232, stop: 0.5 #242424, stop:1 #323232);\n"
"}\n"
"\n"
"QDockWidget::close-button:hover, QDockWidget::float-button:hover\n"
"{\n"
"    background: #242424;\n"
"}\n"
"\n"
"QDockWidget::close-button:pressed, QDockWidget::float-button:pressed\n"
"{\n"
"    padding: 1px -1px -1px 1px;\n"
"}\n"
"\n"
"QMainWindow::separator\n"
"{\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #161616, stop: 0.5 #151515, stop: 0.6 #212121, stop:1 #343434);\n"
"    color: white;\n"
"    padding-left: 4px;\n"
"    border: 1px solid #4c4c4c;\n"
"    spacing: 3px; /* spacing between items in the tool bar */\n"
"}\n"
"\n"
"QMainWindow::separator:hover\n"
"{\n"
"\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #d7801a, stop:0."
                        "5 #b56c17 stop:1 #ffa02f);\n"
"    color: white;\n"
"    padding-left: 4px;\n"
"    border: 1px solid #6c6c6c;\n"
"    spacing: 3px; /* spacing between items in the tool bar */\n"
"}\n"
"\n"
"QToolBar::handle\n"
"{\n"
"     spacing: 3px; /* spacing between items in the tool bar */\n"
"     background: url(:images/handle.png);\n"
"}\n"
"\n"
"QMenu::separator\n"
"{\n"
"    height: 2px;\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:0 #161616, stop: 0.5 #151515, stop: 0.6 #212121, stop:1 #343434);\n"
"    color: white;\n"
"    padding-left: 4px;\n"
"    margin-left: 10px;\n"
"    margin-right: 5px;\n"
"}\n"
"\n"
"QProgressBar\n"
"{\n"
"    border: 2px solid grey;\n"
"    border-radius: 3px;\n"
"    text-align: center;\n"
"}\n"
"\n"
"QProgressBar::chunk\n"
"{\n"
"    background-color: #d7801a;\n"
"    width: 2.15px;\n"
"    margin: 0.5px;\n"
"}\n"
"\n"
"QTabBar::tab {\n"
"    color: #b1b1b1;\n"
"    border: 1px solid #444;\n"
"    border-bottom-style: none;\n"
"    background-color: #323232"
                        ";\n"
"    padding-left: 10px;\n"
"    padding-right: 10px;\n"
"    padding-top: 3px;\n"
"    padding-bottom: 2px;\n"
"    margin-right: -1px;\n"
"}\n"
"\n"
"QTabWidget::pane {\n"
"    border: 1px solid #444;\n"
"    top: 1px;\n"
"}\n"
"\n"
"QTabBar::tab:last\n"
"{\n"
"    margin-right: 0; /* the last selected tab has nothing to overlap with on the right */\n"
"    border-top-right-radius: 3px;\n"
"}\n"
"\n"
"QTabBar::tab:first:!selected\n"
"{\n"
" margin-left: 0px; /* the last selected tab has nothing to overlap with on the right */\n"
"\n"
"\n"
"    border-top-left-radius: 3px;\n"
"}\n"
"\n"
"QTabBar::tab:!selected\n"
"{\n"
"    color: #b1b1b1;\n"
"    border-bottom-style: solid;\n"
"    margin-top: 3px;\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:1 #212121, stop:.4 #343434);\n"
"}\n"
"\n"
"QTabBar::tab:selected\n"
"{\n"
"    border-top-left-radius: 3px;\n"
"    border-top-right-radius: 3px;\n"
"    margin-bottom: 0px;\n"
"}\n"
"\n"
"QTabBar::tab:!selected:hover\n"
"{\n"
"    /*bord"
                        "er-top: 2px solid #ffaa00;\n"
"    padding-bottom: 3px;*/\n"
"    border-top-left-radius: 3px;\n"
"    border-top-right-radius: 3px;\n"
"    background-color: QLinearGradient(x1:0, y1:0, x2:0, y2:1, stop:1 #212121, stop:0.4 #343434, stop:0.2 #343434, stop:0.1 #ffaa00);\n"
"}\n"
"\n"
"QRadioButton::indicator:checked, QRadioButton::indicator:unchecked{\n"
"    color: #b1b1b1;\n"
"    background-color: #323232;\n"
"    border: 1px solid #b1b1b1;\n"
"    border-radius: 6px;\n"
"}\n"
"\n"
"QRadioButton::indicator:checked\n"
"{\n"
"    background-color: qradialgradient(\n"
"        cx: 0.5, cy: 0.5,\n"
"        fx: 0.5, fy: 0.5,\n"
"        radius: 1.0,\n"
"        stop: 0.25 #ffaa00,\n"
"        stop: 0.3 #323232\n"
"    );\n"
"}\n"
"\n"
"QRadioButton::indicator\n"
"{\n"
"    border-radius: 1px;\n"
"}\n"
"\n"
"QRadioButton::indicator:hover, QCheckBox::indicator:hover\n"
"{\n"
"    border: 1px solid #ffaa00;\n"
"}\n"
"\n"
"QCheckBox::indicator{\n"
"    color: #b1b1b1;\n"
"    background-color: #323232;\n"
"    borde"
                        "r: 1px solid #b1b1b1;\n"
"    width: 9px;\n"
"    height: 9px;\n"
"}\n"
"\n"
"QCheckBox::indicator:checked\n"
"{\n"
"    image:url(:images/checkbox_checked.png);\n"
"    /*color: #ffaa00;*/\n"
"    /*background-color:#ffaa00;*/\n"
"}\n"
"\n"
"QRadioButton::indicator:disabled\n"
"{\n"
"    border: 1px solid #444;\n"
"}\n"
"\n"
"QCheckBox::indicator:disabled\n"
"{\n"
"    border: 1px solid #444;\n"
"    /*image:url(:images/checkbox.png);*/\n"
"}\n"
"\n"
"QCheckBox::indicator:checked:disabled\n"
"{\n"
"    border: 1px solid #444;\n"
"    image:url(:images/checkbox_disabled.png);\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
"QSpinBox\n"
"{\n"
"    selection-background-color: #ffaa00;\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4d4d4d, stop: 0 #646464, stop: 1 #5d5d5d);\n"
"    border: 1px solid #1e1e1e;\n"
"    border-radius:2;\n"
"}\n"
"QAbstractSpinBox\n"
"{\n"
"    selection-background-color: #ffaa00;\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #4d4d4d, sto"
                        "p: 0 #646464, stop: 1 #5d5d5d);\n"
"    border: 1px solid #1e1e1e;\n"
"    border-radius:2;\n"
"}\n"
"\n"
"QSpinBox::up-arrow\n"
"{\n"
"	background-image: url(:images/up_arrow.png);\n"
"    width: 7px; height: 5px;\n"
"}\n"
"QAbstractSpinBox::up-arrow\n"
"{\n"
"	background-image: url(:images/up_arrow.png);\n"
"    width: 7px; height: 5px;\n"
"}\n"
"\n"
"QSpinBox::down-arrow\n"
"{\n"
"	background-image: url(:images/down_arrow.png);\n"
"     width: 7px; height: 5px;\n"
"}\n"
"QAbstractSpinBox::down-arrow\n"
"{\n"
"	background-image: url(:images/down_arrow.png);\n"
"     width: 7px; height: 5px;\n"
"}\n"
"\n"
"QSpinBox::up-button \n"
"{\n"
"    border-width: 0px;\n"
"}\n"
"QAbstractSpinBox::up-button \n"
"{\n"
"    border-width: 0px;\n"
"}\n"
"QSpinBox::down-button \n"
"{\n"
"    border-width: 0px;\n"
"}\n"
"QAbstractSpinBox::down-button \n"
"{\n"
"    border-width: 0px;\n"
"}\n"
"\n"
"QDoubleSpinBox\n"
"{\n"
"    selection-background-color: #ffaa00;\n"
"    background-color: QLinearGradient( x1: 0, y1: 0, x2: 0,"
                        " y2: 1, stop: 0 #4d4d4d, stop: 0 #646464, stop: 1 #5d5d5d);\n"
"    border: 1px solid #1e1e1e;\n"
"    border-radius:2;\n"
"}\n"
"\n"
"QDoubleSpinBox::up-arrow\n"
"{\n"
"	background-image: url(:images/up_arrow.png);\n"
"    width: 7px; height: 5px;\n"
"\n"
"}\n"
"\n"
"QDoubleSpinBox::down-arrow\n"
"{\n"
"	background-image: url(:images/down_arrow.png);\n"
"     width: 7px; height: 5px;\n"
"}\n"
"\n"
"QDoubleSpinBox::up-button \n"
"{\n"
"    border-width: 0px;\n"
"}\n"
"\n"
"QDoubleSpinBox::down-button \n"
"{\n"
"    border-width: 0px;\n"
"}\n"
"\n"
"QCalendarWidget::prevmonth\n"
"{\n"
"	background-image: url(:images/left_arrow.png);\n"
"}\n"
"QCalendarWidget::nextmonth\n"
"{\n"
"	background-image: url(:images/right_arrow.png);\n"
"}\n"
"QCalendarWidget\n"
"{\n"
"	 background-color: #242424;\n"
"    color: white;\n"
"}\n"
"\n"
"")
        pack_gui.setDocumentMode(False)
        pack_gui.setUnifiedTitleAndToolBarOnMac(True)
        self.centralwidget = QWidget(pack_gui)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setMinimumSize(QSize(800, 580))
        self.centralwidget.setMaximumSize(QSize(16000, 16777215))
        self.verticalLayout_60 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_60.setObjectName(u"verticalLayout_60")
        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        self.horizontalLayout_16 = QHBoxLayout(self.tab)
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.verticalLayout_4 = QVBoxLayout()
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_10 = QLabel(self.tab)
        self.label_10.setObjectName(u"label_10")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.label_10.sizePolicy().hasHeightForWidth())
        self.label_10.setSizePolicy(sizePolicy1)
        self.label_10.setMinimumSize(QSize(120, 25))
        self.label_10.setMaximumSize(QSize(120, 25))

        self.horizontalLayout_9.addWidget(self.label_10)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.search_root = QLineEdit(self.tab)
        self.search_root.setObjectName(u"search_root")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.search_root.sizePolicy().hasHeightForWidth())
        self.search_root.setSizePolicy(sizePolicy2)
        self.search_root.setMinimumSize(QSize(250, 25))
        self.search_root.setMaximumSize(QSize(3000, 25))
        self.search_root.setDragEnabled(True)

        self.horizontalLayout.addWidget(self.search_root)

        self.search_root_browse = QPushButton(self.tab)
        self.search_root_browse.setObjectName(u"search_root_browse")
        sizePolicy1.setHeightForWidth(self.search_root_browse.sizePolicy().hasHeightForWidth())
        self.search_root_browse.setSizePolicy(sizePolicy1)
        self.search_root_browse.setMinimumSize(QSize(50, 25))
        self.search_root_browse.setMaximumSize(QSize(50, 25))
        self.search_root_browse.setAutoFillBackground(False)
        self.search_root_browse.setIcon(icon)
        self.search_root_browse.setFlat(True)

        self.horizontalLayout.addWidget(self.search_root_browse)


        self.horizontalLayout_9.addLayout(self.horizontalLayout)


        self.verticalLayout.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.label_12 = QLabel(self.tab)
        self.label_12.setObjectName(u"label_12")
        sizePolicy1.setHeightForWidth(self.label_12.sizePolicy().hasHeightForWidth())
        self.label_12.setSizePolicy(sizePolicy1)
        self.label_12.setMinimumSize(QSize(120, 25))
        self.label_12.setMaximumSize(QSize(120, 25))

        self.horizontalLayout_6.addWidget(self.label_12)

        self.search_for = QLineEdit(self.tab)
        self.search_for.setObjectName(u"search_for")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.search_for.sizePolicy().hasHeightForWidth())
        self.search_for.setSizePolicy(sizePolicy3)
        self.search_for.setMinimumSize(QSize(250, 25))
        self.search_for.setMaximumSize(QSize(3000, 25))
        self.search_for.setDragEnabled(True)

        self.horizontalLayout_6.addWidget(self.search_for)


        self.horizontalLayout_8.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.label_11 = QLabel(self.tab)
        self.label_11.setObjectName(u"label_11")
        sizePolicy1.setHeightForWidth(self.label_11.sizePolicy().hasHeightForWidth())
        self.label_11.setSizePolicy(sizePolicy1)
        self.label_11.setMinimumSize(QSize(120, 25))
        self.label_11.setMaximumSize(QSize(120, 25))

        self.horizontalLayout_7.addWidget(self.label_11)

        self.search_contains = QLineEdit(self.tab)
        self.search_contains.setObjectName(u"search_contains")
        sizePolicy3.setHeightForWidth(self.search_contains.sizePolicy().hasHeightForWidth())
        self.search_contains.setSizePolicy(sizePolicy3)
        self.search_contains.setMinimumSize(QSize(250, 25))
        self.search_contains.setMaximumSize(QSize(3000, 25))
        self.search_contains.setDragEnabled(True)

        self.horizontalLayout_7.addWidget(self.search_contains)


        self.horizontalLayout_8.addLayout(self.horizontalLayout_7)


        self.verticalLayout.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_13 = QLabel(self.tab)
        self.label_13.setObjectName(u"label_13")
        sizePolicy1.setHeightForWidth(self.label_13.sizePolicy().hasHeightForWidth())
        self.label_13.setSizePolicy(sizePolicy1)
        self.label_13.setMinimumSize(QSize(120, 25))
        self.label_13.setMaximumSize(QSize(120, 25))

        self.horizontalLayout_5.addWidget(self.label_13)

        self.search_version_regex = QLineEdit(self.tab)
        self.search_version_regex.setObjectName(u"search_version_regex")
        sizePolicy3.setHeightForWidth(self.search_version_regex.sizePolicy().hasHeightForWidth())
        self.search_version_regex.setSizePolicy(sizePolicy3)
        self.search_version_regex.setMinimumSize(QSize(250, 25))
        self.search_version_regex.setMaximumSize(QSize(16000, 16777215))
        self.search_version_regex.setDragEnabled(True)

        self.horizontalLayout_5.addWidget(self.search_version_regex)


        self.verticalLayout.addLayout(self.horizontalLayout_5)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.versions_get_first = QCheckBox(self.tab)
        self.versions_get_first.setObjectName(u"versions_get_first")
        self.versions_get_first.setMinimumSize(QSize(140, 25))
        self.versions_get_first.setMaximumSize(QSize(140, 25))

        self.horizontalLayout_2.addWidget(self.versions_get_first)

        self.versions_first = QSpinBox(self.tab)
        self.versions_first.setObjectName(u"versions_first")
        self.versions_first.setMinimumSize(QSize(50, 25))
        self.versions_first.setMaximumSize(QSize(50, 25))

        self.horizontalLayout_2.addWidget(self.versions_first)


        self.horizontalLayout_4.addLayout(self.horizontalLayout_2)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_4.addItem(self.horizontalSpacer_2)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.versions_get_last = QCheckBox(self.tab)
        self.versions_get_last.setObjectName(u"versions_get_last")
        self.versions_get_last.setMinimumSize(QSize(140, 25))
        self.versions_get_last.setMaximumSize(QSize(140, 25))
        self.versions_get_last.setChecked(True)

        self.horizontalLayout_3.addWidget(self.versions_get_last)

        self.versions_last = QSpinBox(self.tab)
        self.versions_last.setObjectName(u"versions_last")
        self.versions_last.setMinimumSize(QSize(50, 25))
        self.versions_last.setMaximumSize(QSize(50, 25))

        self.horizontalLayout_3.addWidget(self.versions_last)


        self.horizontalLayout_4.addLayout(self.horizontalLayout_3)


        self.verticalLayout.addLayout(self.horizontalLayout_4)


        self.verticalLayout_4.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.tableWidget = QTableWidget(self.tab)
        self.tableWidget.setObjectName(u"tableWidget")

        self.verticalLayout_2.addWidget(self.tableWidget)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_10.addItem(self.horizontalSpacer)

        self.mark_all = QPushButton(self.tab)
        self.mark_all.setObjectName(u"mark_all")
        sizePolicy1.setHeightForWidth(self.mark_all.sizePolicy().hasHeightForWidth())
        self.mark_all.setSizePolicy(sizePolicy1)
        self.mark_all.setMinimumSize(QSize(100, 25))
        self.mark_all.setMaximumSize(QSize(100, 25))

        self.horizontalLayout_10.addWidget(self.mark_all)

        self.mark_none = QPushButton(self.tab)
        self.mark_none.setObjectName(u"mark_none")
        sizePolicy1.setHeightForWidth(self.mark_none.sizePolicy().hasHeightForWidth())
        self.mark_none.setSizePolicy(sizePolicy1)
        self.mark_none.setMinimumSize(QSize(100, 25))
        self.mark_none.setMaximumSize(QSize(100, 25))

        self.horizontalLayout_10.addWidget(self.mark_none)


        self.verticalLayout_2.addLayout(self.horizontalLayout_10)


        self.verticalLayout_4.addLayout(self.verticalLayout_2)

        self.line = QFrame(self.tab)
        self.line.setObjectName(u"line")
        sizePolicy3.setHeightForWidth(self.line.sizePolicy().hasHeightForWidth())
        self.line.setSizePolicy(sizePolicy3)
        self.line.setMinimumSize(QSize(250, 16))
        self.line.setMaximumSize(QSize(3000, 16))
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_4.addWidget(self.line)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.label_14 = QLabel(self.tab)
        self.label_14.setObjectName(u"label_14")
        sizePolicy1.setHeightForWidth(self.label_14.sizePolicy().hasHeightForWidth())
        self.label_14.setSizePolicy(sizePolicy1)
        self.label_14.setMinimumSize(QSize(120, 25))
        self.label_14.setMaximumSize(QSize(120, 25))

        self.horizontalLayout_11.addWidget(self.label_14)

        self.job_folder = QLineEdit(self.tab)
        self.job_folder.setObjectName(u"job_folder")
        sizePolicy2.setHeightForWidth(self.job_folder.sizePolicy().hasHeightForWidth())
        self.job_folder.setSizePolicy(sizePolicy2)
        self.job_folder.setMinimumSize(QSize(250, 25))
        self.job_folder.setMaximumSize(QSize(3000, 25))
        self.job_folder.setDragEnabled(True)

        self.horizontalLayout_11.addWidget(self.job_folder)

        self.job_folder_browse = QPushButton(self.tab)
        self.job_folder_browse.setObjectName(u"job_folder_browse")
        sizePolicy1.setHeightForWidth(self.job_folder_browse.sizePolicy().hasHeightForWidth())
        self.job_folder_browse.setSizePolicy(sizePolicy1)
        self.job_folder_browse.setMinimumSize(QSize(50, 25))
        self.job_folder_browse.setMaximumSize(QSize(50, 25))
        self.job_folder_browse.setAutoFillBackground(False)
        self.job_folder_browse.setIcon(icon)
        self.job_folder_browse.setFlat(True)

        self.horizontalLayout_11.addWidget(self.job_folder_browse)


        self.verticalLayout_3.addLayout(self.horizontalLayout_11)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_15 = QLabel(self.tab)
        self.label_15.setObjectName(u"label_15")
        sizePolicy1.setHeightForWidth(self.label_15.sizePolicy().hasHeightForWidth())
        self.label_15.setSizePolicy(sizePolicy1)
        self.label_15.setMinimumSize(QSize(120, 25))
        self.label_15.setMaximumSize(QSize(120, 25))

        self.horizontalLayout_13.addWidget(self.label_15)

        self.job_name = QLineEdit(self.tab)
        self.job_name.setObjectName(u"job_name")
        sizePolicy3.setHeightForWidth(self.job_name.sizePolicy().hasHeightForWidth())
        self.job_name.setSizePolicy(sizePolicy3)
        self.job_name.setMinimumSize(QSize(250, 25))
        self.job_name.setMaximumSize(QSize(3000, 25))
        self.job_name.setDragEnabled(True)

        self.horizontalLayout_13.addWidget(self.job_name)


        self.horizontalLayout_12.addLayout(self.horizontalLayout_13)

        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.label_16 = QLabel(self.tab)
        self.label_16.setObjectName(u"label_16")
        sizePolicy1.setHeightForWidth(self.label_16.sizePolicy().hasHeightForWidth())
        self.label_16.setSizePolicy(sizePolicy1)
        self.label_16.setMinimumSize(QSize(120, 25))
        self.label_16.setMaximumSize(QSize(120, 25))

        self.horizontalLayout_14.addWidget(self.label_16)

        self.job_template = QLineEdit(self.tab)
        self.job_template.setObjectName(u"job_template")
        sizePolicy3.setHeightForWidth(self.job_template.sizePolicy().hasHeightForWidth())
        self.job_template.setSizePolicy(sizePolicy3)
        self.job_template.setMinimumSize(QSize(250, 25))
        self.job_template.setMaximumSize(QSize(3000, 25))
        self.job_template.setDragEnabled(True)

        self.horizontalLayout_14.addWidget(self.job_template)


        self.horizontalLayout_12.addLayout(self.horizontalLayout_14)


        self.verticalLayout_3.addLayout(self.horizontalLayout_12)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.label_17 = QLabel(self.tab)
        self.label_17.setObjectName(u"label_17")
        sizePolicy1.setHeightForWidth(self.label_17.sizePolicy().hasHeightForWidth())
        self.label_17.setSizePolicy(sizePolicy1)
        self.label_17.setMinimumSize(QSize(120, 25))
        self.label_17.setMaximumSize(QSize(120, 25))

        self.horizontalLayout_15.addWidget(self.label_17)

        self.place_source = QComboBox(self.tab)
        self.place_source.setObjectName(u"place_source")
        sizePolicy1.setHeightForWidth(self.place_source.sizePolicy().hasHeightForWidth())
        self.place_source.setSizePolicy(sizePolicy1)
        self.place_source.setMinimumSize(QSize(250, 25))
        self.place_source.setMaximumSize(QSize(250, 25))

        self.horizontalLayout_15.addWidget(self.place_source)

        self.label_18 = QLabel(self.tab)
        self.label_18.setObjectName(u"label_18")
        sizePolicy1.setHeightForWidth(self.label_18.sizePolicy().hasHeightForWidth())
        self.label_18.setSizePolicy(sizePolicy1)
        self.label_18.setMinimumSize(QSize(120, 25))
        self.label_18.setMaximumSize(QSize(120, 25))

        self.horizontalLayout_15.addWidget(self.label_18)

        self.place_target = QComboBox(self.tab)
        self.place_target.setObjectName(u"place_target")
        sizePolicy1.setHeightForWidth(self.place_target.sizePolicy().hasHeightForWidth())
        self.place_target.setSizePolicy(sizePolicy1)
        self.place_target.setMinimumSize(QSize(250, 25))
        self.place_target.setMaximumSize(QSize(250, 25))

        self.horizontalLayout_15.addWidget(self.place_target)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_15.addItem(self.horizontalSpacer_3)


        self.verticalLayout_3.addLayout(self.horizontalLayout_15)

        self.deadline = QPushButton(self.tab)
        self.deadline.setObjectName(u"deadline")
        sizePolicy3.setHeightForWidth(self.deadline.sizePolicy().hasHeightForWidth())
        self.deadline.setSizePolicy(sizePolicy3)
        self.deadline.setMinimumSize(QSize(100, 50))
        self.deadline.setMaximumSize(QSize(3000, 50))

        self.verticalLayout_3.addWidget(self.deadline)


        self.verticalLayout_4.addLayout(self.verticalLayout_3)


        self.horizontalLayout_16.addLayout(self.verticalLayout_4)

        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        self.horizontalLayout_23 = QHBoxLayout(self.tab_2)
        self.horizontalLayout_23.setObjectName(u"horizontalLayout_23")
        self.verticalLayout_7 = QVBoxLayout()
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.label_22 = QLabel(self.tab_2)
        self.label_22.setObjectName(u"label_22")
        sizePolicy1.setHeightForWidth(self.label_22.sizePolicy().hasHeightForWidth())
        self.label_22.setSizePolicy(sizePolicy1)
        self.label_22.setMinimumSize(QSize(120, 25))
        self.label_22.setMaximumSize(QSize(120, 25))

        self.horizontalLayout_17.addWidget(self.label_22)

        self.settings_file = QLineEdit(self.tab_2)
        self.settings_file.setObjectName(u"settings_file")
        sizePolicy2.setHeightForWidth(self.settings_file.sizePolicy().hasHeightForWidth())
        self.settings_file.setSizePolicy(sizePolicy2)
        self.settings_file.setMinimumSize(QSize(250, 25))
        self.settings_file.setMaximumSize(QSize(3000, 25))
        self.settings_file.setDragEnabled(True)

        self.horizontalLayout_17.addWidget(self.settings_file)


        self.verticalLayout_7.addLayout(self.horizontalLayout_17)

        self.settings = QTreeView(self.tab_2)
        self.settings.setObjectName(u"settings")

        self.verticalLayout_7.addWidget(self.settings)


        self.horizontalLayout_23.addLayout(self.verticalLayout_7)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.horizontalLayout_18 = QHBoxLayout(self.tab_4)
        self.horizontalLayout_18.setObjectName(u"horizontalLayout_18")
        self.log = QTextEdit(self.tab_4)
        self.log.setObjectName(u"log")

        self.horizontalLayout_18.addWidget(self.log)

        self.tabWidget.addTab(self.tab_4, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.horizontalLayout_22 = QHBoxLayout(self.tab_5)
        self.horizontalLayout_22.setObjectName(u"horizontalLayout_22")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.label_19 = QLabel(self.tab_5)
        self.label_19.setObjectName(u"label_19")
        sizePolicy1.setHeightForWidth(self.label_19.sizePolicy().hasHeightForWidth())
        self.label_19.setSizePolicy(sizePolicy1)
        self.label_19.setMinimumSize(QSize(130, 25))
        self.label_19.setMaximumSize(QSize(130, 25))

        self.horizontalLayout_19.addWidget(self.label_19)

        self.preset_list = QComboBox(self.tab_5)
        self.preset_list.setObjectName(u"preset_list")
        sizePolicy3.setHeightForWidth(self.preset_list.sizePolicy().hasHeightForWidth())
        self.preset_list.setSizePolicy(sizePolicy3)
        self.preset_list.setMinimumSize(QSize(250, 25))
        self.preset_list.setMaximumSize(QSize(3000, 25))

        self.horizontalLayout_19.addWidget(self.preset_list)

        self.preset_load = QPushButton(self.tab_5)
        self.preset_load.setObjectName(u"preset_load")
        sizePolicy1.setHeightForWidth(self.preset_load.sizePolicy().hasHeightForWidth())
        self.preset_load.setSizePolicy(sizePolicy1)
        self.preset_load.setMinimumSize(QSize(150, 25))
        self.preset_load.setMaximumSize(QSize(150, 25))

        self.horizontalLayout_19.addWidget(self.preset_load)


        self.verticalLayout_5.addLayout(self.horizontalLayout_19)

        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.label_20 = QLabel(self.tab_5)
        self.label_20.setObjectName(u"label_20")
        sizePolicy1.setHeightForWidth(self.label_20.sizePolicy().hasHeightForWidth())
        self.label_20.setSizePolicy(sizePolicy1)
        self.label_20.setMinimumSize(QSize(130, 25))
        self.label_20.setMaximumSize(QSize(130, 25))

        self.horizontalLayout_20.addWidget(self.label_20)

        self.preset_name = QLineEdit(self.tab_5)
        self.preset_name.setObjectName(u"preset_name")
        sizePolicy3.setHeightForWidth(self.preset_name.sizePolicy().hasHeightForWidth())
        self.preset_name.setSizePolicy(sizePolicy3)
        self.preset_name.setMinimumSize(QSize(250, 25))
        self.preset_name.setMaximumSize(QSize(16000, 16777215))
        self.preset_name.setDragEnabled(True)

        self.horizontalLayout_20.addWidget(self.preset_name)

        self.preset_get_name = QPushButton(self.tab_5)
        self.preset_get_name.setObjectName(u"preset_get_name")
        sizePolicy1.setHeightForWidth(self.preset_get_name.sizePolicy().hasHeightForWidth())
        self.preset_get_name.setSizePolicy(sizePolicy1)
        self.preset_get_name.setMinimumSize(QSize(50, 25))
        self.preset_get_name.setMaximumSize(QSize(50, 25))
        self.preset_get_name.setAutoFillBackground(False)
        icon1 = QIcon()
        icon1.addFile(u":/images/up_arrow.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.preset_get_name.setIcon(icon1)
        self.preset_get_name.setFlat(True)

        self.horizontalLayout_20.addWidget(self.preset_get_name)

        self.preset_save = QPushButton(self.tab_5)
        self.preset_save.setObjectName(u"preset_save")
        sizePolicy1.setHeightForWidth(self.preset_save.sizePolicy().hasHeightForWidth())
        self.preset_save.setSizePolicy(sizePolicy1)
        self.preset_save.setMinimumSize(QSize(95, 25))
        self.preset_save.setMaximumSize(QSize(95, 25))

        self.horizontalLayout_20.addWidget(self.preset_save)


        self.verticalLayout_5.addLayout(self.horizontalLayout_20)

        self.preset_open_folder = QPushButton(self.tab_5)
        self.preset_open_folder.setObjectName(u"preset_open_folder")
        sizePolicy2.setHeightForWidth(self.preset_open_folder.sizePolicy().hasHeightForWidth())
        self.preset_open_folder.setSizePolicy(sizePolicy2)
        self.preset_open_folder.setMinimumSize(QSize(250, 25))
        self.preset_open_folder.setMaximumSize(QSize(3000, 25))
        self.preset_open_folder.setAutoFillBackground(False)
        icon2 = QIcon()
        icon2.addFile(u":/images/system-search.png", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.preset_open_folder.setIcon(icon2)
        self.preset_open_folder.setFlat(True)

        self.verticalLayout_5.addWidget(self.preset_open_folder)


        self.verticalLayout_6.addLayout(self.verticalLayout_5)

        self.line_2 = QFrame(self.tab_5)
        self.line_2.setObjectName(u"line_2")
        sizePolicy3.setHeightForWidth(self.line_2.sizePolicy().hasHeightForWidth())
        self.line_2.setSizePolicy(sizePolicy3)
        self.line_2.setMinimumSize(QSize(250, 16))
        self.line_2.setMaximumSize(QSize(3000, 16))
        self.line_2.setFrameShape(QFrame.Shape.HLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_6.addWidget(self.line_2)

        self.horizontalLayout_21 = QHBoxLayout()
        self.horizontalLayout_21.setObjectName(u"horizontalLayout_21")
        self.label_21 = QLabel(self.tab_5)
        self.label_21.setObjectName(u"label_21")
        sizePolicy1.setHeightForWidth(self.label_21.sizePolicy().hasHeightForWidth())
        self.label_21.setSizePolicy(sizePolicy1)
        self.label_21.setMinimumSize(QSize(130, 25))
        self.label_21.setMaximumSize(QSize(130, 25))

        self.horizontalLayout_21.addWidget(self.label_21)

        self.place_source_default = QLineEdit(self.tab_5)
        self.place_source_default.setObjectName(u"place_source_default")
        sizePolicy3.setHeightForWidth(self.place_source_default.sizePolicy().hasHeightForWidth())
        self.place_source_default.setSizePolicy(sizePolicy3)
        self.place_source_default.setMinimumSize(QSize(130, 25))
        self.place_source_default.setMaximumSize(QSize(3000, 25))
        self.place_source_default.setDragEnabled(True)

        self.horizontalLayout_21.addWidget(self.place_source_default)


        self.verticalLayout_6.addLayout(self.horizontalLayout_21)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_6.addItem(self.verticalSpacer)


        self.horizontalLayout_22.addLayout(self.verticalLayout_6)

        self.tabWidget.addTab(self.tab_5, "")

        self.verticalLayout_60.addWidget(self.tabWidget)

        pack_gui.setCentralWidget(self.centralwidget)
        self.statusBar = QStatusBar(pack_gui)
        self.statusBar.setObjectName(u"statusBar")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.statusBar.sizePolicy().hasHeightForWidth())
        self.statusBar.setSizePolicy(sizePolicy4)
        pack_gui.setStatusBar(self.statusBar)

        self.retranslateUi(pack_gui)

        self.tabWidget.setCurrentIndex(0)
        self.search_root_browse.setDefault(True)
        self.job_folder_browse.setDefault(True)
        self.preset_get_name.setDefault(True)
        self.preset_open_folder.setDefault(True)


        QMetaObject.connectSlotsByName(pack_gui)
    # setupUi

    def retranslateUi(self, pack_gui):
        pack_gui.setWindowTitle(QCoreApplication.translate("pack_gui", u"Pack Nuke", None))
#if QT_CONFIG(tooltip)
        pack_gui.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.label_10.setText(QCoreApplication.translate("pack_gui", u"Search Root:", None))
#if QT_CONFIG(tooltip)
        self.search_root.setToolTip(QCoreApplication.translate("pack_gui", u"<html><head/><body><p>Expects path to folder containing media files.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.search_root.setText("")
#if QT_CONFIG(tooltip)
        self.search_root_browse.setToolTip(QCoreApplication.translate("pack_gui", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:11px; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Browse for video file.</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.search_root_browse.setText("")
        self.label_12.setText(QCoreApplication.translate("pack_gui", u"Search for:", None))
#if QT_CONFIG(tooltip)
        self.search_for.setToolTip(QCoreApplication.translate("pack_gui", u"<html><head/><body><p>Expects path to folder containing media files.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.search_for.setText(QCoreApplication.translate("pack_gui", u"*comp_*.nk", None))
        self.label_11.setText(QCoreApplication.translate("pack_gui", u"Only if Contains:", None))
#if QT_CONFIG(tooltip)
        self.search_contains.setToolTip(QCoreApplication.translate("pack_gui", u"<html><head/><body><p>Expects path to folder containing media files.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.search_contains.setText(QCoreApplication.translate("pack_gui", u"/work/comp/", None))
        self.label_13.setText(QCoreApplication.translate("pack_gui", u"Version Regex:", None))
#if QT_CONFIG(tooltip)
        self.search_version_regex.setToolTip(QCoreApplication.translate("pack_gui", u"<html><head/><body><p>Expects path to folder containing media files.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.search_version_regex.setText(QCoreApplication.translate("pack_gui", u".*_v(\\d{3}).nk", None))
        self.versions_get_first.setText(QCoreApplication.translate("pack_gui", u"Get First Versions:", None))
        self.versions_get_last.setText(QCoreApplication.translate("pack_gui", u"Get Last Versions:", None))
        self.mark_all.setText(QCoreApplication.translate("pack_gui", u"Mark All", None))
        self.mark_none.setText(QCoreApplication.translate("pack_gui", u"Mark None", None))
        self.label_14.setText(QCoreApplication.translate("pack_gui", u"Job Folder:", None))
#if QT_CONFIG(tooltip)
        self.job_folder.setToolTip(QCoreApplication.translate("pack_gui", u"<html><head/><body><p>Expects path to folder containing media files.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.job_folder.setText("")
#if QT_CONFIG(tooltip)
        self.job_folder_browse.setToolTip(QCoreApplication.translate("pack_gui", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:11px; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Browse for video file.</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.job_folder_browse.setText("")
        self.label_15.setText(QCoreApplication.translate("pack_gui", u"Job Name", None))
#if QT_CONFIG(tooltip)
        self.job_name.setToolTip(QCoreApplication.translate("pack_gui", u"<html><head/><body><p>Expects path to folder containing media files.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.job_name.setText("")
        self.label_16.setText(QCoreApplication.translate("pack_gui", u"Job Template", None))
#if QT_CONFIG(tooltip)
        self.job_template.setToolTip(QCoreApplication.translate("pack_gui", u"<html><head/><body><p>Expects path to folder containing media files.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.job_template.setText("")
        self.label_17.setText(QCoreApplication.translate("pack_gui", u"Source Place:", None))
        self.label_18.setText(QCoreApplication.translate("pack_gui", u"Target Place", None))
        self.deadline.setText(QCoreApplication.translate("pack_gui", u"Send to Deadline", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("pack_gui", u"Get Nuke Scripts", None))
        self.label_22.setText(QCoreApplication.translate("pack_gui", u"Settings File:", None))
#if QT_CONFIG(tooltip)
        self.settings_file.setToolTip(QCoreApplication.translate("pack_gui", u"<html><head/><body><p>Expects path to folder containing media files.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.settings_file.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("pack_gui", u"Settings", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("pack_gui", u"Log", None))
        self.label_19.setText(QCoreApplication.translate("pack_gui", u"Pick Preset:", None))
        self.preset_load.setText(QCoreApplication.translate("pack_gui", u"Load Preset", None))
        self.label_20.setText(QCoreApplication.translate("pack_gui", u"Preset Name:", None))
#if QT_CONFIG(tooltip)
        self.preset_name.setToolTip(QCoreApplication.translate("pack_gui", u"<html><head/><body><p>Expects path to folder containing media files.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.preset_name.setText("")
#if QT_CONFIG(tooltip)
        self.preset_get_name.setToolTip(QCoreApplication.translate("pack_gui", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:11px; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Browse for video file.</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.preset_get_name.setText("")
        self.preset_save.setText(QCoreApplication.translate("pack_gui", u"Save Preset", None))
#if QT_CONFIG(tooltip)
        self.preset_open_folder.setToolTip(QCoreApplication.translate("pack_gui", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:11px; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:8pt;\">Browse for video file.</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.preset_open_folder.setText(QCoreApplication.translate("pack_gui", u"OpenPreset Folder", None))
        self.label_21.setText(QCoreApplication.translate("pack_gui", u"Default Source Place:", None))
#if QT_CONFIG(tooltip)
        self.place_source_default.setToolTip(QCoreApplication.translate("pack_gui", u"<html><head/><body><p>Expects path to folder containing media files.</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.place_source_default.setText("")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("pack_gui", u"Presets", None))
    # retranslateUi

