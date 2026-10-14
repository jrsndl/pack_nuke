"""Command line front end (no Nuke, no Deadline: --mode write / --check)."""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packnuke import cli  # noqa: E402
from packnuke.core import jobs  # noqa: E402


def touch(path, data=b'# nuke'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp().replace('\\', '/')
        self.scripts = []
        for shot in ('sq01_sh010', 'sq01_sh020'):
            p = '{}/shots/{}/{}_comp_v003.nk'.format(self.tmp, shot, shot)
            touch(p)
            self.scripts.append(p)
        self.cfg = {
            'job': {'job_name_default': '{place_source}2{place_target}_{timestamp}',
                    'job_root': self.tmp + '/out/{project[name]}', 'job_name_check': r'^.+2.+_\d{6}_\d{4}_'},
            'places': {
                'bc': {'anatomy': {'project': {'name': 'HAR'}}, 'use_script_path_tags': True,
                       'script_path_tags': [{'name': 'SHOT', 'source': 'File Name',
                                             'search': r'^([^_]+_[^_]+)_', 'replace': r'\1'}]},
                'out': {'anatomy': {}}},
            'nuke_scripts': {'source': {'path': '{job}/{SHOT}/{script_name}_source.nk'},
                             'package': {'path': '{job}/{SHOT}/{script_name}.nk'}},
            'categories': {'src': {'path': {'root_template': '{job}/{SHOT}/src',
                                            'root_template_relink': '{job}/{SHOT}/src'}}},
        }
        self.settings = self.tmp + '/settings.json'
        with open(self.settings, 'w') as f:
            json.dump(self.cfg, f)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(args))
        return code, out.getvalue().strip(), err.getvalue()

    def test_write_with_settings_and_list(self):
        lst = self.tmp + '/scripts.txt'
        with open(lst, 'w') as f:
            f.write('# comment\n\n"{}"\n{}\n'.format(self.scripts[0], self.scripts[1]))
        code, out, err = self.run_cli('--settings', self.settings, '--source', 'bc', '--target', 'out',
                                      '--list', lst, '--mode', 'write', '--version-regex', r'_v(\d{3})\.nk')
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith(self.tmp + '/out/HAR/bc2out_'), out)
        self.assertEqual(out.count('\n'), 0)              # only the package root on stdout
        job, _cfg = jobs.read_job(out + '/_pack_nuke')
        self.assertEqual([s.version for s in job.scripts], ['003', '003'])
        self.assertEqual(job.scripts[1].tokens['SHOT'], 'sq01_sh020')

    def test_preset_by_name_and_places_from_preset(self):
        presets = self.tmp + '/presets'
        os.makedirs(presets)
        with open(presets + '/bcv.json', 'w') as f:
            json.dump({'kind': 'packnuke_preset', 'name': 'bcv', 'settings': self.cfg,
                       'gui': {'place_source': 'bc', 'place_target': 'out'}}, f)
        code, out, err = self.run_cli('--preset', 'bcv', '--presets-folder', presets, self.scripts[0],
                                      '--mode', 'write', '--job-name', 'bc2out_260101_1200_0200_x')
        self.assertEqual(code, 0, err)
        self.assertEqual(out, self.tmp + '/out/HAR/bc2out_260101_1200_0200_x')
        self.assertTrue(os.path.isfile(out + '/_pack_nuke/job.json'))

    def test_check_only_and_json(self):
        code, out, err = self.run_cli('--settings', self.settings, '--source', 'bc', '--target', 'out',
                                      self.scripts[0], '--check', '--json', '--mode', 'write')
        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data['mode'], 'check')
        self.assertEqual(data['problems'], [])
        self.assertFalse(os.path.exists(data['package_root']))   # nothing written

    def test_problems_exit_2_and_no_stdout(self):
        code, out, err = self.run_cli('--settings', self.settings, '--source', 'bc', '--target', 'out',
                                      self.tmp + '/missing.nk', '--mode', 'write')
        self.assertEqual(code, 2)
        self.assertEqual(out, '')
        self.assertIn('Script not found', err)
        code, out, err = self.run_cli('--settings', self.settings, '--source', 'bc', '--target', 'bc',
                                      self.scripts[0], '--mode', 'write')
        self.assertEqual(code, 2)
        self.assertIn('must differ', err)
        code, out, err = self.run_cli('--settings', self.settings, self.scripts[0], '--mode', 'write')
        self.assertEqual(code, 2)
        self.assertIn('--source', err)
        code, out, err = self.run_cli('--preset', 'nope', '--presets-folder', self.tmp, self.scripts[0])
        self.assertEqual(code, 2)
        self.assertIn('Preset not found', err)

    def test_submit_needs_executables(self):
        code, out, err = self.run_cli('--settings', self.settings, '--source', 'bc', '--target', 'out',
                                      self.scripts[0])
        self.assertEqual(code, 2)
        self.assertIn('Deadline command', err)


if __name__ == '__main__':
    unittest.main()
