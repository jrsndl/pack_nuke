"""Places tab: edit place anatomy and script path tags, copy/paste between places, and
preview every output path for a real script."""
from __future__ import annotations

import copy
import logging
import re
from typing import Any, Dict, List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import filters, preflight, settings as settings_mod, templates
from .state import AppState
from . import help as help_texts
from .widgets import Debouncer, button, clip_get, clip_put, hbox, hint, label, vbox

log = logging.getLogger('packnuke.gui')

TAG_COLUMNS = ['Name', 'Source', 'Search (regex)', 'Replace', 'Lower', 'Upper', 'Preview']
MISSING_COLOR = QtGui.QColor('#ff7f50')


def _text_to_value(text: str, original: Any) -> Any:
    """Keep non-string anatomy values (numbers, bools) typed when they still parse."""
    if isinstance(original, bool):
        low = text.strip().lower()
        if low in ('true', '1', 'yes'):
            return True
        if low in ('false', '0', 'no'):
            return False
    elif isinstance(original, int):
        try:
            return int(text)
        except ValueError:
            pass
    elif isinstance(original, float):
        try:
            return float(text)
        except ValueError:
            pass
    return text


class PlacesTab(QtWidgets.QWidget):
    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self._loading = False
        self._self_edit = False
        self._build()
        self._preview_later = Debouncer(self.refresh_preview, 250, self)
        state.settings_loaded.connect(self.reload)
        state.places_changed.connect(self._external_places_change)
        state.places_selected.connect(self._preview_later.trigger)
        state.preview_changed.connect(self._preview_later.trigger)
        state.settings_edited.connect(self._preview_later.trigger)
        state.timestamp_changed.connect(self._preview_later.trigger)

    # ------------------------------------------------------------------ UI
    def _build(self) -> None:
        self.place_list = QtWidgets.QListWidget()
        self.place_list.currentTextChanged.connect(self._place_selected)
        self.place_list.setToolTip('Places from settings.json. Double click to rename.')
        self.place_list.itemDoubleClicked.connect(lambda _i: self.rename_place())
        self.role_label = label('')
        self.role_label.setWordWrap(True)
        left = QtWidgets.QWidget()
        left.setLayout(vbox(
            label('Places'), self.place_list, self.role_label,
            hbox(button('Add', self.add_place), button('Duplicate', self.duplicate_place)),
            hbox(button('Rename', self.rename_place), button('Delete', self.delete_place)),
            button('Use as source', lambda: self._use_as('source')),
            button('Use as target', lambda: self._use_as('target'))))

        # anatomy
        self.anatomy = QtWidgets.QTableWidget(0, 2)
        self.anatomy.setHorizontalHeaderLabels(['Key (nested with dots)', 'Value'])
        self.anatomy.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        self.anatomy.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.anatomy.setColumnWidth(0, 200)
        self.anatomy.verticalHeader().setVisible(False)
        self.anatomy.verticalHeader().setDefaultSectionSize(22)
        self.anatomy.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.anatomy.itemChanged.connect(self._anatomy_edited)
        self._shortcuts(self.anatomy, self.copy_anatomy, self.paste_anatomy, self.remove_anatomy)
        self.copy_to_anatomy = self._copy_to_button(self.copy_anatomy_to)
        anatomy_page = QtWidgets.QWidget()
        anatomy_page.setLayout(vbox(
            hint('Tokens of this place, used in templates as {key} or nested {project[name]}. '
                 'Ctrl+C / Ctrl+V copy rows between places (also through the clipboard).'),
            self.anatomy,
            hbox(button('Add row', self.add_anatomy), button('Remove rows', self.remove_anatomy), 8,
                 button('Copy rows', self.copy_anatomy), button('Paste rows', self.paste_anatomy),
                 self.copy_to_anatomy, None), margins=4))

        # script path tags
        self.use_tags = QtWidgets.QCheckBox('Use script path tags for this place')
        self.use_tags.toggled.connect(self._tags_edited)
        self.tags = QtWidgets.QTableWidget(0, len(TAG_COLUMNS))
        self.tags.setHorizontalHeaderLabels(TAG_COLUMNS)
        self.tags.verticalHeader().setVisible(False)
        self.tags.verticalHeader().setDefaultSectionSize(24)
        self.tags.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        hdr = self.tags.horizontalHeader()
        hdr.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        for c, w in ((0, 90), (1, 90), (3, 80), (4, 50), (5, 50), (6, 140)):
            self.tags.setColumnWidth(c, w)
        self.tags.itemChanged.connect(self._tags_edited)
        self._shortcuts(self.tags, self.copy_tags, self.paste_tags, self.remove_tags)
        self.copy_to_tags = self._copy_to_button(self.copy_tags_to)
        tags_page = QtWidgets.QWidget()
        tags_page.setLayout(vbox(
            hint('Tags parsed from each Nuke script path ({SHOT}, {TASK} ...). "Replace" uses group '
                 'references like \\1. The Preview column shows the result for the preview script.'),
            self.use_tags, self.tags,
            hbox(button('Add tag', self.add_tag), button('Remove', self.remove_tags), 8,
                 button('Up', lambda: self.move_tag(-1)), button('Down', lambda: self.move_tag(1)), 8,
                 button('Copy tags', self.copy_tags), button('Paste tags', self.paste_tags),
                 self.copy_to_tags, None), margins=4))

        self.editor_tabs = QtWidgets.QTabWidget()
        self.editor_tabs.addTab(anatomy_page, 'Anatomy')
        self.editor_tabs.addTab(tags_page, 'Script path tags')

        # preview
        self.preview_title = label('')
        self.preview_places = label('')
        for lbl in (self.preview_title, self.preview_places):
            lbl.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
            lbl.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
            lbl.setMinimumHeight(lbl.fontMetrics().height() + 6)
        self.preview = QtWidgets.QTreeWidget()
        self.preview.setColumnCount(3)
        self.preview.setHeaderLabels(['Output', 'Resolved', 'Template'])
        self.preview.setColumnWidth(0, 190)
        self.preview.setColumnWidth(1, 420)
        self.preview.setAlternatingRowColors(True)
        self.preview.setUniformRowHeights(True)
        preview_box = QtWidgets.QGroupBox('Output path preview')
        preview_box.setLayout(vbox(
            self.preview_title, self.preview_places,
            hint('Uses the current source/target places (Queue tab). Farm-only tokens such as {node} '
                 'or {category} are shown as <node>. Missing tokens are highlighted.'),
            self.preview, hbox(None, button('Refresh', self.refresh_preview)), margins=6))

        top = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        top.addWidget(left)
        top.addWidget(self.editor_tabs)
        top.setStretchFactor(1, 1)
        top.setSizes([200, 800])
        help_texts.apply([
            (self.place_list, 'Places'), (self.anatomy, 'anatomy_table'), (self.tags, 'tags_table'),
            (self.use_tags, 'Use script path tags for this place'), (self.preview, 'preview_tree'),
            (self.role_label, 'Whether this place is the current source or target (Queue tab)')])
        main = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        main.addWidget(top)
        main.addWidget(preview_box)
        main.setStretchFactor(0, 1)
        main.setStretchFactor(1, 1)
        self.setLayout(vbox(main, margins=6))

    def _shortcuts(self, table, copy_fn, paste_fn, delete_fn) -> None:
        for seq, fn in ((QtGui.QKeySequence.Copy, copy_fn), (QtGui.QKeySequence.Paste, paste_fn),
                        (QtGui.QKeySequence.Delete, delete_fn)):
            sc = QtGui.QShortcut(seq, table)
            sc.setContext(QtCore.Qt.WidgetWithChildrenShortcut)
            sc.activated.connect(fn)

    def _copy_to_button(self, fn) -> QtWidgets.QPushButton:
        b = QtWidgets.QPushButton('Copy to place ▾')
        b.setToolTip('Copy the selected rows (or all rows if none selected) into another place')
        menu = QtWidgets.QMenu(b)
        menu.aboutToShow.connect(lambda: self._fill_copy_menu(menu, fn))
        b.setMenu(menu)
        return b

    def _fill_copy_menu(self, menu: QtWidgets.QMenu, fn) -> None:
        menu.clear()
        cur = self.current_name()
        others = [n for n in self.state.place_names() if n != cur]
        for name in others:
            menu.addAction(name, lambda _c=False, n=name: fn([n]))
        if len(others) > 1:
            menu.addSeparator()
            menu.addAction('All other places', lambda _c=False: fn(others))
        if not others:
            menu.addAction('(no other place)').setEnabled(False)

    # ------------------------------------------------------------------ helpers
    def current_name(self) -> str:
        item = self.place_list.currentItem()
        return item.text() if item else ''

    def current_place(self) -> Optional[Dict[str, Any]]:
        return (self.state.settings.get('places') or {}).get(self.current_name())

    def _commit(self) -> None:
        self._self_edit = True
        try:
            self.state.edited(places=True)
        finally:
            self._self_edit = False
        self._preview_later.trigger()

    def _external_places_change(self) -> None:
        if not self._self_edit:
            self.reload()
        self._preview_later.trigger()

    # ------------------------------------------------------------------ place list
    def reload(self) -> None:
        cur = self.current_name()
        names = self.state.place_names()
        self.place_list.blockSignals(True)
        self.place_list.clear()
        self.place_list.addItems(names)
        self.place_list.blockSignals(False)
        if names:
            self.place_list.setCurrentRow(names.index(cur) if cur in names else 0)
        self._place_selected(self.current_name())
        self._preview_later.trigger()

    def _place_selected(self, _name: str) -> None:
        self._load_editors()
        self._update_role()

    def _update_role(self) -> None:
        name = self.current_name()
        roles = []
        if name and name == self.state.place_source:
            roles.append('source')
        if name and name == self.state.place_target:
            roles.append('target')
        self.role_label.setText('Current {}'.format(' and '.join(roles)) if roles else '')

    def _use_as(self, role: str) -> None:
        name = self.current_name()
        if not name:
            return
        src, tgt = self.state.place_source, self.state.place_target
        if role == 'source':
            src, tgt = name, (src if tgt == name else tgt)
        else:
            tgt, src = name, (tgt if src == name else src)
        self.state.set_places(src, tgt)
        self._update_role()

    def _ask_name(self, title: str, text: str = '') -> str:
        name, ok = QtWidgets.QInputDialog.getText(self, title, 'Place name:', text=text)
        name = (name or '').strip()
        if not ok or not name:
            return ''
        if name in self.state.place_names():
            QtWidgets.QMessageBox.warning(self, title, 'A place named "{}" already exists.'.format(name))
            return ''
        return name

    def add_place(self) -> None:
        name = self._ask_name('Add place')
        if name:
            self.state.settings['places'][name] = copy.deepcopy(settings_mod.DEFAULT_PLACE)
            self._after_list_change(name)

    def duplicate_place(self) -> None:
        cur = self.current_place()
        if cur is None:
            return
        name = self._ask_name('Duplicate place', self.current_name() + '_copy')
        if name:
            self.state.settings['places'][name] = copy.deepcopy(cur)
            self._after_list_change(name)

    def rename_place(self) -> None:
        old = self.current_name()
        if not old:
            return
        new = self._ask_name('Rename place', old)
        if new:
            self.state.rename_place(old, new)
            self._after_list_change(new, commit=False)

    def delete_place(self) -> None:
        name = self.current_name()
        if not name:
            return
        if QtWidgets.QMessageBox.question(self, 'Delete place', 'Delete place "{}"?'.format(name)) \
                != QtWidgets.QMessageBox.Yes:
            return
        del self.state.settings['places'][name]
        self.state._fix_places()
        self._after_list_change('')

    def _after_list_change(self, select: str, commit: bool = True) -> None:
        names = self.state.place_names()
        self.place_list.blockSignals(True)
        self.place_list.clear()
        self.place_list.addItems(names)
        self.place_list.blockSignals(False)
        if names:
            self.place_list.setCurrentRow(names.index(select) if select in names else 0)
        self._load_editors()
        self.state._fix_places()
        if commit:
            self._commit()
        self.state.places_selected.emit()
        self._update_role()

    # ------------------------------------------------------------------ editors
    def _load_editors(self) -> None:
        place = self.current_place() or {}
        self._loading = True
        try:
            self._anatomy_original = dict(templates.flatten(place.get('anatomy') or {}))
            pairs = templates.flatten(place.get('anatomy') or {})
            self.anatomy.setRowCount(0)
            for k, v in pairs:
                self._append_anatomy_row(k, v)
            self.use_tags.setChecked(bool(place.get('use_script_path_tags')))
            self.tags.setRowCount(0)
            for tag in place.get('script_path_tags') or []:
                self._append_tag_row(tag)
        finally:
            self._loading = False
        enabled = bool(self.current_name())
        self.editor_tabs.setEnabled(enabled)
        self._update_tag_previews()

    # anatomy
    def _append_anatomy_row(self, key: str, value: Any) -> None:
        r = self.anatomy.rowCount()
        self.anatomy.insertRow(r)
        self.anatomy.setItem(r, 0, QtWidgets.QTableWidgetItem(str(key)))
        if isinstance(value, dict):
            value = ''
        self.anatomy.setItem(r, 1, QtWidgets.QTableWidgetItem('' if value is None else str(value)))

    def _anatomy_rows(self, selected_only: bool = False) -> List[List[str]]:
        rows = range(self.anatomy.rowCount())
        if selected_only:
            sel = sorted({i.row() for i in self.anatomy.selectedIndexes()})
            rows = sel or rows
        out = []
        for r in rows:
            k = self.anatomy.item(r, 0)
            v = self.anatomy.item(r, 1)
            key = k.text().strip() if k else ''
            if key:
                out.append([key, v.text() if v else ''])
        return out

    def _anatomy_edited(self, *_args) -> None:
        if self._loading:
            return
        place = self.current_place()
        if place is None:
            return
        orig = getattr(self, '_anatomy_original', {})
        pairs = [(k, _text_to_value(v, orig.get(k))) for k, v in self._anatomy_rows()]
        place['anatomy'] = templates.unflatten(pairs)
        self._anatomy_original = dict(templates.flatten(place['anatomy']))
        self._commit()

    def add_anatomy(self) -> None:
        self._loading = True
        self._append_anatomy_row('new_key', '')
        self._loading = False
        r = self.anatomy.rowCount() - 1
        self.anatomy.setCurrentCell(r, 0)
        self.anatomy.editItem(self.anatomy.item(r, 0))

    def remove_anatomy(self) -> None:
        rows = sorted({i.row() for i in self.anatomy.selectedIndexes()}, reverse=True)
        if not rows:
            return
        self._loading = True
        for r in rows:
            self.anatomy.removeRow(r)
        self._loading = False
        self._anatomy_edited()

    def copy_anatomy(self) -> None:
        rows = self._anatomy_rows(selected_only=True)
        clip_put('anatomy', rows)
        log.info('Copied %d anatomy row(s) from place %s', len(rows), self.current_name())

    def _merge_anatomy(self, place: Dict[str, Any], rows: List[List[str]]) -> None:
        pairs = dict(templates.flatten(place.get('anatomy') or {}))
        for k, v in rows:
            pairs[k] = v
        place['anatomy'] = templates.unflatten(pairs.items())

    def paste_anatomy(self) -> None:
        rows = clip_get('anatomy')
        place = self.current_place()
        if not rows or place is None:
            log.warning('Clipboard does not contain anatomy rows.')
            return
        self._merge_anatomy(place, rows)
        self._load_editors()
        self._commit()
        log.info('Pasted %d anatomy row(s) into place %s', len(rows), self.current_name())

    def copy_anatomy_to(self, names: List[str]) -> None:
        rows = self._anatomy_rows(selected_only=True)
        for n in names:
            self._merge_anatomy(self.state.settings['places'][n], rows)
        self._commit()
        log.info('Copied %d anatomy row(s) from %s to %s', len(rows), self.current_name(), ', '.join(names))

    # tags
    def _append_tag_row(self, tag: Dict[str, Any]) -> None:
        tag = templates.deep_merge(settings_mod.DEFAULT_PATH_TAG, tag)
        r = self.tags.rowCount()
        self.tags.insertRow(r)
        self.tags.setItem(r, 0, QtWidgets.QTableWidgetItem(str(tag.get('name', ''))))
        combo = QtWidgets.QComboBox()
        combo.addItems([filters.SOURCE_FILE_NAME, filters.SOURCE_FILE_PATH])
        combo.setCurrentText(filters.canonical_source(tag.get('source', filters.SOURCE_FILE_NAME)))
        combo.currentTextChanged.connect(self._tags_edited)
        self.tags.setCellWidget(r, 1, combo)
        self.tags.setItem(r, 2, QtWidgets.QTableWidgetItem(str(tag.get('search', ''))))
        self.tags.setItem(r, 3, QtWidgets.QTableWidgetItem(str(tag.get('replace', ''))))
        for c, key in ((4, 'lowercase'), (5, 'uppercase')):
            it = QtWidgets.QTableWidgetItem()
            it.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable)
            it.setCheckState(QtCore.Qt.Checked if tag.get(key) else QtCore.Qt.Unchecked)
            self.tags.setItem(r, c, it)
        prev = QtWidgets.QTableWidgetItem('')
        prev.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        self.tags.setItem(r, 6, prev)

    def _tag_rows(self, selected_only: bool = False) -> List[Dict[str, Any]]:
        rows = range(self.tags.rowCount())
        if selected_only:
            sel = sorted({i.row() for i in self.tags.selectedIndexes()})
            rows = sel or rows
        out = []
        for r in rows:
            def txt(c):
                it = self.tags.item(r, c)
                return it.text() if it else ''

            def chk(c):
                it = self.tags.item(r, c)
                return bool(it and it.checkState() == QtCore.Qt.Checked)
            combo = self.tags.cellWidget(r, 1)
            out.append({
                'name': txt(0).strip(),
                'source': combo.currentText() if combo else filters.SOURCE_FILE_NAME,
                'search': txt(2),
                'replace': txt(3),
                'lowercase': chk(4),
                'uppercase': chk(5),
            })
        return out

    def _tags_edited(self, *_args) -> None:
        if self._loading:
            return
        place = self.current_place()
        if place is None:
            return
        place['use_script_path_tags'] = self.use_tags.isChecked()
        place['script_path_tags'] = self._tag_rows()
        self._update_tag_previews()
        self._commit()

    def _update_tag_previews(self) -> None:
        script = self.state.preview_script()
        self._loading, was = True, self._loading
        try:
            for r, tag in enumerate(self._tag_rows()):
                it = self.tags.item(r, 6)
                if it is None:
                    continue
                err = filters.regex_error(tag['search']) if tag['search'] else None
                if err:
                    it.setText('invalid regex')
                    it.setToolTip(err)
                    it.setForeground(MISSING_COLOR)
                elif script:
                    v = filters.eval_path_tag(tag, script)
                    warns = []
                    replace = tag['replace'] or ''
                    if re.search(r'(?<!\\)/\d', replace) and '\\' not in replace:
                        warns.append('Replace "{}" is literal text - did you mean "\\{}"?'.format(
                            replace, replace.lstrip('/')[:1]))
                    if re.search(r'\{\d+-\d+\}', tag['search'] or ''):
                        warns.append('"{a-b}" in the regex is literal text, a quantifier is written "{a,b}".')
                    if not self.use_tags.isChecked():
                        warns.append('Script path tags are switched off for this place.')
                    text = 'no match' if v is None else v
                    it.setText(('⚠ ' if warns else '') + text)
                    it.setToolTip('\n'.join([text] + warns + ['', 'Script: ' + script]))
                    it.setForeground(MISSING_COLOR if (v is None or warns) else QtGui.QColor('#b1b1b1'))
                else:
                    it.setText('')
                    it.setToolTip('No preview script (add one to the Queue or select one in Get Nuke Scripts)')
        finally:
            self._loading = was

    def add_tag(self) -> None:
        self._loading = True
        self._append_tag_row(dict(settings_mod.DEFAULT_PATH_TAG))
        self._loading = False
        self._tags_edited()
        r = self.tags.rowCount() - 1
        self.tags.setCurrentCell(r, 0)
        self.tags.editItem(self.tags.item(r, 0))

    def remove_tags(self) -> None:
        rows = sorted({i.row() for i in self.tags.selectedIndexes()}, reverse=True)
        if not rows:
            return
        self._loading = True
        for r in rows:
            self.tags.removeRow(r)
        self._loading = False
        self._tags_edited()

    def move_tag(self, delta: int) -> None:
        r = self.tags.currentRow()
        tags = self._tag_rows()
        n = r + delta
        if r < 0 or not (0 <= n < len(tags)):
            return
        tags[r], tags[n] = tags[n], tags[r]
        place = self.current_place()
        place['script_path_tags'] = tags
        self._load_editors()
        self.tags.setCurrentCell(n, 0)
        self._commit()

    def copy_tags(self) -> None:
        rows = self._tag_rows(selected_only=True)
        clip_put('script_path_tags', rows)
        log.info('Copied %d tag(s) from place %s', len(rows), self.current_name())

    @staticmethod
    def _merge_tags(place: Dict[str, Any], rows: List[Dict[str, Any]]) -> None:
        tags = list(place.get('script_path_tags') or [])
        by_name = {t.get('name'): i for i, t in enumerate(tags)}
        for row in rows:
            if row.get('name') in by_name:
                tags[by_name[row['name']]] = dict(row)
            else:
                tags.append(dict(row))
        place['script_path_tags'] = tags

    def paste_tags(self) -> None:
        rows = clip_get('script_path_tags')
        place = self.current_place()
        if not rows or place is None:
            log.warning('Clipboard does not contain script path tags.')
            return
        self._merge_tags(place, rows)
        self._load_editors()
        self._commit()
        log.info('Pasted %d tag(s) into place %s (same names replaced)', len(rows), self.current_name())

    def copy_tags_to(self, names: List[str]) -> None:
        rows = self._tag_rows(selected_only=True)
        for n in names:
            self._merge_tags(self.state.settings['places'][n], rows)
        self._commit()
        log.info('Copied %d tag(s) from %s to %s', len(rows), self.current_name(), ', '.join(names))

    # ------------------------------------------------------------------ preview
    def refresh_preview(self) -> None:
        self._update_tag_previews()
        self._update_role()
        st = self.state
        script = st.preview_script()
        self.preview.clear()
        self.preview_places.setText('Places: {} → {}'.format(st.place_source or '?', st.place_target or '?'))
        if not script:
            self.preview_title.setText('No preview script. Add scripts to the Queue, or select one in '
                                       'Get Nuke Scripts.')
            self.preview_title.setToolTip('')
            return
        self.preview_title.setText('Preview for: {}'.format(script))
        self.preview_title.setToolTip(script)
        tok = st.script_tokens(script)

        def add(parent, name, resolved, tpl='', missing=()):
            it = QtWidgets.QTreeWidgetItem(parent, [name, resolved, tpl])
            it.setToolTip(1, resolved)
            it.setToolTip(2, tpl)
            if missing:
                for c in range(3):
                    it.setForeground(c, MISSING_COLOR)
                it.setToolTip(1, 'missing tokens: ' + ', '.join(missing))
            return it

        job = QtWidgets.QTreeWidgetItem(self.preview, ['Job'])
        jr_tpl = st.settings['job'].get('job_root', '')
        jn_tpl = st.settings['job'].get('job_name_default', '')
        base = st.base_tokens()
        add(job, 'Job root', templates.format_template(jr_tpl, base, strict=False), jr_tpl,
            templates.missing_tokens(jr_tpl, base))
        add(job, 'Job name', templates.format_template(jn_tpl, base, strict=False), jn_tpl,
            templates.missing_tokens(jn_tpl, base))
        add(job, 'Job folder ({job})', tok.get('job', ''))

        outs = QtWidgets.QTreeWidgetItem(self.preview, ['Paths'])
        for label_text, tpl, resolved, missing in preflight.preview_paths(st.settings, tok):
            add(outs, label_text, resolved, tpl, missing)

        tags = st.script_tags(script)
        toks = QtWidgets.QTreeWidgetItem(self.preview, ['Tokens'])
        for k, v in sorted(templates.flatten(tok), key=lambda kv: (kv[0] not in tags, kv[0].lower())):
            it = add(toks, k, '' if v is None else str(v))
            if k in tags:
                f = it.font(0)
                f.setBold(True)
                it.setFont(0, f)
        for top in (job, outs):
            top.setExpanded(True)
        toks.setExpanded(False)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh_preview()
