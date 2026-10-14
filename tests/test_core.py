"""Unit tests for packnuke.core (no Nuke, no Qt). Run: python -m unittest discover tests"""
import datetime
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packnuke.core import (copier, filters, jobs, paths, preflight, scanner, sequences,  # noqa: E402
                           settings as settings_mod, templates, tokens, versions)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def touch(path, data=b'x'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


class TmpCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp().replace('\\', '/')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)


class TestPaths(unittest.TestCase):
    def test_norm(self):
        self.assertEqual(paths.norm('C:\\a\\\\b\\'), 'C:/a/b')
        self.assertEqual(paths.norm('\\\\server\\share\\x'), '//server/share/x')
        self.assertEqual(paths.norm('C:/'), 'C:/')

    def test_relpath_component_wise(self):
        # old make_relative matched string prefixes: /a/b vs /a/bc/x gave "c/x"
        self.assertEqual(paths.relpath('/a/bc/x', '/a/b'), '../bc/x')
        self.assertEqual(paths.relpath('/a/b', '/a/b'), '.')
        self.assertEqual(paths.relpath('/a/b/c/d.exr', '/a/b'), 'c/d.exr')
        self.assertEqual(paths.relpath('/a', '/a/b/c'), '../..')
        self.assertEqual(paths.relpath('C:/x/y', 'c:/x/z'), '../y')
        self.assertIsNone(paths.relpath('D:/x', 'C:/x'))
        self.assertIsNone(paths.relpath('//srv/a/x', '//srv/b/x'))
        self.assertEqual(paths.relpath('//srv/a/x/y', '//srv/a/x'), 'y')

    def test_is_absolute(self):
        for p in ('C:/a', '/a', '//srv/share', 'c:\\a'):
            self.assertTrue(paths.is_absolute(p), p)
        for p in ('a/b', './a', '../a'):
            self.assertFalse(paths.is_absolute(p), p)


class TestSequences(TmpCase):
    def test_parse(self):
        fp = sequences.parse_frame_pattern('plate.%04d.exr')
        self.assertEqual((fp.prefix, fp.padding, fp.suffix), ('plate.', 4, '.exr'))
        self.assertEqual(sequences.parse_frame_pattern('a.%d.exr').padding, 0)
        self.assertEqual(sequences.parse_frame_pattern('a.%4d.exr').padding, 4)
        self.assertEqual(sequences.parse_frame_pattern('a.####.exr').padding, 4)
        self.assertEqual(sequences.parse_frame_pattern('a.#.exr').padding, 1)
        self.assertIsNone(sequences.parse_frame_pattern('a.exr'))

    def test_exact_matching(self):
        d = self.tmp + '/seq'
        for n in ('plate.1001.exr', 'plate.1002.exr', 'plate.0999.exr', 'plate.10000.exr',
                  'plate.v2.1001.exr', 'plate.1001_old.exr', 'plate.101.exr', 'other.1001.exr'):
            touch(d + '/' + n)
        found = sequences.list_sequence(d + '/plate.%04d.exr')
        self.assertEqual([f for f, _p, _s in found], [999, 1001, 1002, 10000])
        found = sequences.list_sequence(d + '/plate.####.exr')
        self.assertEqual(len(found), 4)
        found = sequences.list_sequence(d + '/plate.%d.exr')
        self.assertEqual(sorted(f for f, _p, _s in found), [101, 999, 1001, 1002, 10000])

    def test_views_and_resolve(self):
        d = self.tmp + '/st'
        for v in ('left', 'right'):
            for f in (1, 2):
                touch('{}/{}/img.{:04d}.exr'.format(d, v, f))
        res = sequences.resolve_files(d + '/%V/img.%04d.exr', ['left', 'right'])
        self.assertEqual(len(res.files), 4)
        self.assertEqual(res.frames, [1, 2])
        self.assertEqual(res.total_size, 4)
        touch(d + '/l.txt')
        res = sequences.resolve_files(d + '/%v.txt', ['left', 'right'])
        self.assertEqual(res.files, [d + '/l.txt'])

    def test_clean_name_and_ranges(self):
        self.assertEqual(sequences.clean_name('plate.%04d.exr'), 'plate.exr')
        self.assertEqual(sequences.clean_name('plate_####.exr'), 'plate.exr')
        self.assertEqual(sequences.frame_ranges([1, 2, 3, 5, 7, 8]), '1-3,5,7-8')


class TestTemplates(unittest.TestCase):
    def test_nested_and_missing(self):
        tok = {'project': {'name': 'HAR'}, 'job': 'Z:/x'}
        self.assertEqual(templates.format_template('{job}/{project[name]}', tok), 'Z:/x/HAR')
        with self.assertRaises(templates.TemplateError) as cm:
            templates.format_template('{job}/{SHOT}/{project[code]}', tok)
        self.assertEqual(cm.exception.missing, ['SHOT', 'project[code]'])
        self.assertEqual(templates.format_template('{job}/{SHOT}', tok, strict=False), 'Z:/x/{SHOT}')
        self.assertEqual(templates.format_template('{root[work]}/a', {}, strict=False), '{root[work]}/a')
        self.assertEqual(templates.missing_tokens('{a}{b[c]}', {'a': 1}), ['b[c]'])

    def test_flatten_roundtrip(self):
        d = {'studio': {'name': 'BC', 'code': 'bc'}, 'x': 1}
        self.assertEqual(templates.unflatten(templates.flatten(d)), d)


class TestFilters(unittest.TestCase):
    subject = {'File Name': 'plate.1001.exr', 'File Path': '/p/v001/plate.1001.exr',
               'Node Class': 'Read', 'Knob Name': 'file'}

    def test_regex_without_match_does_not_crash(self):
        r = filters.eval_filter({'source': 'File Name', 'search': r'.*\.(\w{2,4})$', 'check': []},
                                {'File Name': 'noextension'})
        self.assertFalse(r.hit)
        r = filters.eval_filter({'source': 'File Name', 'search': 'plate'}, self.subject)  # no group
        self.assertTrue(r.hit)
        self.assertEqual(r.value, 'plate')

    def test_check_invert_alias(self):
        f = {'source': 'File Name', 'search': r'.*\.(\w{2,4})$', 'check': ['EXR', 'jpg']}
        self.assertTrue(filters.eval_filter(f, self.subject).hit)
        self.assertFalse(filters.eval_filter(dict(f, invert=True), self.subject).hit)
        f = {'source': 'Full Path', 'search': r'.*/(v\d\d\d)/.*'}
        r = filters.eval_filter(f, self.subject)
        self.assertTrue(r.hit)
        self.assertEqual(r.value, 'v001')

    def test_category(self):
        cat = {'filter_options': {'skip_disabled': True, 'combine_filters': 'AND'},
               'filters': [{'source': 'Node Class', 'search': 'Read DeepRead', 'token_name': 'cls'},
                           {'source': 'File Name', 'search': r'\.(exr)$', 'token_name': 'ext'}]}
        ok, tok, _ = filters.match_category(cat, self.subject, False, False)
        self.assertTrue(ok)
        self.assertEqual(tok, {'cls': 'Read', 'ext': 'exr'})
        ok, _tok, reason = filters.match_category(cat, self.subject, True, False)
        self.assertFalse(ok)
        self.assertEqual(reason, 'disabled')

    def test_path_tags(self):
        tag = {'name': 'SHOT', 'source': 'File Name', 'search': r'^([^_]*_[^_]*)_(.*)$', 'replace': r'\1'}
        self.assertEqual(filters.eval_path_tag(tag, 'X:/a/sq01_sh010_comp_v001.nk'), 'sq01_sh010')
        tag = {'name': 'EP', 'source': 'File Name', 'search': '.*', 'replace': '101'}
        self.assertEqual(filters.eval_path_tag(tag, 'a.nk'), '101')
        tag = {'name': 'T', 'source': 'File Name', 'search': r'_([a-z]+)_v\d+', 'uppercase': True}
        self.assertEqual(filters.eval_path_tag(tag, 'sh_comp_v001.nk'), 'COMP')
        self.assertIsNone(filters.eval_path_tag({'search': '(['}, 'x'))


class TestVersions(unittest.TestCase):
    def entries(self):
        return [versions.ScriptEntry('/s/a_v{:03d}.nk'.format(i), '/s', 'a_v{:03d}.nk'.format(i)) for i in
                (1, 2, 9, 10)] + [versions.ScriptEntry('/s/notes.nk', '/s', 'notes.nk')]

    def test_first_last(self):
        f = versions.VersionFilter(version_regex=r'_v(\d+)\.nk$', last_enabled=True, last_n=2)
        self.assertTrue(f.compile())
        self.assertEqual([e.version for e in f.filter_folder(self.entries())], ['009', '010'])
        f.first_enabled, f.first_n = True, 1
        self.assertEqual([e.version for e in f.filter_folder(self.entries())], ['001', '009', '010'])

    def test_patterns_contains(self):
        f = versions.VersionFilter(name_patterns='*_v???.nk', contains='/S', last_enabled=False)
        f.compile()
        self.assertEqual(len(f.filter_folder(self.entries())), 4)
        f = versions.VersionFilter(contains='/other/', last_enabled=False)
        f.compile()
        self.assertEqual(f.filter_folder(self.entries()), [])

    def test_bad_regex(self):
        f = versions.VersionFilter(version_regex='([')
        self.assertFalse(f.compile())


class TestScanner(TmpCase):
    def test_scan(self):
        for p in ('a/comp/x_v001.nk', 'a/comp/x_v002.nk', 'b/render/r.nk', 'b/c/d/e/deep.nk', 'a/x.nk~',
                  'a/x.nk.autosave', 'top.NK'):
            touch(self.tmp + '/' + p)
        found = {}
        sc = scanner.NkScanner(self.tmp, workers=4, skip_dirs=['render'])
        stats = sc.run(lambda folder, entries: found.update({folder: entries}))
        names = sorted(e.name for es in found.values() for e in es)
        self.assertEqual(names, ['deep.nk', 'top.NK', 'x_v001.nk', 'x_v002.nk'])
        self.assertEqual(stats.files, 4)
        found = {}
        scanner.NkScanner(self.tmp, workers=2, max_depth=2).run(lambda f, e: found.update({f: e}))
        self.assertNotIn('deep.nk', [e.name for es in found.values() for e in es])

    def test_missing_root(self):
        stats = scanner.NkScanner(self.tmp + '/nope').run(lambda f, e: None)
        self.assertEqual(stats.files, 0)
        self.assertEqual(stats.errors, 1)


class TestSettings(unittest.TestCase):
    def test_repo_settings_file_is_valid(self):
        cfg = settings_mod.load_settings(os.path.join(REPO, 'settings.json'))
        issues = settings_mod.validate(cfg)
        self.assertEqual(settings_mod.errors_only(issues), [])

    def test_special_categories_migration(self):
        old = {'fonts': {'enabled': False, 'root_template': '{job}/f', 'root_template_relink': '/r/f',
                         'top_folder': 'x', 'top_folder_relink': 'y', 'skip_disabled': False},
               'gizmos': {'to_groups': True, 'root_template': '{job}/g', 'root_template_relink': '/r/g'},
               'categories': {'src': {'path': {'root_template': '{job}', 'root_template_relink': '{job}'}}}}
        cfg = settings_mod.complete(old)
        self.assertNotIn('fonts', cfg)
        self.assertEqual(list(cfg['categories']), ['src', 'fonts', 'gizmos', 'ocio'])
        self.assertEqual(cfg['categories']['fonts']['path']['root_template'], '{job}/f')
        self.assertFalse(cfg['categories']['fonts']['filter_options']['skip_disabled'])
        f = settings_mod.special(cfg, 'fonts')
        self.assertEqual((f['enabled'], f['top_folder'], f['skip_disabled']), (False, 'x', False))
        self.assertTrue(settings_mod.special(cfg, 'gizmos')['to_groups'])
        self.assertEqual(settings_mod.special(cfg, 'ocio')['max_files'], 5000)
        self.assertEqual(list(settings_mod.media_categories(cfg)), ['src'])
        # idempotent
        self.assertEqual(settings_mod.complete(cfg), cfg)

    def test_migration_and_validation(self):
        data = {'places': {'a': {'is_source': True, 'script_path_tags': [
            {'name': 'S', 'source': 'File Name', 'search': r'^(sq\d{2-4})', 'replace': '/1'}]}},
            'categories': {'c': {'path': {'root_template': '{job}', 'root_template_relink': '{job}'},
                                 'filters': [{'source': 'Full Path', 'search': '('}]}}}
        cfg = settings_mod.complete(data)
        self.assertNotIn('is_source', cfg['places']['a'])
        self.assertEqual(cfg['categories']['c']['filters'][0]['source'], 'File Path')
        issues = settings_mod.validate(cfg)
        text = '\n'.join(m for _l, m in issues)
        self.assertIn('At least two places', text)
        self.assertIn('invalid regular expression', text)
        self.assertIn('typo', text)
        self.assertIn('quantifier', text)


class TestTokensJobs(TmpCase):
    def cfg(self):
        return settings_mod.complete({
            'job': {'job_name_default': '{place_source}2{place_target}_{timestamp}',
                    'job_root': '{root[work]}/{project[name]}/out'},
            'places': {
                'bc': {'anatomy': {'project': {'name': 'HAR'}, 'root': {'work': 'z:'}},
                       'use_script_path_tags': True,
                       'script_path_tags': [{'name': 'SHOT', 'source': 'File Name',
                                             'search': r'^([^_]+_[^_]+)_', 'replace': r'\1'}]},
                'vendor': {'anatomy': {}}}})

    def test_tokens(self):
        cfg = self.cfg()
        stamp = tokens.timestamp(datetime.datetime(2026, 1, 2, 3, 4, tzinfo=datetime.timezone.utc))
        self.assertTrue(stamp.startswith('260102_0304_'))
        base = tokens.place_tokens(cfg, 'bc', 'vendor', 'T')
        self.assertEqual(tokens.job_root(cfg, base), 'z:/HAR/out')
        self.assertEqual(tokens.job_name(cfg, base), 'bc2vendor_T')
        tok = tokens.build_tokens(cfg, 'bc', 'vendor', 'X:/s/sq1_sh010_comp_v001.nk', 'T', 'z:/HAR/out/j', 'j')
        self.assertEqual(tok['SHOT'], 'sq1_sh010')
        self.assertEqual(tok['script_name'], 'sq1_sh010_comp_v001')
        self.assertEqual(tok['job'], 'z:/HAR/out/j')
        self.assertEqual(tok['project']['name'], 'HAR')
        # tags are evaluated even when no tag matches -> anatomy still present (old bug C3)
        tok = tokens.build_tokens(cfg, 'bc', 'vendor', 'X:/s/nomatch.nk', 'T')
        self.assertEqual(tok['root']['work'], 'z:')

    def test_job_roundtrip(self):
        cfg = self.cfg()
        job_path = self.tmp + '/pkg/job1'
        tok = tokens.build_tokens(cfg, 'bc', 'vendor', 'X:/s/a_b_v001.nk', 'T', job_path, 'job1')
        job = jobs.Job('job1', job_path, 'T', 'bc', 'vendor', [jobs.JobScript(
            jobs.make_script_id(0, 'a_b_track.nk'), 'X:/s/a_b_track.nk', 'a_b_track.nk', '001', {'SHOT': 'a_b'}, tok)])
        self.assertEqual(job.scripts[0].id, '0000_a_b_track')  # old rstrip('.nk') gave 'a_b_trac'
        folder = jobs.write_job(job, cfg)
        job2, cfg2 = jobs.read_job(folder)
        self.assertEqual(job2.scripts[0].tokens['root']['work'], 'z:')
        self.assertEqual(cfg2['job']['path'], job_path)
        with open(folder + '/nuke_files.csv', encoding='utf-8-sig') as f:
            self.assertIn('SHOT=a_b', f.read())

    def test_preflight(self):
        cfg = self.cfg()
        cfg['categories'] = {'src': {'path': {'root_template': '{job}/{SHOT}/{category}',
                                              'root_template_relink': '{job}/{SHOT}', 'top_folder': '{node}',
                                              'top_folder_relink': '{extension}'},
                                     'filters': [{'source': 'File Name', 'search': '(x)', 'token_name': 'extension'}]}}
        tok = tokens.build_tokens(cfg, 'bc', 'vendor', 'X:/s/nomatch.nk', 'T', 'z:/j', 'j')
        problems = preflight.check_templates(cfg, tok)
        self.assertTrue(any('SHOT' in p for p in problems))
        tok['SHOT'] = 'sh'
        self.assertEqual(preflight.check_templates(cfg, tok), [])


class TestCopier(TmpCase):
    def test_copy_skip_and_hash(self):
        src = self.tmp + '/a/f.bin'
        touch(src, b'hello' * 1000)
        t = copier.CopyTask(src, self.tmp + '/b/c/f.bin', 5000)
        r = copier.run_copies([t], threads=2, want_hash=True)
        self.assertEqual(r[0].status, 'copied')
        self.assertEqual(r[0].hash, copier.file_hash(src))
        r = copier.run_copies([t], threads=2)
        self.assertEqual(r[0].status, 'skipped')
        r = copier.run_copies([copier.CopyTask(self.tmp + '/missing', self.tmp + '/x')], threads=1)
        self.assertEqual(r[0].status, 'error')
        self.assertFalse([n for n in os.listdir(self.tmp + '/b/c') if '.pnpart.' in n])

    def test_human_size(self):
        self.assertEqual(copier.human_size(512), '512 B')
        self.assertEqual(copier.human_size(1536), '1.50 KB')


if __name__ == '__main__':
    unittest.main()
