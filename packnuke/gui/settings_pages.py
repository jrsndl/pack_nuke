"""Settings sub-pages: Nuke Scripts and Categories editors.

Both edit ``state.settings`` in place and call ``commit()`` after every change. Path fields show
the resolved result for the preview script (first Queue item / selected found script).
"""
from __future__ import annotations

import copy
import os
from typing import Any, Callable, Dict, List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import filters, paths, preflight, sequences, settings as settings_mod, templates
from .state import AppState
from .widgets import button, hbox, hint, label, vbox

MISSING = '#ff7f50'
OK = '#7fc97f'


class ResolvedLabel(QtWidgets.QLabel):
    """Shows a template resolved with the preview tokens; missing tokens in orange."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('hint')
        self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)

    def show_template(self, template: str, tokens: Dict[str, Any]) -> None:
        if not template:
            self.setText('')
            self.setToolTip('')
            return
        resolved = templates.format_template(template, tokens, strict=False)
        missing = templates.missing_tokens(template, tokens)
        if missing:
            self.setText('→ {}   (missing: {})'.format(resolved, ', '.join(missing)))
            self.setStyleSheet('color: {};'.format(MISSING))
        else:
            self.setText('→ ' + resolved)
            self.setStyleSheet('')
        self.setToolTip('Resolved for the preview script:\n' + resolved)


def preview_tokens(state: AppState, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    tok = dict(preflight.dynamic_tokens(state.settings))
    script = state.preview_script()
    if script:
        tok.update(state.script_tokens(script))
    else:
        tok.update(state.base_tokens())
        tok.setdefault('job', state.auto_job_root() + '/' + state.auto_job_name())
    if extra:
        tok.update(extra)
    return tok


# ====================================================================== Nuke scripts

SCRIPT_HELP = {
    'source': 'An untouched copy of the original Nuke script.',
    'package': 'The script inside the package, relinked to the copied files.',
    'target': 'A script prepared for the receiving place: links point to the *_relink locations '
              '(category "relink" templates) and relative paths are computed from "Path at target".',
}


class NukeScriptsPage(QtWidgets.QWidget):
    def __init__(self, state: AppState, commit: Callable[[], None], parent=None):
        super().__init__(parent)
        self.state = state
        self.commit = commit
        self._loading = False
        self.w: Dict[str, Dict[str, Any]] = {}
        lay = QtWidgets.QVBoxLayout(self)
        lay.addWidget(hint('Where the three Nuke scripts of every packed script are written. Templates use '
                           'tokens like {job}, {SHOT}, {script_name}. The line under each path shows it '
                           'resolved for the preview script.'))
        for which in ('source', 'package', 'target'):
            lay.addWidget(self._group(which))
        lay.addStretch(1)

    def _line(self, which: str, key: str, tip: str) -> QtWidgets.QWidget:
        edit = QtWidgets.QLineEdit()
        edit.setToolTip(tip)
        edit.textEdited.connect(self._edited)
        res = ResolvedLabel()
        self.w[which][key] = edit
        self.w[which][key + ':res'] = res
        box = QtWidgets.QWidget()
        box.setLayout(vbox(edit, res, spacing=1))
        return box

    def _group(self, which: str) -> QtWidgets.QGroupBox:
        self.w[which] = {}
        box = QtWidgets.QGroupBox('{} script'.format(which.capitalize()))
        box.setToolTip(SCRIPT_HELP[which])
        form = QtWidgets.QFormLayout(box)
        copy_cb = QtWidgets.QCheckBox('Write this script')
        copy_cb.setToolTip('nuke_scripts.{}.copy - switch off to skip this script.'.format(which))
        copy_cb.toggled.connect(self._edited)
        self.w[which]['copy'] = copy_cb
        form.addRow('', copy_cb)
        form.addRow('Path:', self._line(which, 'path', 'Where the script is written (inside the package).'))
        if which == 'target':
            form.addRow('Path at target:', self._line(
                which, 'path_relink', 'Where the script will live at the receiving place. Relative links are '
                                      'computed from here.'))
        if which in ('package', 'target'):
            rel = QtWidgets.QCheckBox('Relative file paths')
            rel.setToolTip('Write file paths relative to the project directory (set in the script) '
                           'instead of absolute paths.')
            above = QtWidgets.QSpinBox()
            above.setRange(0, 20)
            above.setToolTip('Project directory = the script folder, or this many folders above it.')
            custom = QtWidgets.QCheckBox('Custom project directory')
            custom.setToolTip('Use the template below as the project directory instead of the script folder.')
            for w in (rel, custom):
                w.toggled.connect(self._edited)
            above.valueChanged.connect(self._edited)
            self.w[which].update({'relative': rel, 'relative_above_script': above,
                                  'relative_custom_project': custom})
            form.addRow('', rel)
            form.addRow('Folders above script:', above)
            form.addRow('', custom)
            form.addRow('Project directory:', self._line(
                which, 'relative_custom_project_template', 'Template of the custom project directory.'))
        return box

    def reload(self) -> None:
        ns = self.state.settings['nuke_scripts']
        self._loading = True
        try:
            for which, widgets in self.w.items():
                sec = ns.get(which) or {}
                for key, w in widgets.items():
                    if key.endswith(':res'):
                        continue
                    if isinstance(w, QtWidgets.QCheckBox):
                        w.setChecked(bool(sec.get(key, key == 'copy')))
                    elif isinstance(w, QtWidgets.QSpinBox):
                        w.setValue(int(sec.get(key, 0) or 0))
                    else:
                        w.setText(str(sec.get(key, '') or ''))
        finally:
            self._loading = False
        self._enable()
        self.refresh_previews()

    def _enable(self) -> None:
        for which, widgets in self.w.items():
            on = widgets['copy'].isChecked()
            for key, w in widgets.items():
                if key != 'copy':
                    w.setEnabled(on)
            if 'relative' in widgets and on:
                rel = widgets['relative'].isChecked()
                custom = widgets['relative_custom_project'].isChecked()
                widgets['relative_above_script'].setEnabled(rel and not custom)
                widgets['relative_custom_project'].setEnabled(rel)
                widgets['relative_custom_project_template'].setEnabled(rel and custom)
                widgets['relative_custom_project_template:res'].setEnabled(rel and custom)

    def _edited(self, *_args) -> None:
        if self._loading:
            return
        ns = self.state.settings['nuke_scripts']
        for which, widgets in self.w.items():
            sec = ns.setdefault(which, {})
            for key, w in widgets.items():
                if key.endswith(':res'):
                    continue
                if isinstance(w, QtWidgets.QCheckBox):
                    sec[key] = w.isChecked()
                elif isinstance(w, QtWidgets.QSpinBox):
                    sec[key] = w.value()
                else:
                    sec[key] = w.text()
        self._enable()
        self.refresh_previews()
        self.commit()

    def refresh_previews(self) -> None:
        tok = preview_tokens(self.state)
        for which, widgets in self.w.items():
            for key, w in widgets.items():
                if key.endswith(':res'):
                    w.show_template(widgets[key[:-4]].text(), tok)


# ====================================================================== Categories

FILTER_COLUMNS = ['Source', 'Search', 'Check (comma separated)', 'Token name', 'Invert', 'Test']


class CategoriesPage(QtWidgets.QWidget):
    def __init__(self, state: AppState, commit: Callable[[], None], parent=None):
        super().__init__(parent)
        self.state = state
        self.commit = commit
        self._loading = False
        self._build()

    # ------------------------------------------------------------------ UI
    def _build(self) -> None:
        self.list = QtWidgets.QListWidget()
        self.list.setToolTip('Categories are evaluated in this order. With "first matching category only" '
                             '(Farm & Misc) the order decides. Double click to rename.')
        self.list.currentRowChanged.connect(lambda _r: self._load_category())
        self.list.itemDoubleClicked.connect(lambda _i: self.rename())
        left = QtWidgets.QWidget()
        left.setLayout(vbox(
            label('Categories'), self.list,
            hbox(button('Add', self.add, 'Create a new category'),
                 button('Duplicate', self.duplicate, 'Copy the selected category under a new name')),
            hbox(button('Rename', self.rename, 'Rename the selected category ({category} token)'),
                 button('Delete', self.delete, 'Delete the selected category')),
            hbox(button('Up', lambda: self.move(-1), 'Move the category up'),
                 button('Down', lambda: self.move(1), 'Move the category down'))))

        # paths
        self.fields: Dict[str, QtWidgets.QLineEdit] = {}
        self.resolved: Dict[str, ResolvedLabel] = {}
        path_box = QtWidgets.QGroupBox('Paths')
        pf = QtWidgets.QFormLayout(path_box)
        for key, title, tip in (
                ('root_template', 'Package root:', 'Folder in the package, e.g. {job}/{SHOT}/{category}'),
                ('top_folder', 'Top folder:', 'Sub folder per file, e.g. {node} or {clean_name}. The file name is '
                                              'never changed, so this keeps different files with the same name apart.'),
                ('root_template_relink', 'Relink root:', 'Where the same files will be at the receiving place '
                                                        '(used by the target script).'),
                ('top_folder_relink', 'Relink top folder:', 'Sub folder at the receiving place.')):
            e = QtWidgets.QLineEdit()
            e.setToolTip(tip)
            e.textEdited.connect(self._edited)
            self.fields[key] = e
            pf.addRow(title, e)
        for key, title in (('package', 'Package folder:'), ('relink', 'Folder at target:')):
            r = ResolvedLabel()
            self.resolved[key] = r
            pf.addRow(title, r)
        pf.addRow('', hint('Per file tokens: {category} {node} {node_class} {knob} {clean_name} {extension} '
                           'plus the token names of the filters below.'))

        # options
        self.skip_disconnected = QtWidgets.QCheckBox('Skip disconnected nodes')
        self.skip_disconnected.setToolTip('Nodes without inputs and outputs (often old, unused Reads) do not '
                                          'belong to this category.')
        self.skip_disabled = QtWidgets.QCheckBox('Skip disabled nodes')
        self.skip_disabled.setToolTip('Disabled nodes do not belong to this category.')
        self.combine = QtWidgets.QComboBox()
        self.combine.addItems(['AND', 'OR'])
        self.combine.setToolTip('AND: every filter must hit. OR: one hit is enough.')
        for w in (self.skip_disconnected, self.skip_disabled):
            w.toggled.connect(self._edited)
        self.combine.currentTextChanged.connect(self._edited)
        opt_box = QtWidgets.QGroupBox('Options')
        opt_box.setLayout(hbox(self.skip_disconnected, self.skip_disabled, 16, label('Combine filters:'),
                               self.combine, None, margins=6))

        # filters
        self.filters = QtWidgets.QTableWidget(0, len(FILTER_COLUMNS))
        self.filters.setHorizontalHeaderLabels(FILTER_COLUMNS)
        self.filters.verticalHeader().setVisible(False)
        self.filters.verticalHeader().setDefaultSectionSize(24)
        self.filters.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.filters.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        for c, w in ((0, 100), (2, 170), (3, 120), (4, 50), (5, 150)):
            self.filters.setColumnWidth(c, w)
        self.filters.setToolTip(
            'Source: what is tested (file name, full file path, node class, knob name).\n'
            'Search: regex (for Node Class: space separated class names). Group 1 is the value.\n'
            'Check: if not empty, the filter hits only when the value is one of these (case-insensitive).\n'
            'Token name: the value becomes a token, e.g. {extension}.\n'
            'Invert: flips the hit.  Test: result for the test file below.')
        self.filters.itemChanged.connect(self._edited)
        filt_box = QtWidgets.QGroupBox('Filters')
        filt_box.setLayout(vbox(
            self.filters,
            hbox(button('Add filter', self.add_filter, 'Add a filter row'),
                 button('Remove', self.remove_filters, 'Remove the highlighted filters'),
                 button('Up', lambda: self.move_filter(-1), 'Move the current filter up'),
                 button('Down', lambda: self.move_filter(1), 'Move the current filter down'), None),
            margins=6))

        # test
        self.test_path = QtWidgets.QLineEdit()
        self.test_path.setPlaceholderText('e.g. //server/prj/shots/sh010/plates/sh010_plate.%04d.exr')
        self.test_path.setToolTip('A file path to test this category with. A sequence pattern or one frame works.')
        self.test_class = QtWidgets.QLineEdit('Read')
        self.test_class.setToolTip('Node class of the test node.')
        self.test_class.setMaximumWidth(120)
        self.test_knob = QtWidgets.QLineEdit('file')
        self.test_knob.setToolTip('Knob name of the test node.')
        self.test_knob.setMaximumWidth(80)
        self.test_disabled = QtWidgets.QCheckBox('disabled')
        self.test_disabled.setToolTip('Test as a disabled node.')
        self.test_disconnected = QtWidgets.QCheckBox('disconnected')
        self.test_disconnected.setToolTip('Test as a disconnected node.')
        for w in (self.test_path, self.test_class, self.test_knob):
            w.textChanged.connect(self.run_test)
        for w in (self.test_disabled, self.test_disconnected):
            w.toggled.connect(self.run_test)
        self.test_result = label('')
        self.test_result.setWordWrap(True)
        test_box = QtWidgets.QGroupBox('Test')
        test_box.setLayout(vbox(
            hbox(label('File:'), self.test_path, label('Class:'), self.test_class, label('Knob:'), self.test_knob,
                 self.test_disabled, self.test_disconnected),
            self.test_result, margins=6))

        right = QtWidgets.QWidget()
        right.setLayout(vbox(path_box, opt_box, filt_box, test_box))
        self.editor = right
        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(1, 1)
        split.setSizes([180, 800])
        self.setLayout(vbox(
            hint('Categories decide where media files go in the package. A file joins every category whose '
                 'filters match (or only the first, see Farm & Misc). Files matching no category are not '
                 'packed and keep their original path.'),
            split))

    # ------------------------------------------------------------------ data helpers
    def cats(self) -> Dict[str, Any]:
        return self.state.settings.setdefault('categories', {})

    def current(self) -> str:
        it = self.list.currentItem()
        return it.text() if it else ''

    def cat(self) -> Optional[Dict[str, Any]]:
        return self.cats().get(self.current())

    def _set_cats(self, items: List) -> None:
        self.state.settings['categories'] = dict(items)

    def reload(self) -> None:
        cur = self.current()
        names = list(self.cats().keys())
        self.list.blockSignals(True)
        self.list.clear()
        self.list.addItems(names)
        self.list.blockSignals(False)
        if names:
            self.list.setCurrentRow(names.index(cur) if cur in names else 0)
        self._load_category()

    def _after_change(self, select: str) -> None:
        names = list(self.cats().keys())
        self.list.blockSignals(True)
        self.list.clear()
        self.list.addItems(names)
        self.list.blockSignals(False)
        if names:
            self.list.setCurrentRow(names.index(select) if select in names else 0)
        self._load_category()
        self.commit()

    def _ask(self, title: str, text: str = '') -> str:
        name, ok = QtWidgets.QInputDialog.getText(self, title, 'Category name:', text=text)
        name = (name or '').strip()
        if not ok or not name:
            return ''
        if name in self.cats():
            QtWidgets.QMessageBox.warning(self, title, 'Category "{}" already exists.'.format(name))
            return ''
        return name

    def add(self) -> None:
        name = self._ask('Add category')
        if name:
            self.cats()[name] = copy.deepcopy(settings_mod.DEFAULT_CATEGORY)
            self._after_change(name)

    def duplicate(self) -> None:
        cat = self.cat()
        if cat is None:
            return
        name = self._ask('Duplicate category', self.current() + '_copy')
        if name:
            self.cats()[name] = copy.deepcopy(cat)
            self._after_change(name)

    def rename(self) -> None:
        old = self.current()
        if not old:
            return
        new = self._ask('Rename category', old)
        if new:
            self._set_cats([(new if k == old else k, v) for k, v in self.cats().items()])
            self._after_change(new)

    def delete(self) -> None:
        name = self.current()
        if not name:
            return
        if QtWidgets.QMessageBox.question(self, 'Delete category', 'Delete category "{}"?'.format(name)) \
                != QtWidgets.QMessageBox.Yes:
            return
        del self.cats()[name]
        self._after_change('')

    def move(self, delta: int) -> None:
        items = list(self.cats().items())
        i = self.list.currentRow()
        j = i + delta
        if i < 0 or not (0 <= j < len(items)):
            return
        items[i], items[j] = items[j], items[i]
        self._set_cats(items)
        self._after_change(items[j][0])

    # ------------------------------------------------------------------ editor
    def _load_category(self) -> None:
        cat = self.cat()
        self.editor.setEnabled(cat is not None)
        self._loading = True
        try:
            cat = templates.deep_merge(settings_mod.DEFAULT_CATEGORY, cat or {})
            p = cat.get('path') or {}
            for key, e in self.fields.items():
                e.setText(str(p.get(key, '') or ''))
            opts = cat.get('filter_options') or {}
            self.skip_disconnected.setChecked(bool(opts.get('skip_disconnected')))
            self.skip_disabled.setChecked(bool(opts.get('skip_disabled')))
            self.combine.setCurrentText(str(opts.get('combine_filters', 'AND')).upper())
            self.filters.setRowCount(0)
            for flt in cat.get('filters') or []:
                self._append_filter(flt)
        finally:
            self._loading = False
        self.run_test()

    def _append_filter(self, flt: Dict[str, Any]) -> None:
        r = self.filters.rowCount()
        self.filters.insertRow(r)
        combo = QtWidgets.QComboBox()
        combo.addItems(list(filters.SOURCES))
        combo.setCurrentText(filters.canonical_source(flt.get('source', filters.SOURCE_FILE_NAME)))
        combo.currentTextChanged.connect(self._edited)
        self.filters.setCellWidget(r, 0, combo)
        self.filters.setItem(r, 1, QtWidgets.QTableWidgetItem(str(flt.get('search', ''))))
        self.filters.setItem(r, 2, QtWidgets.QTableWidgetItem(', '.join(str(c) for c in (flt.get('check') or []))))
        self.filters.setItem(r, 3, QtWidgets.QTableWidgetItem(str(flt.get('token_name', '') or '')))
        inv = QtWidgets.QTableWidgetItem()
        inv.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable)
        inv.setCheckState(QtCore.Qt.Checked if flt.get('invert') else QtCore.Qt.Unchecked)
        self.filters.setItem(r, 4, inv)
        test = QtWidgets.QTableWidgetItem('')
        test.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        self.filters.setItem(r, 5, test)

    def _filter_rows(self) -> List[Dict[str, Any]]:
        out = []
        for r in range(self.filters.rowCount()):
            def txt(c):
                it = self.filters.item(r, c)
                return it.text() if it else ''
            combo = self.filters.cellWidget(r, 0)
            inv = self.filters.item(r, 4)
            out.append({
                'source': combo.currentText() if combo else filters.SOURCE_FILE_NAME,
                'search': txt(1),
                'check': [c.strip() for c in txt(2).split(',') if c.strip()],
                'token_name': txt(3).strip(),
                'invert': bool(inv and inv.checkState() == QtCore.Qt.Checked),
            })
        return out

    def _edited(self, *_args) -> None:
        if self._loading:
            return
        cat = self.cat()
        if cat is None:
            return
        cat['path'] = dict(cat.get('path') or {}, **{k: e.text() for k, e in self.fields.items()})
        cat['filter_options'] = dict(cat.get('filter_options') or {}, skip_disconnected=self.skip_disconnected.isChecked(),
                                     skip_disabled=self.skip_disabled.isChecked(),
                                     combine_filters=self.combine.currentText())
        cat['filters'] = self._filter_rows()
        self.run_test()
        self.commit()

    def add_filter(self) -> None:
        self._loading = True
        self._append_filter({'source': filters.SOURCE_FILE_NAME, 'search': r'\.(\w+)$', 'token_name': 'extension'})
        self._loading = False
        self._edited()

    def remove_filters(self) -> None:
        rows = sorted({i.row() for i in self.filters.selectedIndexes()}, reverse=True)
        if not rows:
            return
        self._loading = True
        for r in rows:
            self.filters.removeRow(r)
        self._loading = False
        self._edited()

    def move_filter(self, delta: int) -> None:
        cat = self.cat()
        r = self.filters.currentRow()
        rows = self._filter_rows()
        n = r + delta
        if cat is None or r < 0 or not (0 <= n < len(rows)):
            return
        rows[r], rows[n] = rows[n], rows[r]
        cat['filters'] = rows
        self._load_category()
        self.filters.setCurrentCell(n, 1)
        self.commit()

    # ------------------------------------------------------------------ test + preview
    def run_test(self, *_args) -> None:
        cat = self.cat()
        path = paths.norm(self.test_path.text().strip())
        name = paths.basename(path)
        node_class = self.test_class.text().strip() or 'Read'
        knob = self.test_knob.text().strip() or 'file'
        subject = {'File Name': name, 'File Path': path, 'Node Class': node_class, 'Knob Name': knob}
        extra = {'category': self.current() or '<category>', 'node': 'Read1', 'node_class': node_class,
                 'knob': knob}
        if name:
            extra['clean_name'] = sequences.clean_name(name)
            extra['extension'] = os.path.splitext(name)[1].lstrip('.').lower()

        self._loading, was = True, self._loading
        try:
            rows = self._filter_rows()
            for r, flt in enumerate(rows):
                it = self.filters.item(r, 5)
                if it is None:
                    continue
                err = filters.regex_error(flt['search']) if flt['source'] != filters.SOURCE_NODE_CLASS and \
                    flt['search'] else None
                if err:
                    it.setText('invalid regex')
                    it.setToolTip(err)
                    it.setForeground(QtGui.QColor(MISSING))
                elif path:
                    res = filters.eval_filter(flt, subject)
                    it.setText('{}{}'.format('hit' if res.hit else 'no hit',
                                             ' = ' + res.value if res.value is not None else ''))
                    it.setToolTip(it.text())
                    it.setForeground(QtGui.QColor(OK if res.hit else MISSING))
                else:
                    it.setText('')
                    it.setToolTip('Enter a test file below.')
        finally:
            self._loading = was

        if cat is not None and path:
            ok, tokens, reason = filters.match_category(cat, subject, self.test_disabled.isChecked(),
                                                        self.test_disconnected.isChecked())
            extra.update(tokens)
            if ok:
                text = 'Matches category "{}"{}'.format(
                    self.current(), '; tokens: ' + ', '.join('{}={}'.format(k, v) for k, v in tokens.items())
                    if tokens else '')
            else:
                text = 'Does not match ({})'.format({'disabled': 'disabled node skipped',
                                                     'disconnected': 'disconnected node skipped',
                                                     'filters': 'filters'}.get(reason, reason))
            self.test_result.setText(text)
            self.test_result.setStyleSheet('color: {};'.format(OK if ok else MISSING))
        else:
            self.test_result.setText('Enter a file path to test this category.')
            self.test_result.setStyleSheet('')

        tok = preview_tokens(self.state, extra)
        f = {k: e.text() for k, e in self.fields.items()}
        file_name = name or '<file>'
        self.resolved['package'].show_template(
            templates.join_template(f['root_template'], f['top_folder']) + '/' + file_name, tok)
        self.resolved['relink'].show_template(
            templates.join_template(f['root_template_relink'], f['top_folder_relink']) + '/' + file_name, tok)

    def refresh_previews(self) -> None:
        self.run_test()
