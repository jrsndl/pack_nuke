"""GUI smoke test against a fake PySide6 (tests/fakeqt). Executes the real GUI logic - scan,
filters, marks, queue, inspector, places editing + copy/paste, preview, settings, presets,
job writing and log filtering - without a display. Run with real Qt by hand as well."""
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def touch(path, data=b'x'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


class GuiSmoke(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import PySide6  # noqa: F401
            if getattr(PySide6, '__version__', '') != 'fake':
                raise unittest.SkipTest('real PySide6 installed - run the GUI by hand instead')
        except ImportError:
            pass
        sys.path.insert(0, os.path.join(HERE, 'fakeqt'))
        sys.path.insert(0, REPO)
        for m in [m for m in sys.modules if m.startswith('packnuke.gui')]:
            del sys.modules[m]

    def setUp(self):
        self.tmp = tempfile.mkdtemp().replace('\\', '/')
        # a shots tree
        for shot in ('har_sq01_sh010_main', 'har_sq01_sh020_main'):
            for v in (1, 2, 3):
                touch('{}/shots/{}/work/comp/{}_comp_v{:03d}.nk'.format(self.tmp, shot, shot, v))
            touch('{}/shots/{}/work/roto/{}_roto_v001.nk'.format(self.tmp, shot, shot))
            touch('{}/shots/{}/render/big/frame.nk'.format(self.tmp, shot))
        cfg = json.load(open(os.path.join(REPO, 'settings.json'), encoding='utf-8'))
        cfg['job']['job_root'] = self.tmp + '/out/{project[name]}/{place_source}2{place_target}'
        with open(self.tmp + '/settings.json', 'w') as f:
            json.dump(cfg, f)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_whole_gui(self):
        from PySide6 import QtCore, QtWidgets
        from packnuke.gui.app import setup_logging
        from packnuke.gui.main_window import MainWindow
        # never open Explorer / Finder from the tests (the temp folders are deleted afterwards)
        from packnuke.gui import tab_queue, tab_scripts, widgets
        opened = []
        for mod in (tab_queue, tab_scripts, widgets):
            mod.reveal = opened.append
        widgets.open_path = opened.append
        from packnuke.core import jobs

        QtWidgets.QApplication([])
        app_dir = self.tmp + '/app'
        os.makedirs(app_dir)
        QtCore.QSettings._stores.clear()
        shutil.copy(self.tmp + '/settings.json', app_dir + '/settings.json')   # app root settings
        handler = setup_logging(app_dir)
        win = MainWindow(app_dir, handler)
        st = win.state
        self.assertEqual(st.settings_path, app_dir + '/settings.json')
        self.assertEqual(st.settings_source, 'file')
        self.assertEqual(st.place_names(), ['bc', 'out'])

        # ---- Get Nuke Scripts: one scan of *.nk, then instant filters
        s = win.scripts
        s.root.setText(self.tmp + '/shots')
        s.skip_dirs.setText('render')
        s.search_for.setText('*.nk')
        s.version_regex.setText(r'.*_v(\d{3})\.nk')
        s.last_enabled.setChecked(False)
        s.start_scan()
        self.assertEqual(sum(len(v) for v in s.folders.values()), 8)        # render folder skipped
        self.assertEqual(s.model.rowCount(), 8)
        s.search_contains.setText('/work/comp/')
        s.last_enabled.setChecked(True)
        s.last_n.setValue(1)
        self.assertEqual(sorted(e.name for e in s.model.entries),
                         ['har_sq01_sh010_main_comp_v003.nk', 'har_sq01_sh020_main_comp_v003.nk'])
        s.last_n.setValue(2)
        self.assertEqual(s.model.rowCount(), 4)
        # multi-select + unmark
        s.table.selectionModel().select_rows([0, 1])
        s.mark_selected(False)
        self.assertEqual(len(s.model.marked_entries()), 2)
        self.assertTrue(win._preview_path())
        s.mark_selected(None)  # toggle back
        self.assertEqual(len(s.model.marked_entries()), 4)
        s.model.set_marks([3], False)
        s.send_marked()
        self.assertEqual(len(st.queue), 3)
        s.send_marked()                                                         # no duplicates
        self.assertEqual(len(st.queue), 3)
        self.assertEqual(win.tabs.tabText(1), 'Queue (3/3)')

        # ---- Queue + inspector
        q = win.queue
        q.table.selectionModel().select_rows([0])
        tokens_shown = {q.insp_table.item(r, 0).text(): q.insp_table.item(r, 1).text()
                        for r in range(q.insp_table.rowCount())}
        self.assertIn('SHOT', tokens_shown)
        self.assertIn('project.name', tokens_shown)
        self.assertIn('job', tokens_shown)
        self.assertIn('SHOT=', q.model.data(q.model.index(0, 4)))
        q.inspector_btn.setChecked(False)
        self.assertFalse(q.inspector.isVisible())
        q.inspector_btn.setChecked(True)
        self.assertTrue(q.job_name.text().startswith('bc2out_'))
        self.assertTrue(q.job_root.text().startswith(self.tmp + '/out/BCV_054_HAR/bc2out'))

        # ---- Places: edit anatomy, copy/paste between places, tags, preview
        p = win.places
        p.reload()
        self.assertEqual(p.current_name(), 'bc')
        rows = {p.anatomy.item(r, 0).text(): r for r in range(p.anatomy.rowCount())}
        p.anatomy.item(rows['project.code'], 1).setText('bcv054x')
        self.assertEqual(st.settings['places']['bc']['anatomy']['project']['code'], 'bcv054x')
        self.assertTrue(st.dirty)
        p.anatomy.selectionModel().select_rows([rows['project.code']])
        p.copy_anatomy()
        p.place_list.setCurrentRow(1)
        self.assertEqual(p.current_name(), 'out')
        p.paste_anatomy()
        self.assertEqual(st.settings['places']['out']['anatomy']['project']['code'], 'bcv054x')
        p.place_list.setCurrentRow(0)
        p.tags.selectionModel().select_rows([0])
        p.copy_tags_to(['out'])
        self.assertEqual(st.settings['places']['out']['script_path_tags'][0]['replace'], '\\1')
        p.add_tag()
        self.assertEqual(st.settings['places']['bc']['script_path_tags'][-1]['name'], 'TAG')
        p.tags.selectionModel().select_rows([p.tags.rowCount() - 1])
        p.remove_tags()
        self.assertNotEqual(st.settings['places']['bc']['script_path_tags'][-1]['name'], 'TAG')
        p.refresh_preview()
        self.assertIn('sq01_sh0', p.preview_title.text())
        labels = [c.texts[0] for top in p.preview.top for c in top.children]
        self.assertIn('Package script', labels)
        self.assertIn('Job root', labels)
        shot_preview = [c for top in p.preview.top for c in top.children if c.texts[0] == 'Package script'][0]
        self.assertIn('/har_sq01_sh0', shot_preview.texts[1])
        # place management
        QtWidgets.QInputDialog.answer = ('vendor2', True)
        p.duplicate_place()
        self.assertIn('vendor2', st.place_names())
        QtWidgets.QInputDialog.answer = ('vendor3', True)
        p.rename_place()
        self.assertIn('vendor3', st.place_names())
        p.delete_place()
        self.assertEqual(st.place_names(), ['bc', 'out'])

        # ---- Settings tab
        t = win.settings_tab
        t.reload()
        t.pool.user_types('io_pool')
        self.assertEqual(st.settings['deadline_job']['pool'], 'io_pool')
        t.priority.setValue(77)
        self.assertEqual(st.settings['deadline_job']['priority'], 77)
        t.copy_threads.setValue(12)
        self.assertEqual(st.settings['copy']['threads'], 12)
        t._platform_edits[('nuke', 'Windows')].setText('C:/Nuke/Nuke.exe')
        self.assertEqual(st.settings['nuke']['Windows'], 'C:/Nuke/Nuke.exe')
        # Nuke Scripts page
        ns = t.nuke_scripts
        ns.w['package']['path'].user_types('{job}/{SHOT}/pkg_{script_name}.nk')
        self.assertEqual(st.settings['nuke_scripts']['package']['path'], '{job}/{SHOT}/pkg_{script_name}.nk')
        self.assertIn('/har_sq01_sh0', ns.w['package']['path:res'].text())
        ns.w['target']['copy'].setChecked(True)
        self.assertTrue(st.settings['nuke_scripts']['target']['copy'])
        ns.w['package']['relative_above_script'].setValue(2)
        self.assertEqual(st.settings['nuke_scripts']['package']['relative_above_script'], 2)
        ns.w['source']['path'].user_types('{job}/{NOPE}/x.nk')
        self.assertIn('missing: NOPE', ns.w['source']['path:res'].text())
        ns.w['source']['path'].user_types('{job}/{SHOT}/{script_name}_source.nk')
        # Categories page
        c = t.categories
        self.assertEqual(c.current(), 'src')
        c.test_path.setText('//srv/shots/sh010/plates/v001/plate.%04d.exr')
        self.assertTrue(c.test_result.text().startswith('Matches'), c.test_result.text())
        c.fields['top_folder'].user_types('{extension}')
        self.assertEqual(st.settings['categories']['src']['path']['top_folder'], '{extension}')
        self.assertIn('/exr/plate.%04d.exr', c.resolved['package'].text())
        c.test_path.setText('//srv/shots/sh010/plates/notes.txt')
        c.test_class.setText('Grade')                 # src is OR-combined; Read alone would match
        self.assertTrue(c.test_result.text().startswith('Does not match'))
        QtWidgets.QInputDialog.answer = ('mov', True)
        c.add()
        self.assertEqual(list(st.settings['categories']), ['src', 'mov', 'fonts', 'gizmos', 'ocio'])
        c.add_filter()
        c.filters.item(0, 1).setText(r'\.(mov)$')
        self.assertEqual(st.settings['categories']['mov']['filters'][0]['search'], r'\.(mov)$')
        c.move(-1)
        self.assertEqual(list(st.settings['categories']), ['mov', 'src', 'fonts', 'gizmos', 'ocio'])
        QtWidgets.QInputDialog.answer = ('movies', True)
        c.rename()
        self.assertEqual(list(st.settings['categories']), ['movies', 'src', 'fonts', 'gizmos', 'ocio'])
        c.delete()
        self.assertEqual(list(st.settings['categories']), ['src', 'fonts', 'gizmos', 'ocio'])
        # built-in category: editable folders/options, fixed name, no filters
        c.list.setCurrentRow(list(st.settings['categories']).index('gizmos'))
        self.assertEqual(c.current(), 'gizmos')
        self.assertFalse(c.filt_box.isVisible())
        self.assertTrue(c.to_groups.isVisible())
        self.assertFalse(c._buttons['ren'].isEnabled())
        c.rename()
        c.delete()
        self.assertIn('gizmos', st.settings['categories'])
        c.to_groups.setChecked(True)
        c.fields['top_folder'].user_types('gz')
        from packnuke.core import settings as settings_mod
        g = settings_mod.special(st.settings, 'gizmos')
        self.assertEqual((g['to_groups'], g['top_folder']), (True, 'gz'))
        self.assertIn('/gz/<file>', c.resolved['package'].text())
        c.list.setCurrentRow(list(st.settings['categories']).index('ocio'))
        c.max_files.setValue(10)
        self.assertEqual(settings_mod.special(st.settings, 'ocio')['max_files'], 10)
        self.assertFalse(c.skip_disabled.isVisible())
        QtWidgets.QInputDialog.answer = ('fonts', True)
        c.list.setCurrentRow(0)
        c.add()                                   # reserved name refused
        self.assertEqual(list(st.settings['categories']).count('fonts'), 1)
        c.list.setCurrentRow(0)

        t.pages.setCurrentIndex(3)
        idx = t.json_model.index(0, 1)
        self.assertTrue(idx.isValid())
        t.validate()
        saved = self.tmp + '/settings_saved.json'
        t.path.setText(saved)
        t.save()
        self.assertFalse(st.dirty)
        with open(saved, encoding='utf-8') as f:
            self.assertEqual(json.load(f)['deadline_job']['priority'], 77)

        # ---- Presets
        pr = win.presets
        pr.folder.setText(self.tmp + '/presets')
        pr._folder_changed()
        pr.name.setText('comp last 2')
        pr.save()
        self.assertEqual(pr.preset_names(), ['comp last 2'])
        preset_file = self.tmp + '/presets/comp last 2.json'
        # the preset is now where the settings live
        self.assertEqual((st.settings_source, st.settings_path, st.dirty), ('preset', preset_file, False))
        self.assertEqual(t.path.text(), preset_file)
        # editing + Save writes into the preset, keeping its GUI state
        t.pool.user_types('pool_in_preset')
        self.assertTrue(st.dirty)
        t.save()
        with open(preset_file, encoding='utf-8') as f:
            pdata = json.load(f)
        self.assertEqual(pdata['settings']['deadline_job']['pool'], 'pool_in_preset')
        self.assertEqual(pdata['gui']['search_contains'], '/work/comp/')
        s.search_contains.setText('/work/roto/')
        self.assertTrue(pr.load('comp last 2'))
        self.assertEqual(s.search_contains.text(), '/work/comp/')
        self.assertFalse(st.dirty)
        self.assertEqual(st.settings['deadline_job']['pool'], 'pool_in_preset')
        self.assertEqual(st.ini.get_str('presets_folder'), self.tmp + '/presets')
        self.assertEqual(st.ini.get_str('last_preset'), 'comp last 2')

        # ---- Write job files (no Deadline here)
        q.reset_job_root()
        q.write_only()
        folder = jobs.job_dir(q.job_folder())
        job, cfg = jobs.read_job(folder)
        self.assertEqual(len(job.scripts), len([x for x in st.queue if x.marked]))
        self.assertEqual(job.scripts[0].tokens['project']['name'], 'BCV_054_HAR')
        self.assertIn('SHOT', job.scripts[0].tags)
        # submit refuses without executables
        QtWidgets.QMessageBox.warnings.clear()
        q.submit()
        self.assertTrue(any('not found' in w or 'not set' in w for w in QtWidgets.QMessageBox.warnings))

        # ---- queue removal
        q.table.selectionModel().select_rows([0])
        q.remove_selected()
        self.assertEqual(len(st.queue), 2)

        # ---- Log tab level filter
        lg = win.log_tab
        n_all = len(lg.records)
        self.assertGreater(n_all, 5)
        lg.level_combo.setCurrentIndex(3)   # errors only
        shown = len(lg.view._lines)
        self.assertLess(shown, n_all)
        lg.level_combo.setCurrentIndex(0)
        self.assertEqual(len(lg.view._lines), n_all)

        # ---- close: ini written
        class Ev:
            def accept(self):
                self.ok = True

            def ignore(self):
                self.ok = False
        ev = Ev()
        win.closeEvent(ev)
        self.assertTrue(ev.ok)
        self.assertEqual(st.ini.get_str('search_contains'), '/work/comp/')

        # ---- restart: the last preset is restored
        win2 = MainWindow(app_dir, handler)
        self.assertEqual(win2.state.settings_source, 'preset')
        self.assertEqual(win2.state.settings_path, preset_file)
        self.assertEqual(win2.state.settings['deadline_job']['pool'], 'pool_in_preset')


if __name__ == '__main__':
    unittest.main()
