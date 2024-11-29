# This Python file uses the following encoding: utf-8

import csv
import datetime
from functools import partial
import json
import logging
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from typing import Any, List, Dict, Union

from PySide6 import QtWidgets, QtGui
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

        self.found_versions_counter = 0
        self.place_list = None
        self.ui = Ui_pack_gui()
        self.ui.setupUi(self)
        ui_images_rc.qInitResources()
        #self.resize(1400, 300)

        # data structs
        self.found_versions = None
        self.filtered_versions = None

        # from the gui
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
        self.settings_json = {}
        self.place_source_default = None

        self.column_titles = ['Path', 'Tokens', 'Open', 'Select']
        self.user_stopped = False
        self.place_list = []
        self.place_source = ''
        self.place_target = ''
        self.anatomy = {}



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
        prefs_pth = self.application_path + '/settings.ini'
        print('-> init prefs')
        print('-> prefs: ' + prefs_pth)
        self.settings = QtCore.QSettings(prefs_pth, QtCore.QSettings.IniFormat)
        self.settings.setFallbacksEnabled(False)    # File only
        try:
            self.settings_read()
        except Exception as e:
            print('-> Failed to read preferences.')
            try:
                self.settings_set_defaults()
                self.settings_write()
                self.settings_read()
            except Exception as e:
                print('-> Failed to write preferences.')

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
        # mark all/none
        self.ui.mark_all.clicked.connect(self.select_all)
        self.ui.mark_none.clicked.connect(self.select_none)

        # places change
        self.ui.place_source.currentIndexChanged.connect(self.place_change)
        self.ui.place_target.currentIndexChanged.connect(self.place_change)

        # job name
        self.ui.job_name.textChanged.connect(self._validate_job_name)

        # job folder browse
        self.ui.job_folder_browse.clicked.connect(self.get_job_folder)

        # settings json path
        self.ui.settings_file.textChanged.connect(self.display_json)

        # go
        self.ui.deadline.clicked.connect(self.go)
        # quit

        self.stop_short = QtGui.QShortcut(QtGui.QKeySequence('Ctrl+.'), self)
        self.stop_short.activated.connect(self.user_stop)

        # show settings json
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
        self.settings_file = str(self.ui.settings_file.displayText())

        self.ui.place_source_default.blockSignals(True)
        self.ui.place_source_default.setText(self.settings.value('place_source_default'))
        self.ui.place_source_default.blockSignals(False)
        self.place_source_default = str(self.ui.place_source_default.displayText())

    def display_json(self):
        """Reads json settings file and displays in GUI
        Will also populate places and job path in GUI

        """

        def load_settings_from_file(file_path):
            """Load JSON settings from a specified file path."""
            try:
                with open(file_path) as file:
                    return json.load(file)
            except FileNotFoundError:
                logger.error(f"Settings file {file_path} not found.")
            except json.JSONDecodeError:
                logger.error(f"Error decoding the JSON settings file {file_path}")
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}\n{file_path}")
            return None

        def configure_settings_ui(ui):
            """Configure the settings UI elements."""
            ui.settings.show()
            ui.settings.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            # self.ui.settings.setAlternatingRowColors(True)

        self.settings_file = str(self.ui.settings_file.displayText()).replace('\\', '/')
        if self.settings_file:
            self.settings_json = load_settings_from_file(self.settings_file)
            if self.settings_json:
                self.model.load(self.settings_json)
                configure_settings_ui(self.ui)
            else:
                logger.critical(f"Settings not available, packing will fail.")

        if self.settings_json is not None and self.settings_json != {}:
            self.ui.job_template.setText(self.settings_json['job']['job_name_check'])
            self.ui.job_template.setText(self.settings_json['job']['job_name_check'])

            self.place_list = list(self.settings_json['places'].keys())
            if len(self.place_list) >= 2:
                self.ui.place_source.blockSignals(True)
                self.ui.place_source.clear()
                self.ui.place_source.addItems(self.place_list)
                self.ui.place_target.blockSignals(True)
                self.ui.place_target.clear()
                self.ui.place_target.addItems(self.place_list)
                try:
                    preferred_source = self.ui.place_source_default.displayText()
                    if preferred_source in self.place_list:
                        i = self.place_list.index(preferred_source)
                        self.ui.place_source.setCurrentIndex(i)
                        # set target to close place that is not source
                        if i == 0:
                            self.ui.place_target.setCurrentIndex(1)
                        else:
                            self.ui.place_target.setCurrentIndex(0)
                    else:
                        self.ui.place_source.setCurrentIndex(0)
                        self.ui.place_target.setCurrentIndex(1)
                except:
                    logger.error("Failed to set places dropbox")

                self.ui.place_source.blockSignals(False)
                self.ui.place_target.blockSignals(False)
                self._fill_job_path()
            else:
                logger.error(
                    f"Found {len(self.place_list)} places defined in settings json. At least two are required.")

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

    def get_job_folder(self):
         file_name = QtWidgets.QFileDialog.getExistingDirectory(
             self,
             "Select Job Folder",
             str(self.ui.job_folder.displayText())
         )
         self.ui.job_folder.setText(os.path.realpath(file_name).replace('\\', '/'))

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

    def external_execute(self, args):

        kwargs = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True  # Automatically decodes to string
        }
        if platform.system().lower() == "windows":
            kwargs["creationflags"] = (
                    subprocess.CREATE_NEW_PROCESS_GROUP
                    | getattr(subprocess, "DETACHED_PROCESS", 0)
                    | getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
        popen = subprocess.Popen(args, **kwargs)
        popen_stdout, popen_stderr = popen.communicate()
        if popen_stdout:
            print(popen_stdout)
        if popen_stderr:
            print(f"Error: {popen_stderr}")

        # Check the return code
        if popen.returncode != 0:
            print(f"Command failed with return code {popen.returncode}")

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

    def apply(self, nuke_file):
        pass

    def user_stop(self):
        QApplication.processEvents()
        self.user_stopped = True
        print("-> User Stop!")
        QApplication.processEvents()

    def find_versions(self):
        """Crawl source folder and find all Nuke files (versions)

        self.found_versions are stored in a dictionary with the following structure:
            key: path to folder containing the version files
            value: list of version file names
        """

        def normalize_path(file_path: str) -> str:
            """Convert path to a uniform format with forward slashes."""
            return str(file_path).replace('\\', '/')

        def add_to_version_list(split_folders: list, version_dict: dict[str, list[str]]):
            """Add extracted path parts to the version dictionary."""
            base_path = '/'.join(split_folders[:-1])
            folder_name = split_folders[-1]
            self.found_versions_counter += 1
            if base_path in version_dict:
                version_dict[base_path].append(folder_name)
            else:
                version_dict[base_path] = [folder_name]

        def sort_versions(version_dict: dict[str, list[str]]) -> dict[str, list[str]]:
            """Sort versions found in the directory structure."""
            return {k: sorted(v) for k, v in version_dict.items()}

        logger.debug(f"Searching for versions in {self.search_root}")
        version_dict = {}
        self.found_versions_counter = 0

        for path in Path(self.search_root).rglob(self.search_for):
            normalized_path = normalize_path(path)

            if self.search_contains in normalized_path:
                try:
                    path_parts = normalized_path.split('/')
                    if path_parts:
                        add_to_version_list(path_parts, version_dict)
                except Exception as e:  # Specify the exception type if known
                    logger.error(f"Failed to process path {normalized_path}: {e}")

        self.found_versions = sort_versions(version_dict)
        logger.debug(f"Found {self.found_versions_counter} versions.")

    def filter_versions(self):
        """ Filter out versions based on settings
        Search for only if contains string in whole path
        Use version regex to parse version out of the file name
        Use first m and last n versions

        This assumes the versions of the Nuke script are in one folder.

        self.filtered_versions is a dict with following structure:
            key: path to folder containing the version files
            value: list of version file names
        """

        def match_regex(regex_filter: list[dict], input_source:str) -> str:
            """Checks if the regex_filter matches the input_source by regex

            Returns the matched first group or replace regex
            """

            def _replace_with_regex(pattern, regex_filter, input_source):
                if regex_filter.get('replace'):
                    try:
                        return pattern.match(input_source).expand(regex_filter['replace'])
                    except (AttributeError, re.error):
                        return None
                return None

            def _get_group(pattern, input_source):
                match = pattern.search(input_source)
                if match:
                    try:
                        return match.group(1)
                    except IndexError:
                        return match.group(0)
                return None

            def _apply_case_modifications(result, regex_filter):
                if result:
                    if regex_filter.get('lowercase'):
                        result = result.lower()
                    if regex_filter.get('uppercase'):
                        result = result.upper()
                return result

            if not regex_filter.get('search'):
                return None

            try:
                pattern = re.compile(regex_filter['search'])
            except re.error:
                return None

            result = _replace_with_regex(pattern, regex_filter, input_source)
            if result is None:
                result = _get_group(pattern, input_source)

            return _apply_case_modifications(result, regex_filter)

        def compile_regex():
            """Compile regex for searching versions."""
            try:
                self.regex_compiled = re.compile(self.search_version_regex)
                return True
            except re.error:
                logger.error("Version Regex Error")
                return False

        def get_script_path_tags(full_path: str) -> dict:
            """Get tags from file name or file path.
            There can be one or more tags stored as list of dicts defined in settings json
            ['places'][place_source]['use_script_path_tags']

            Each dict contains the following:
                "name" : the name of the tag
                "source": filename or path
                "search": regular expression to match
                "replace": regular expression to replace
                "lowercase": True or False, lowercase the result
                "uppercase": True or False, uppercase the result

            Returns dict with tags
                "tag name" : matching value
            """

            if self.settings_json is None:
                return {}
            place_source = self.ui.place_source.currentText()
            if not self.settings_json['places'][place_source]['use_script_path_tags']:
                return {}
            tags_list = self.settings_json['places'][place_source]['script_path_tags']
            if tags_list is None or len(tags_list) == 0:
                return {}

            tokens = {}
            for one_filter in tags_list:
                match = None
                if one_filter['source'] == 'File Name':
                    match = match_regex(one_filter, input_source=os.path.basename(full_path))
                elif one_filter['source'] == 'File Path':
                    match = match_regex(one_filter, input_source=full_path.replace('\\', '/'))

                if match is not None:
                    tokens[one_filter['name']] = match
            return tokens

        def extract_version_info(folder_path:str, file_name:str) -> dict:
            """Extract version information from a single file.

            Returns dict with following keys:
                'path': folder_path,
                'file': file_name,
                'full': f"{folder_path}/{file_name}",
                'version': version number
                'apply': bool value user-selecting the version in the gui
                'tokens': tokens parsed from the path
            """
            match = self.regex_compiled.search(file_name)
            if match:
                try:
                    version = match.group(1)
                    tokens = get_script_path_tags(f"{folder_path}/{file_name}")
                    if tokens:
                        token_str = ';'.join(f"{k}:{v}" for k, v in {**tokens, **self.anatomy}.items())
                    else:
                        token_str = ''
                    return {
                        'path': folder_path,
                        'file': file_name,
                        'version': version,
                        'full': f"{folder_path}/{file_name}",
                        'apply': True,
                        'tokens': token_str
                    }
                except Exception as e:
                    logger.error(f"Failed to parse {file_name} : {e}", exc_info=True)
            else:
                logger.warning(f"No version match found for file: {file_name}")
            return {}

        def process_folder(folder_path:str, files:list) -> list:
            """Process all files in a folder: extract version information.
            Returns sorted dict with versions
            """
            version_info_list = []
            for file_name in files:
                version_info = extract_version_info(folder_path, file_name)
                if version_info:
                    version_info_list.append(version_info)
            return sorted(version_info_list, key=lambda x: x['version'])

        def add_filtered_versions(folder_data):
            """Extends filtered versions based on version limiting settings.
            """
            max_versions = len(folder_data)
            if self.versions_get_first:
                items_to_append = folder_data[:min(self.versions_first, max_versions)]
            elif self.versions_get_last:
                items_to_append = folder_data[max_versions - min(self.versions_last, max_versions):]
            else:
                items_to_append = folder_data

            self.filtered_versions.extend(items_to_append)

        if self.settings_json is None:
            logger.error("Settings json not loaded. Cannot parse tags from paths.")

        self.filtered_versions = []
        if not compile_regex():
            return

        if self.found_versions is not None:
            for folder_path, files in self.found_versions.items():
                folder_data = process_folder(folder_path, files)
                add_filtered_versions(folder_data)
        logger.debug(f"{len(self.filtered_versions)} versions available after filtering.")

    @staticmethod
    def my_time():
        """
        Used for timestamping packages
        Stores UTC time, and adds UTC offset for user comfort
        Offset assumes plus sign, unless - present
        """
        # get utc time YYMMDD-HHMM_
        utc = datetime.datetime.now(datetime.timezone.utc).strftime('%y%m%d_%H%M_')
        # get utc to local time offset, this is just for user
        offset = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime('%z').replace('+', '')
        return utc + offset

    def _fill_job_path(self):
        class Default(dict):
            def __missing__(self, key):
                return key

        if self.settings_json is None or self.settings_json == {}:
            return None
        if self.place_list is None or self.place_list == []:
            return None
        place_source = self.ui.place_source.currentText()
        place_target = self.ui.place_target.currentText()

        self.settings_json['places'][place_source]['is_source'] = True
        self.settings_json['places'][place_source]['is_target'] = False
        self.settings_json['places'][place_target]['is_source'] = False
        self.settings_json['places'][place_target]['is_target'] = True

        self.anatomy = {
            'timestamp': self.my_time(),
            'place_source': place_source,
            'place_target': place_target,
        }
        self.anatomy.update(self.settings_json['places'][place_source]['anatomy'])

        # job root
        self.ui.job_folder.setText(
            self.settings_json['job']['job_root'].format_map(Default(self.anatomy)).replace("\\", "/"))
        self.ui.job_folder.setEnabled(False)
        self.ui.job_folder_browse.setEnabled(False)

        # job folder
        self.ui.job_name.setText(
            self.settings_json['job']['job_name_default'].format_map(Default(self.anatomy)).replace("\\", "/"))
        self.ui.job_name.setEnabled(False)

    def _validate_job_name(self):
        if not re.match(self.ui.job_template.displayText(), self.ui.job_name.displayText()):
            logger.error("Make sure job name matches convention.")
            return False
        else:
            logger.info("Job name matches convention.")
            return True

    def place_change(self):
        place_source = self.ui.place_source.currentText()
        place_target = self.ui.place_target.currentText()
        if place_source == place_target:
            logging.error("Source and target places have to be different")
        else:
            self._fill_job_path()

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
                    elif my_title == 'tokens':
                        self.ui.tableWidget.setItem(row, column_number,
                                                    QtWidgets.QTableWidgetItem(
                                                        str(line['tokens'])))
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

    def go(self):
        """Writes json settings and csv file to the job path and sends packing to Deadline."""

        def create_and_verify_directory(path):
            """Creates a directory if it doesn't exist and verifies its creation."""
            try:
                os.makedirs(path, exist_ok=True)
                if not os.path.isdir(path):
                    logging.critical(f"Directory was not created: {path}")
                    return False
                return True
            except OSError as e:
                logging.critical(f"Error creating directory {path}: {e}")
                return False

        def write_csv_file(path, headers, data_rows):
            """Writes data to a CSV file."""
            try:
                with open(path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(data_rows)
            except OSError as e:
                logging.error(f"Error writing CSV file {path}: {e}")

        def execute_deadline_jobs():
            nuke_exe = self.settings_json['nuke'].get(platform.system()).replace('\\', '/')
            deadline_exe = self.settings_json['deadline'].get(platform.system()).replace('\\', '/')
            deadline_py = self.settings_json['deadline_python'].get(platform.system()).replace('\\', '/')

            if nuke_exe is None or not os.path.exists(nuke_exe):
                logging.critical(f"Can't find Nuke executable: {nuke_exe}")
                return
            if deadline_exe is None or not os.path.exists(deadline_exe):
                logging.critical(f"Can't find Deadline executable: {deadline_exe}")
                return
            if deadline_py is None or not os.path.exists(deadline_py):
                logging.critical(f"Can't find Deadline python file: {deadline_py}")
                return

            job_path = self.settings_json['job']['path'].replace('\\', '/') + '/_pack_nuke'
            params_1 = [
                deadline_exe, '-SubmitCommandLineJob', '-executable', nuke_exe,
                '-pool', self.settings_json['deadline_job']['pool'],
                '-group', self.settings_json['deadline_job']['group'],
                '-priority', str(self.settings_json['deadline_job']['priority']),
                '-department', self.settings_json['deadline_job']['department'],
                '-prop', f"LimitGroups={self.settings_json['deadline_job']['LimitGroups']}",
                f"outputDir={job_path}"
            ]
            json_settings_path = os.path.join(job_path, 'settings.json').replace('\\', '/')

            for version in selected_versions:
                # the deadline arguments have to be quoted, so pre-joining here
                deadline_args = " ".join(["-t", deadline_py, version[3], json_settings_path, version[0]])
                params_2 = [
                    '-name', version[0], # id
                    '-arguments', deadline_args
                ]
                logger.info(f"Submitting job: {params_1 + params_2}")
                self.external_execute(params_1 + params_2)

        gui_job_path = self.ui.job_folder.displayText()
        gui_job_name = self.ui.job_name.displayText()
        gui_source = self.ui.place_source.currentText()
        gui_target = self.ui.place_target.currentText()
        job_path = os.path.join(gui_job_path, gui_job_name)

        self.settings_json['job']['path'] = job_path
        self.settings_json['job']['name'] = gui_job_name
        self.settings_json['job']['timestamp'] = self.anatomy['timestamp']

        if not create_and_verify_directory(job_path):
            return
        pack_dir = os.path.join(job_path, '_pack_nuke')
        if not create_and_verify_directory(pack_dir):
            return

        # Write CSV file with all Nuke scripts
        csv_file_path = os.path.join(pack_dir, 'nuke_files.csv')
        csv_titles = ['Id', 'Name', 'Version', 'Full Path', 'Tokens', 'Package', 'Source', 'Target']

        selected_versions = [
            [f"{str(index).zfill(4)}_{one['file'].rstrip('.nk')}", one['file'], one['version'], one['full'],
             one['tokens'], gui_job_name, gui_source, gui_target]
            for index, one in enumerate(self.filtered_versions) if one['apply']
        ]
        write_csv_file(csv_file_path, csv_titles, selected_versions)

        # Write settings file
        settings_file_path = os.path.join(pack_dir, 'settings.json')
        try:
            with open(settings_file_path, 'w') as json_file:
                json.dump(self.settings_json, json_file)
        except OSError as e:
            logging.error(f"Error writing settings file {settings_file_path}: {e}")

        execute_deadline_jobs()


def get_app_path():
    application_path = None
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the app
        # path into variable _MEIPASS'.
        #self.application_path = sys._MEIPASS.replace('\\', '/')
        application_path = os.path.dirname(sys.executable).replace('\\', '/')
    else:
        application_path = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
    return application_path


if __name__ == "__main__":

    # log
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter_time = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
    formatter = logging.Formatter('%(levelname)s:%(message)s')
    app_path = get_app_path()
    if app_path is not None:
        app_path += '/pack_nuke_gui.log'
        file_handler = logging.FileHandler(app_path)
        logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Plastique")
    app = app.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)

    main = MainWindow()
    main.show()
    sys.exit(app.exec())
