# This Python file uses the following encoding: utf-8

from functools import partial
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any, List, Dict, Union

from PySide6 import QtWidgets, QtCore, QtGui
from ui_pack_nuke import *
from ui_images_rc import *

import pprint

class TreeItem:
    """A Json item corresponding to a line in QTreeView"""

    def __init__(self, parent: "TreeItem" = None):
        self._parent = parent
        self._key = ""
        self._value = ""
        self._value_type = None
        self._children = []

    def appendChild(self, item: "TreeItem"):
        """Add item as a child"""
        self._children.append(item)

    def child(self, row: int) -> "TreeItem":
        """Return the child of the current item from the given row"""
        return self._children[row]

    def parent(self) -> "TreeItem":
        """Return the parent of the current item"""
        return self._parent

    def childCount(self) -> int:
        """Return the number of children of the current item"""
        return len(self._children)

    def row(self) -> int:
        """Return the row where the current item occupies in the parent"""
        return self._parent._children.index(self) if self._parent else 0

    @property
    def key(self) -> str:
        """Return the key name"""
        return self._key

    @key.setter
    def key(self, key: str):
        """Set key name of the current item"""
        self._key = key

    @property
    def value(self) -> str:
        """Return the value name of the current item"""
        return self._value

    @value.setter
    def value(self, value: str):
        """Set value name of the current item"""
        self._value = value

    @property
    def value_type(self):
        """Return the python type of the item's value."""
        return self._value_type

    @value_type.setter
    def value_type(self, value):
        """Set the python type of the item's value."""
        self._value_type = value

    @classmethod
    def load(
        cls, value: Union[List, Dict], parent: "TreeItem" = None, sort=True
    ) -> "TreeItem":
        """Create a 'root' TreeItem from a nested list or a nested dictonary

        Examples:
            with open("file.json") as file:
                data = json.dump(file)
                root = TreeItem.load(data)

        This method is a recursive function that calls itself.

        Returns:
            TreeItem: TreeItem
        """
        rootItem = TreeItem(parent)
        rootItem.key = "root"

        if isinstance(value, dict):
            items = sorted(value.items()) if sort else value.items()

            for key, value in items:
                child = cls.load(value, rootItem)
                child.key = key
                child.value_type = type(value)
                rootItem.appendChild(child)

        elif isinstance(value, list):
            for index, value in enumerate(value):
                child = cls.load(value, rootItem)
                child.key = index
                child.value_type = type(value)
                rootItem.appendChild(child)

        else:
            rootItem.value = value
            rootItem.value_type = type(value)

        return rootItem


class JsonModel(QtCore.QAbstractItemModel):
    """ An editable model of Json data """

    def __init__(self, parent: QObject = None):
        super().__init__(parent)

        self._rootItem = TreeItem()
        self._headers = ("key", "value")

    def clear(self):
        """ Clear data from the model """
        self.load({})

    def load(self, document: dict):
        """Load model from a nested dictionary returned by json.loads()

        Arguments:
            document (dict): JSON-compatible dictionary
        """

        assert isinstance(
            document, (dict, list, tuple)
        ), "`document` must be of dict, list or tuple, " f"not {type(document)}"

        self.beginResetModel()

        self._rootItem = TreeItem.load(document)
        self._rootItem.value_type = type(document)

        self.endResetModel()

        return True

    def data(self, index: QtCore.QModelIndex, role: QtCore.Qt.ItemDataRole) -> Any:
        """Override from QAbstractItemModel

        Return data from a json item according index and role

        """
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == QtCore.Qt.DisplayRole:
            if index.column() == 0:
                return item.key

            if index.column() == 1:
                return item.value

        elif role == QtCore.Qt.EditRole:
            if index.column() == 1:
                return item.value

    def setData(self, index: QtCore.QModelIndex, value: Any, role: QtCore.Qt.ItemDataRole):
        """Override from QAbstractItemModel

        Set json item according index and role

        Args:
            index (QModelIndex)
            value (Any)
            role (Qt.ItemDataRole)

        """
        if role == QtCore.Qt.EditRole:
            if index.column() == 1:
                item = index.internalPointer()
                item.value = str(value)

                self.dataChanged.emit(index, index, [QtCore.Qt.EditRole])

                return True

        return False

    def headerData(
        self, section: int, orientation: QtCore.Qt.Orientation, role: QtCore.Qt.ItemDataRole
    ):
        """Override from QAbstractItemModel

        For the JsonModel, it returns only data for columns (orientation = Horizontal)

        """
        if role != QtCore.Qt.DisplayRole:
            return None

        if orientation == QtCore.Qt.Horizontal:
            return self._headers[section]

    def index(self, row: int, column: int, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        """Override from QAbstractItemModel

        Return index according row, column and parent

        """
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index: QtCore.QModelIndex) -> QtCore.QModelIndex:
        """Override from QAbstractItemModel

        Return parent index of index

        """

        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self._rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent=QtCore.QModelIndex()):
        """Override from QAbstractItemModel

        Return row count from parent index
        """
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self._rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def columnCount(self, parent=QtCore.QModelIndex()):
        """Override from QAbstractItemModel

        Return column number. For the model, it always return 2 columns
        """
        return 2

    def flags(self, index: QtCore.QModelIndex) -> QtCore.Qt.ItemFlags:
        """Override from QAbstractItemModel

        Return flags of index
        """
        flags = super(JsonModel, self).flags(index)

        if index.column() == 1:
            return QtCore.Qt.ItemIsEditable | flags
        else:
            return flags

    def to_json(self, item=None):

        if item is None:
            item = self._rootItem

        nchild = item.childCount()

        if item.value_type is dict:
            document = {}
            for i in range(nchild):
                ch = item.child(i)
                document[ch.key] = self.to_json(ch)
            return document

        elif item.value_type == list:
            document = []
            for i in range(nchild):
                ch = item.child(i)
                document.append(self.to_json(ch))
            return document

        else:
            return item.value

class MainWindow(QtWidgets.QMainWindow, Ui_pack_gui):

    def __init__(self, parent = None):
        super().__init__()

        self.ui = Ui_pack_gui()
        self.ui.setupUi(self)
        ui_images_rc.qInitResources()
        self.resize(1400, 300)

        # data structs
        self.found_versions = None
        self.filtered_versions = None

        #
        self.search_root = None
        self.search_contains = None
        self.search_for = None
        self.search_version_regex = None
        self.regex_compiled = None
        self.versions_get_first = None
        self.versions_first = None
        self.versions_get_last = None
        self.versions_last = None
        self.settings_file = None
        self.settings_json = None
        self.place_source_default = None

        self.column_titles = ['Path', 'Open', 'Select']
        self.user_stopped = False

        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app
            # path into variable _MEIPASS'.
            #self.application_path = sys._MEIPASS.replace('\\', '/')
            self.application_path = os.path.dirname(
                sys.executable).replace('\\', '/')
        else:
            self.application_path = os.path.dirname(
                os.path.abspath(__file__)).replace('\\', '/')

        # settings
        prefs_pth = self.application_path + '\\settings.ini'
        print('-> init prefs')
        print('-> prefs: ' + prefs_pth)
        self.settings = QtCore.QSettings(prefs_pth, QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)    # File only
        try:
            self.settings_read()
        except:
            print('-> Failed to read preferences.')
            try:
                self.settings_set_defaults()
                self.settings_write()
                self.settings_read()
            except:
                print('-> Failed to write preferences.')



        # -------------------------------------------------------------------
        # signals
        # path
        self.ui.search_root.textChanged.connect(self.search_changed)
        self.ui.search_root_browse.clicked.connect(self.get_folder)
        # search
        self.ui.search_contains.textChanged.connect(self.search_changed)
        self.ui.search_for.textChanged.connect(self.search_changed)
        # versions
        self.ui.search_version_regex.textChanged.connect(self.versions_changed)
        self.ui.versions_get_first.clicked.connect(self.versions_changed)
        self.ui.versions_get_last.clicked.connect(self.versions_changed)
        self.ui.versions_first.valueChanged.connect(self.versions_changed)
        self.ui.versions_last.valueChanged.connect(self.versions_changed)
        # all
        self.ui.mark_all.clicked.connect(self.select_all)
        self.ui.mark_none.clicked.connect(self.select_none)

        self.ui.settings_file.textChanged.connect(self.display_json)

        # go
        self.ui.deadline.clicked.connect(self.go)
        # quit
        exit = QtGui.QAction(self)

        self.stop_short = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+.'), self)
        self.stop_short.activated.connect(self.user_stop)

        logging.basicConfig(
            filename=os.path.join(self.application_path, 'pack_nuke_gui.log')
            .replace('\\', '/'), level=logging.DEBUG)
        logging.info('Started at: ' + time.strftime("%Y-%m-%d, %H:%M"))

        self.model = JsonModel()
        self.ui.settings.setModel(self.model)
        self.display_json()

    def settings_set_defaults(self):

        self.settings.setValue('search_root', 'C:/projects/ProjectMeridian')
        self.settings.setValue('search_contains', '/work/comp/')
        self.settings.setValue('search_for', '*_comp_v???.nk')
        self.settings.setValue('search_version_regex', '.*_v(\d{3}).nk')
        self.settings.setValue('versions_get_first', False)
        self.settings.setValue('versions_first', 1)
        self.settings.setValue('versions_get_last', True)
        self.settings.setValue('versions_last', 1)
        self.settings.setValue('settings_file', '')
        self.settings.setValue('place_source_default', 'studio')

    def settings_write(self):
        """
        Write display settings to file
        """
        self.settings.setValue('search_root', self.ui.search_root.displayText())
        self.settings.setValue('search_contains', self.ui.search_contains.displayText())
        self.settings.setValue('search_for', self.ui.search_for.displayText())
        self.settings.setValue('search_version_regex', self.ui.search_version_regex.displayText())
        self.settings.setValue('versions_get_first', int(self.ui.versions_get_first.isChecked()))
        self.settings.setValue('versions_first', int(self.ui.versions_first.value()))
        self.settings.setValue('versions_get_last', int(self.ui.versions_get_last.isChecked()))
        self.settings.setValue('versions_last', int(self.ui.versions_last.value()))
        self.settings.setValue('settings_file', self.ui.settings_file.displayText())
        self.settings.setValue('place_source_default', self.ui.place_source_default.displayText())

    def settings_read(self):
        """
        Read settings from file
        """
        self.ui.search_root.blockSignals(True)
        self.ui.search_root.setText(self.settings.value('search_root'))
        self.ui.search_root.blockSignals(False)
        self.search_root = str(self.ui.search_root.displayText()).replace('\\', '/')

        self.ui.search_contains.blockSignals(True)
        self.ui.search_contains.setText(self.settings.value('search_contains'))
        self.ui.search_contains.blockSignals(False)
        self.search_contains = str(self.ui.search_contains.displayText()).replace('\\', '/')

        self.ui.search_for.blockSignals(True)
        self.ui.search_for.setText(self.settings.value('search_for'))
        self.ui.search_for.blockSignals(False)
        self.search_for = str(self.ui.search_for.displayText()).replace('\\', '/')

        self.ui.search_version_regex.blockSignals(True)
        self.ui.search_version_regex.setText(self.settings.value('search_version_regex'))
        self.ui.search_version_regex.blockSignals(False)
        self.search_version_regex = str(self.ui.search_version_regex.displayText())

        self.ui.versions_get_first.blockSignals(True)
        self.ui.versions_get_first.setChecked(int(self.settings.value('versions_get_first')))
        self.ui.versions_get_first.blockSignals(False)
        self.versions_get_first = int(self.ui.versions_get_first.isChecked())

        self.ui.versions_first.blockSignals(True)
        self.ui.versions_first.setValue(int(self.settings.value('versions_first')))
        self.ui.versions_first.blockSignals(False)
        self.versions_first = int(self.ui.versions_first.value())

        self.ui.versions_get_last.blockSignals(True)
        self.ui.versions_get_last.setChecked(int(self.settings.value('versions_get_last')))
        self.ui.versions_get_last.blockSignals(False)
        self.versions_get_last = int(self.ui.versions_get_last.isChecked())

        self.ui.versions_last.blockSignals(True)
        self.ui.versions_last.setValue(int(self.settings.value('versions_last')))
        self.ui.versions_last.blockSignals(False)
        self.versions_last = int(self.ui.versions_last.value())

        self.ui.settings_file.blockSignals(True)
        self.ui.settings_file.setText(self.settings.value('settings_file'))
        self.ui.settings_file.blockSignals(False)
        self.settings_file = str(self.ui.settings_file.toPlainText())

        self.ui.place_source_default.blockSignals(True)
        self.ui.place_source_default.setText(self.settings.value('place_source_default'))
        self.ui.place_source_default.blockSignals(False)
        self.place_source_default = str(self.ui.place_source_default.toPlainText())

    def closeEvent(self, event):
        self.settings_write()
        event.accept()

    def get_folder(self):
        file_name = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Starting Folder",
            str(self.ui.search_root.displayText())
        )
        fldr = os.path.realpath(file_name).replace('\\', '/')
        self.ui.search_root.setText(fldr)
        self.search_changed()

    def _get_search_gui(self):
        self.search_root = str(self.ui.search_root.displayText()).replace('\\', '/')
        self.search_contains = str(self.ui.search_contains.displayText()).replace('\\', '/')
        self.search_for = str(self.ui.search_for.displayText()).replace('\\', '/')
        self.search_version_regex = str(self.ui.search_version_regex.displayText())
        self.versions_get_first = int(self.ui.versions_get_first.isChecked())
        self.versions_first = int(self.ui.versions_first.value())
        self.versions_get_last = int(self.ui.versions_get_last.isChecked())
        self.versions_last = int(self.ui.versions_last.value())

    def search_changed(self):

        self._get_search_gui()

        # get versions
        self.find_versions()
        self.filter_versions()
        self.display_table()

    def versions_changed(self):
        self._get_search_gui()

        # get versions
        self.filter_versions()
        self.display_table()

    def explore_shot_from_table(self, row, column):
        self.explore(self.filtered_versions[row]['full'])

    def explore(self, path):

        platform = 'win'
        if sys.platform.startswith('darwin'):
            platform = 'mac'
        elif str(os.name).startswith('posix'):
            platform = 'nix'

        if path and path != '' and os.path.exists(path):
            if platform == 'win':
                if os.path.isdir(path):
                    path = path + '/'
                subprocess.Popen('explorer /root,  \"' + path.replace('/', '\\') + '\"')
            if platform == 'mac':
                subprocess.call(['open', "-R", path])
            if platform == 'nix':
                subprocess.call(('xdg-open', path))

    def find_versions(self):
        lst = {}
        for path in Path(self.search_root).rglob(self.search_for):
            _pth = str(path).replace('\\', '/')
            if self.search_contains in _pth:
                try:
                    _split = _pth.split('/')
                    if _split:
                        _last = str(_split[-1])
                        _start = str('/'.join(_split[:-1]))
                        if lst.get(_start):
                            # add to the list of subfolders
                            lst[_start].append(_last)
                        else:
                            # first subfolder
                            lst[_start] = [_last]
                except:
                    pass
        # sort versions
        for k, v in lst.items():
            vs = sorted(v)
            lst[k] = vs
        self.found_versions = lst

    def filter_versions(self):
        """
        This assumes the versions of the Nuke script are in one folder
        """

        self.filtered_versions = []
        try:
            self.regex_compiled = re.compile(self.search_version_regex)
            regex_valid = True
        except re.error:
            regex_valid = False
            print("Regex Error")
            return

        if self.found_versions is not None:
            for one_path, file_list in self.found_versions.items():

                one_folder = []
                for one_file in file_list:
                    my_dict = {}
                    m = self.regex_compiled.search(one_file)
                    if m:
                        try:
                            # if user made a group
                            version = m.group(1)
                            my_dict = {
                                'path': one_path,
                                'file': one_file,
                                'version': version,
                                'full': one_path + '/' + one_file,
                                'apply': True
                            }
                            one_folder.append(my_dict)
                        except:
                            pass
                #sort folder
                folder_sorted = sorted(one_folder, key=lambda i: i['version'])
                max_versions = len(folder_sorted)
                if bool(self.versions_get_first):
                    _first = self.versions_first
                    if max_versions < self.versions_first:
                        _first = max_versions
                    for i in range(0, _first):
                        self.filtered_versions.append(folder_sorted[i])
                if bool(self.versions_get_last):
                    _last = self.versions_last
                    if max_versions < self.versions_last:
                        _last = max_versions
                    for i in range(-1 * _last, 0):
                        self.filtered_versions.append(folder_sorted[i])
                if not bool(self.versions_get_first) and (not bool(self.versions_get_last)):
                    # add all
                    for one in folder_sorted:
                        self.filtered_versions.append(one)

    def _select_all_none(self, is_selected=True):
        for one_row in self.filtered_versions:
            one_row['apply'] = is_selected
        self.display_table()

    def select_all(self):
        self._select_all_none(True)

    def select_none(self):
        self._select_all_none(False)

    def handle_apply(self, row, column):
        _apply = bool(self.filtered_versions[row]['apply'])
        if _apply:
            self.filtered_versions[row]['apply'] = False
        else:
            self.filtered_versions[row]['apply'] = True
        #self.display_table()

    def display_json(self):

        self.settings_file = str(self.ui.settings_file.displayText()).replace('\\', '/')
        if self.settings_file is not None and self.settings_file != '':
            if Path(self.settings_file).is_file():
                with open(self.settings_file) as settings_file:
                    self.settings_json = json.load(settings_file)
                    self.model.load(self.settings_json)

                self.ui.settings.show()
                self.ui.settings.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
                #self.ui.settings.setAlternatingRowColors(True)

    def display_table(self):

        # display table
        self.ui.tableWidget.clear()
        self.ui.tableWidget.setColumnCount(0)
        self.ui.tableWidget.setRowCount(0)

        if self.filtered_versions and self.column_titles:
            self.ui.tableWidget.setSortingEnabled(False)
            self.ui.tableWidget.setColumnCount(len(self.column_titles))
            self.ui.tableWidget.setHorizontalHeaderLabels(self.column_titles)
            self.ui.tableWidget.setRowCount(len(self.filtered_versions))

            for row, line in enumerate(self.filtered_versions):
                # set row color by check list
                color = 'white'

                # for every column in a row
                for column_number, one_column in enumerate(self.column_titles):
                    my_title = str(one_column).lstrip().rstrip().lower()

                    if my_title == 'open':
                        btn = QtWidgets.QPushButton('Open', self)
                        btn.setIcon(QtGui.QIcon(":/images/system-search.png"))
                        index = QtCore.QPersistentModelIndex(self.ui.tableWidget.model().index(row, column_number))

                        # partial instead of lambda!
                        btn.clicked.connect(partial(self.explore_shot_from_table, index.row(), index.column()))
                        self.ui.tableWidget.setCellWidget(row, column_number, btn)
                    elif my_title == 'select':
                        chbx = QtWidgets.QCheckBox('Select ', self)
                        chbx.setChecked(line['apply'])
                        index = QtCore.QPersistentModelIndex(self.ui.tableWidget.model().index(row, column_number))
                        # partial instead of lambda!
                        chbx.clicked.connect(partial(self.handle_apply, index.row(), index.column()))
                        self.ui.tableWidget.setCellWidget(row, column_number, chbx)
                    elif my_title == 'path':
                        self.ui.tableWidget.setItem(row, column_number,
                                                    QtWidgets.QTableWidgetItem(
                                                        str(line['full'])))
                    else:
                        logging.error("Can't display table row")

                    # colorize cell
                    itm = self.ui.tableWidget.item(row, column_number)
                    if itm:
                        if color == 'green':
                            itm.setBackground(QtGui.QColor('darkgreen'))
                        elif color == 'orange':
                            itm.setBackground(QtGui.QColor('sienna'))
                        elif color == 'red':
                            itm.setBackground(QtGui.QColor('maroon'))
                        elif color == 'purple':
                            itm.setBackground(QtGui.QColor('purple'))
                        else:
                            # white
                            itm.setBackground(QtGui.QColor("#4d4d4d"))

            self.ui.tableWidget.setSortingEnabled(True)
            self.ui.tableWidget.resizeColumnsToContents()
            self.ui.tableWidget.resizeRowsToContents()

    def apply(self, nuke_file):
        pass


    def go(self):

        total = 0
        files = []
        for one in self.filtered_versions:
            if one['apply']:
                total += 1
                files.append(one['full'])
        total_versions = len(self.filtered_versions)

        _go = False
        button = QtWidgets.QMessageBox.question(
            self, "Do or don't, there is no try!",
            "Are you sure to apply python script to {} Nuke scripts?".format(total))
        if button == QtWidgets.QMessageBox.Yes:
            _go = True
        if _go:
            logging.info('Processing started at: ' + time.strftime("%Y-%m-%d, %H:%M"))
            cnt = 1
            go_time = time.time()
            self.ui.execute.setText('Processing ' + str(total) + ' scripts')
            self.ui.execute.setEnabled(False)
            success = []
            for row, line in enumerate(self.filtered_versions):
                QApplication.processEvents()
                if self.user_stopped:
                    print("Breaking")
                    break

                if bool(line['apply']):
                    start_time = time.time()
                    self.ui.tableWidget.item(row, 0).setBackground(QtGui.QColor('darkgreen'))
                    self.ui.tableWidget.repaint()
                    logging.info(line['full'])

                    # apply
                    apply_ok = self.apply(line['full'])
                    if not apply_ok:
                        logging.error('Error processing file: {}'.format(line['full']))
                    else:
                        success.append(os.path.basename(line['full']) + '\n')

                    last_apply_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - start_time))
                    elapsed_time = time.strftime("%H:%M:%S", time.gmtime(time.time() - go_time))
                    average = float(time.time() - go_time) / float(cnt)
                    time_needed = time.strftime("%H:%M:%S", time.gmtime((total - cnt) * average))
                    status = "Just Processed file {}/{}: {}.Last apply time: {}, elapsed time: {}, estimated time: {}".format(cnt, total, line['file'], last_apply_time, elapsed_time, time_needed)
                    self.ui.execute.setText(status)
                    logging.info(status)
                    cnt += 1

                    # uncheck apply for item that is done
                    self.handle_apply(row, 0)

            # Change back to ready
            logging.info('Processed files: \n{}'.format(''.join(success)))

            self.ui.execute.setText('Execute')
            self.ui.execute.setEnabled(True)

    def user_stop(self):
        QApplication.processEvents()
        self.user_stopped = True
        print("-> User Stop!")
        QApplication.processEvents()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Plastique")
    app = app.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)

    main = MainWindow()
    main.show()
    sys.exit(app.exec())
