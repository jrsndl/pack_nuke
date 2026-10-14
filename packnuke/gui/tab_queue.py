"""Queue tab: scripts to pack, token inspector, job settings and Deadline submission."""
from __future__ import annotations

import logging
import os
import re
from typing import List, Optional

from PySide6 import QtCore, QtGui, QtWidgets

from ..core import jobs, paths, preflight, settings as settings_mod, templates, tokens as tokens_mod
from ..farm import deadline
from .script_models import QueueModel, SortProxy
from .state import AppState
from .widgets import (KeyValueTable, PathEdit, button, configure_table, first_selected_row, hbox, label,
                      reveal, selected_rows, set_status_label, vbox)
from .workers import SubmitWorker

log = logging.getLogger('packnuke.gui')


class QueueTab(QtWidgets.QWidget):
    status = QtCore.Signal(str)
    busy = QtCore.Signal(bool)
    selection_changed = QtCore.Signal()

    def __init__(self, state: AppState, parent=None):
        super().__init__(parent)
        self.state = state
        self.submit_worker: Optional[SubmitWorker] = None
        self.local_process: Optional[QtCore.QProcess] = None
        self._job_root_auto = True
        self._job_name_auto = True
        self._build()
        state.queue_changed.connect(self.model.refresh)
        state.places_changed.connect(self._places_changed)
        state.settings_loaded.connect(self._places_changed)
        state.places_selected.connect(self._sync_place_combos)
        state.timestamp_changed.connect(self._refresh_job_fields)

    # ------------------------------------------------------------------ UI
    def _build(self) -> None:
        self.model = QueueModel(self.state, lambda p: tokens_mod.tags_summary(self.state.script_tags(p)), self)
        self.proxy = SortProxy(self)
        self.proxy.setSourceModel(self.model)
        self.table = QtWidgets.QTableView()
        self.table.setModel(self.proxy)
        configure_table(self.table, stretch_col=4)
        self.table.setColumnWidth(0, 28)
        self.table.setColumnWidth(1, 300)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 300)
        self.table.selectionModel().selectionChanged.connect(self._selection)
        self.model.modelReset.connect(self._selection)
        self.model.marks_changed.connect(self._update_counts)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        self.table.doubleClicked.connect(self._double_clicked)
        space = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key_Space), self.table)
        space.setContext(QtCore.Qt.WidgetShortcut)
        space.activated.connect(lambda: self.mark_selected(None))
        delete = QtGui.QShortcut(QtGui.QKeySequence.Delete, self.table)
        delete.setContext(QtCore.Qt.WidgetShortcut)
        delete.activated.connect(self.remove_selected)

        self.counts = label('')
        self.inspector_btn = QtWidgets.QPushButton('Inspector')
        self.inspector_btn.setCheckable(True)
        self.inspector_btn.setChecked(True)
        self.inspector_btn.setToolTip('Show / hide the token inspector (drag the splitter to resize)')
        self.inspector_btn.toggled.connect(self._toggle_inspector)
        row_actions = hbox(
            button('Mark all', lambda: self.model.set_marks(None, True)),
            button('Mark none', lambda: self.model.set_marks(None, False)),
            8,
            button('Mark selected', lambda: self.mark_selected(True)),
            button('Unmark selected', lambda: self.mark_selected(False)),
            8,
            button('Remove selected', self.remove_selected, 'Del'),
            button('Clear queue', self.clear_queue),
            None, self.counts, 8, self.inspector_btn)

        # inspector
        self.insp_title = label('')
        self.insp_title.setWordWrap(True)
        self.insp_table = KeyValueTable()
        self.insp_only_tags = QtWidgets.QCheckBox('Script path tags only')
        self.insp_only_tags.toggled.connect(self._selection)
        insp = QtWidgets.QGroupBox('Tokens of the selected script')
        insp.setLayout(vbox(self.insp_title, self.insp_only_tags, self.insp_table, margins=6))
        self.inspector = insp

        left = QtWidgets.QWidget()
        left.setLayout(vbox(self.table, row_actions))
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(left)
        self.splitter.addWidget(insp)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setCollapsible(0, False)
        self.splitter.splitterMoved.connect(self._splitter_moved)

        # job
        self.place_source = QtWidgets.QComboBox()
        self.place_target = QtWidgets.QComboBox()
        self.place_source.currentTextChanged.connect(self._place_combo_changed)
        self.place_target.currentTextChanged.connect(self._place_combo_changed)
        self.places_state = label('')
        self.job_root = PathEdit('dir')
        self.job_root.changed.connect(self._job_root_edited)
        self.job_name = QtWidgets.QLineEdit()
        self.job_name.textEdited.connect(self._job_name_edited)
        self.job_name.textChanged.connect(self._validate_name)
        self.job_name_state = label('')
        self.job_folder_label = label('')
        self.job_folder_label.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        grid = QtWidgets.QGridLayout()
        grid.setColumnStretch(1, 1)
        grid.addWidget(label('Source place:'), 0, 0)
        grid.addLayout(hbox(self.place_source, label('→  Target place:'), self.place_target,
                            button('⇄', self.swap_places, 'Swap source and target'), self.places_state, None),
                       0, 1)
        grid.addWidget(label('Job root:'), 1, 0)
        grid.addLayout(hbox(self.job_root, button('Auto', self.reset_job_root, 'Use settings job.job_root')), 1, 1)
        grid.addWidget(label('Job name:'), 2, 0)
        grid.addLayout(hbox(self.job_name, self.job_name_state,
                            button('Auto', self.reset_job_name, 'Use settings job.job_name_default'),
                            button('New timestamp', self.state.refresh_timestamp)), 2, 1)
        grid.addWidget(label('Job folder:'), 3, 0)
        grid.addWidget(self.job_folder_label, 3, 1)

        self.check_btn = button('Check', self.check, 'Validate settings, places and templates for every marked script')
        self.write_btn = button('Write job files only', self.write_only,
                                'Create the package folder with settings.json, job.json and nuke_files.csv')
        self.local_btn = button('Run first locally', self.run_local,
                                'Write the job files and pack the first marked script on this machine with nuke -t')
        self.submit_btn = button('Send to Deadline', self.submit, object_name='primary')
        job_box = QtWidgets.QGroupBox('Package')
        job_box.setLayout(vbox(grid, hbox(None, self.check_btn, self.write_btn, self.local_btn, self.submit_btn),
                               margins=6))

        self.setLayout(vbox(self.splitter, job_box, margins=6))

    # ------------------------------------------------------------------ places / job fields
    def _places_changed(self) -> None:
        self._sync_place_combos()
        self.model.refresh_tokens()
        self._refresh_job_fields()
        self._selection()

    def _sync_place_combos(self) -> None:
        names = self.state.place_names()
        for combo, value in ((self.place_source, self.state.place_source), (self.place_target, self.state.place_target)):
            combo.blockSignals(True)
            if [combo.itemText(i) for i in range(combo.count())] != names:
                combo.clear()
                combo.addItems(names)
            combo.setCurrentText(value)
            combo.blockSignals(False)
        same = self.state.place_source == self.state.place_target
        set_status_label(self.places_state, not same and len(names) >= 2,
                         'source and target must differ' if same else ('' if len(names) >= 2 else 'need 2 places'))
        self.model.refresh_tokens()
        self._refresh_job_fields()
        self._selection()

    def _place_combo_changed(self, *_args) -> None:
        self.state.set_places(self.place_source.currentText(), self.place_target.currentText())

    def swap_places(self) -> None:
        self.state.set_places(self.state.place_target, self.state.place_source)

    def _refresh_job_fields(self) -> None:
        if self._job_root_auto:
            self.job_root.edit.blockSignals(True)
            self.job_root.setText(self.state.auto_job_root())
            self.job_root.edit.blockSignals(False)
        if self._job_name_auto:
            self.job_name.setText(self.state.auto_job_name())
        self._update_job_folder()

    def _job_root_edited(self, _text: str) -> None:
        self._job_root_auto = False
        self._update_job_folder()

    def _job_name_edited(self, _text: str) -> None:
        self._job_name_auto = False
        self._update_job_folder()

    def reset_job_root(self) -> None:
        self._job_root_auto = True
        self._refresh_job_fields()

    def reset_job_name(self) -> None:
        self._job_name_auto = True
        self._refresh_job_fields()

    def job_folder(self) -> str:
        return templates.join_template(paths.norm(self.job_root.text()), self.job_name.text().strip())

    def _update_job_folder(self) -> None:
        self.job_folder_label.setText(self.job_folder())
        self._selection()

    def _validate_name(self) -> bool:
        rx = self.state.settings['job'].get('job_name_check') or ''
        name = self.job_name.text().strip()
        if not name:
            set_status_label(self.job_name_state, False, 'empty')
            return False
        if '{' in name:
            set_status_label(self.job_name_state, False, 'unresolved token')
            return False
        if rx:
            try:
                ok = re.match(rx, name) is not None
            except re.error:
                ok = False
            set_status_label(self.job_name_state, ok, 'matches convention' if ok else "doesn't match job_name_check")
            return ok
        set_status_label(self.job_name_state, True, '')
        return True

    def get_state(self) -> dict:
        return {'place_source': self.state.place_source, 'place_target': self.state.place_target,
                'inspector': self.inspector_btn.isChecked()}

    def set_state(self, s: dict) -> None:
        src, tgt = s.get('place_source'), s.get('place_target')
        names = self.state.place_names()
        if src in names and tgt in names:
            self.state.set_places(src, tgt)
        if 'inspector' in s:
            from .state import to_bool
            self.inspector_btn.setChecked(to_bool(s['inspector'], True))

    # ------------------------------------------------------------------ table
    def _update_counts(self) -> None:
        marked = sum(1 for q in self.state.queue if q.marked)
        self.counts.setText('{} in queue, {} marked'.format(len(self.state.queue), marked))

    def mark_selected(self, value: Optional[bool]) -> None:
        rows = selected_rows(self.table)
        if rows:
            self.model.set_marks(rows, value)

    def remove_selected(self) -> None:
        self.model.remove_rows(selected_rows(self.table))
        self.state.preview_changed.emit()

    def clear_queue(self) -> None:
        self.state.queue.clear()
        self.model.refresh()
        self.state.preview_changed.emit()

    def first_selected_path(self) -> str:
        row = first_selected_row(self.table)
        if row is not None and row < len(self.state.queue):
            return self.state.queue[row].path
        return ''

    def first_path(self) -> str:
        """Selected row, else the first row in view order."""
        p = self.first_selected_path()
        if p or not self.state.queue:
            return p
        idx = self.proxy.mapToSource(self.proxy.index(0, 0))
        return self.state.queue[idx.row()].path if idx.isValid() else self.state.queue[0].path

    def _toggle_inspector(self, show: bool) -> None:
        self.inspector.setVisible(show)

    def _splitter_moved(self, *_args) -> None:
        sizes = self.splitter.sizes()
        if len(sizes) > 1 and sizes[1] == 0 and self.inspector_btn.isChecked():
            self.inspector_btn.blockSignals(True)
            self.inspector_btn.setChecked(False)
            self.inspector_btn.blockSignals(False)
            self.inspector.setVisible(False)

    def _selection(self, *_args) -> None:
        self.selection_changed.emit()
        row = first_selected_row(self.table)
        rows = selected_rows(self.table)
        if row is None or row >= len(self.state.queue):
            self.insp_title.setText('Select one script to see its tokens.')
            self.insp_table.set_pairs([])
            return
        q = self.state.queue[row]
        extra = ' ({} selected, showing the first)'.format(len(rows)) if len(rows) > 1 else ''
        self.insp_title.setText(q.path + extra)
        tags = self.state.script_tags(q.path)
        if self.insp_only_tags.isChecked():
            pairs = templates.flatten(tags)
        else:
            tok = self.state.script_tokens(q.path, self.job_folder(), self.job_name.text().strip())
            pairs = sorted(templates.flatten(tok), key=lambda kv: (kv[0] not in tags, kv[0].lower()))
        self.insp_table.set_pairs(pairs, highlight=tags.keys())

    def _double_clicked(self, index) -> None:
        if index.column() != 0:
            reveal(self.state.queue[self.proxy.mapToSource(index).row()].path)

    def _context_menu(self, pos) -> None:
        rows = selected_rows(self.table)
        menu = QtWidgets.QMenu(self)
        menu.addAction('Mark selected', lambda: self.mark_selected(True))
        menu.addAction('Unmark selected', lambda: self.mark_selected(False))
        menu.addAction('Remove selected', self.remove_selected)
        if rows:
            path = self.state.queue[rows[0]].path
            menu.addSeparator()
            menu.addAction('Show in file browser', lambda: reveal(path))
            menu.addAction('Copy path(s)', lambda: QtWidgets.QApplication.clipboard().setText(
                '\n'.join(self.state.queue[r].path for r in rows)))
        menu.exec(self.table.viewport().mapToGlobal(pos))

    # ------------------------------------------------------------------ checks and submission
    def _problems(self, for_submit: bool) -> List[str]:
        st = self.state
        problems = settings_mod.errors_only(settings_mod.validate(st.settings))
        if not st.settings_path:
            problems.append('No settings file loaded (Settings tab).')
        if st.place_source == st.place_target:
            problems.append('Source and target place must differ.')
        marked = [q for q in st.queue if q.marked]
        if not marked:
            problems.append('No marked scripts in the queue.')
        if not self._validate_name():
            problems.append('Job name "{}" is not valid ({}).'.format(self.job_name.text(), self.job_name_state.text()))
        if not paths.is_absolute(self.job_root.text()):
            problems.append('Job root "{}" is not an absolute path.'.format(self.job_root.text()))
        for q in marked:
            if not os.path.isfile(q.path):
                problems.append('Script not found: {}'.format(q.path))
        job_folder, job_name = self.job_folder(), self.job_name.text().strip()
        seen = set()
        for q in marked:
            for p in preflight.check_templates(st.settings, st.script_tokens(q.path, job_folder, job_name)):
                if p not in seen:
                    seen.add(p)
                    problems.append('{} ({})'.format(p, q.name))
        if for_submit:
            problems.extend(deadline.check_executables(st.settings))
        return problems

    def check(self) -> bool:
        problems = self._problems(for_submit=True)
        if problems:
            for p in problems:
                log.error('check: %s', p)
            QtWidgets.QMessageBox.warning(self, 'Check', '{} problem(s):\n\n{}'.format(
                len(problems), '\n'.join('• ' + p for p in problems[:25])))
            return False
        log.info('Check OK: %d scripts ready.', sum(1 for q in self.state.queue if q.marked))
        self.status.emit('Check OK.')
        return True

    def _write_job(self, for_submit: bool) -> Optional[jobs.Job]:
        problems = self._problems(for_submit)
        if problems:
            for p in problems:
                log.error('%s', p)
            QtWidgets.QMessageBox.warning(self, 'Cannot continue', '{} problem(s):\n\n{}'.format(
                len(problems), '\n'.join('• ' + p for p in problems[:25])))
            return None
        job = self.state.build_job(self.job_folder(), self.job_name.text().strip())
        folder = jobs.job_dir(job.job_path)
        if os.path.isfile(folder + '/' + jobs.JOB_FILE):
            if QtWidgets.QMessageBox.question(
                    self, 'Package exists', 'A job already exists in\n{}\n\nOverwrite its job files?'.format(folder)
            ) != QtWidgets.QMessageBox.Yes:
                return None
        try:
            jobs.write_job(job, self.state.settings)
        except OSError as e:
            log.error('Writing job files to %s failed: %s', folder, e)
            return None
        log.info('Job files written to %s (%d scripts)', folder, len(job.scripts))
        return job

    def write_only(self) -> None:
        job = self._write_job(for_submit=False)
        if job:
            self.status.emit('Job files written to {}'.format(jobs.job_dir(job.job_path)))
            reveal(jobs.job_dir(job.job_path))

    def submit(self) -> None:
        if self.submit_worker is not None and self.submit_worker.isRunning():
            return
        job = self._write_job(for_submit=True)
        if not job:
            return
        log.info('Submitting %d jobs to Deadline (batch "%s")...', len(job.scripts), job.job_name)
        self.submit_worker = SubmitWorker(self.state.settings_copy(), job, self)
        self.submit_worker.result.connect(self._submit_result)
        self.submit_worker.done.connect(self._submit_done)
        self.submit_worker.finished.connect(self.submit_worker.deleteLater)
        self.submit_btn.setEnabled(False)
        self.busy.emit(True)
        self.submit_worker.start()

    def _submit_result(self, res, done: int, total: int) -> None:
        if res.ok:
            log.info('Submitted %s -> Deadline job %s', res.script_id, res.job_id)
        else:
            log.error('Submitting %s failed: %s', res.script_id, res.error or res.output)
            if res.command:
                log.debug('command: %s', res.command)
        self.status.emit('Submitting {}/{}...'.format(done, total))

    def _submit_done(self, ok: int, failed: int) -> None:
        self.submit_btn.setEnabled(True)
        self.busy.emit(False)
        msg = 'Deadline: {} job(s) submitted, {} failed.'.format(ok, failed)
        (log.error if failed else log.info)('%s', msg)
        self.status.emit(msg)
        self.submit_worker = None

    def run_local(self) -> None:
        if self.local_process is not None and self.local_process.state() != QtCore.QProcess.NotRunning:
            log.warning('A local pack is already running.')
            return
        st = self.state
        nuke_exe = settings_mod.platform_value(st.settings.get('nuke') or {}, deadline.system_name())
        if not nuke_exe or not os.path.isfile(nuke_exe):
            log.error('Nuke executable not found: %s (Settings tab)', nuke_exe)
            return
        job = self._write_job(for_submit=False)
        if not job:
            return
        script = job.scripts[0]
        entry = paths.join(st.app_dir, 'pack_nuke.py')
        args = ['-t', entry, '--job-dir', jobs.job_dir(job.job_path), '--id', script.id]
        log.info('Running locally: %s %s', nuke_exe, ' '.join(args))
        proc = QtCore.QProcess(self)
        proc.setProcessChannelMode(QtCore.QProcess.MergedChannels)
        proc.readyReadStandardOutput.connect(lambda: self._local_output(proc))
        proc.finished.connect(lambda code, _status: self._local_done(code, job))
        proc.errorOccurred.connect(lambda err: self._local_failed(err, job))
        self.local_process = proc
        self.busy.emit(True)
        proc.start(nuke_exe, args)

    def _local_output(self, proc: QtCore.QProcess) -> None:
        text = proc.readAllStandardOutput().data().decode('utf-8', 'replace')
        for line in text.splitlines():
            if line.strip():
                lvl = logging.ERROR if (' ERROR ' in line or ' CRITICAL ' in line) else (
                    logging.WARNING if ' WARNING ' in line else logging.INFO)
                log.log(lvl, '[nuke] %s', line.rstrip())

    def _local_failed(self, err, job: jobs.Job) -> None:
        if err == QtCore.QProcess.FailedToStart:
            log.error('Nuke could not be started for the local run.')
            self._local_done(-1, job)

    def shutdown(self) -> None:
        """Stop background work before the window closes (a running QThread would abort Qt)."""
        if self.submit_worker is not None and self.submit_worker.isRunning():
            log.info('Waiting for the running Deadline submission to finish...')
            self.submit_worker.stop()
            self.submit_worker.wait()
        if self.local_process is not None and self.local_process.state() != QtCore.QProcess.NotRunning:
            self.local_process.kill()
            self.local_process.waitForFinished(5000)

    def _local_done(self, code: int, job: jobs.Job) -> None:
        if self.local_process is None:
            return
        self.busy.emit(False)
        (log.info if code == 0 else log.error)('Local pack finished with exit code %s. Report folder: %s/%s',
                                               code, jobs.job_dir(job.job_path), jobs.REPORTS_FOLDER)
        self.status.emit('Local pack finished (exit code {}).'.format(code))
        self.local_process = None
