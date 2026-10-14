"""End-to-end packing with a fake Nuke host: plan, copy, relink, report, exit code."""
import csv
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packnuke.core import jobs, settings as settings_mod, tokens  # noqa: E402
from packnuke.core.plan import OcioInfo, ScanResult, ScannedFile, ScannedFont, ScannedGizmo  # noqa: E402
from packnuke.farm import deadline, pack_job  # noqa: E402


def touch(path, data=b'data'):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as f:
        f.write(data)


class FakeHost:
    """Same interface as NukeHost; records what would be written into the script."""

    def __init__(self, scan: ScanResult, gizmos=()):
        self._scan = scan
        self._gizmos = list(gizmos)
        self.knobs = {}
        self.root = {}
        self.saved = {}
        self.converted = False
        self.opened = None

    def open_script(self, path):
        self.opened = path

    def scan_gizmos(self):
        return list(self._gizmos)

    def convert_gizmos_to_groups(self):
        self.converted = True
        return ['converted gizmo {} to group'.format(g.node) for g in self._gizmos]

    def scan(self):
        return self._scan

    def apply_relink(self, spec):
        if spec.project_dir_knob is not None:
            self.root['project_directory'] = spec.project_dir_knob
        for op in spec.ops:
            self.knobs[(op.node, op.knob)] = op.value
        self.root.update(spec.root_ops)
        return []

    def save_script_as(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump({'knobs': {'{}.{}'.format(*k): v for k, v in self.knobs.items()}, 'root': self.root}, f)
        self.saved[path] = (dict(self.knobs), dict(self.root))


class PackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp().replace('\\', '/')
        src = self.tmp + '/src'
        self.src = src
        for f in (1001, 1002, 1003):
            touch('{}/plates/sh010_plate.{}.exr'.format(src, f))
        touch(src + '/plates/sh010_plate.1001_old.exr')       # must NOT be copied
        touch(src + '/elements/smoke.mov')
        touch(src + '/elements/noext')                         # crashed the old category regex
        touch(src + '/fonts/Arial.ttf')
        touch(src + '/gizmos/MyGlow.gizmo')
        touch(src + '/ocio/aces/config.ocio')
        touch(src + '/ocio/aces/luts/a.spi3d')
        touch(src + '/renders/out.1001.exr')
        touch(src + '/sq01_sh010_comp_v003.nk', b'# nuke script')

        self.cfg = settings_mod.complete({
            'job': {'job_name_default': '{place_source}2{place_target}_{timestamp}', 'job_root': self.tmp + '/out'},
            'nuke_scripts': {
                'source': {'copy': True, 'path': '{job}/{SHOT}/{script_name}_source.nk'},
                'package': {'copy': True, 'path': '{job}/{SHOT}/{script_name}.nk', 'relative': True,
                            'relative_above_script': 1},
                'target': {'copy': True, 'path': '{job}/{SHOT}/{script_name}_target.nk',
                           'path_relink': '/mnt/vendor/{SHOT}/nuke/{script_name}.nk', 'relative': False},
            },
            'places': {
                'bc': {'anatomy': {'project': {'name': 'HAR'}, 'root': {'work': 'z:'}},
                       'use_script_path_tags': True,
                       'script_path_tags': [{'name': 'SHOT', 'source': 'File Name',
                                             'search': r'^([^_]+_[^_]+)_', 'replace': r'\1'}]},
                'vendor': {'anatomy': {}}},
            'categories': {
                'plates': {'path': {'root_template': '{job}/{SHOT}/{category}',
                                    'root_template_relink': '/mnt/vendor/{SHOT}/{category}',
                                    'top_folder': '{clean_name}', 'top_folder_relink': '{clean_name}'},
                           'filter_options': {'skip_disabled': True, 'skip_disconnected': True,
                                              'combine_filters': 'AND'},
                           'filters': [{'source': 'File Name', 'search': r'\.(\w{2,4})$', 'check': ['exr'],
                                        'token_name': 'extension'}]},
                'elements': {'path': {'root_template': '{job}/{SHOT}/{category}',
                                      'root_template_relink': '/mnt/vendor/{SHOT}/{category}',
                                      'top_folder': '{node}', 'top_folder_relink': '{node}'},
                             'filter_options': {'skip_disabled': False, 'skip_disconnected': False},
                             'filters': [{'source': 'File Name', 'search': r'\.(mov)$', 'token_name': 'ext'}]},
            },
            'fonts': {'root_template': '{job}/_shared', 'root_template_relink': '/mnt/vendor/_shared',
                      'top_folder': 'fonts', 'top_folder_relink': 'fonts'},
            'gizmos': {'root_template': '{job}/_shared', 'root_template_relink': '/mnt/vendor/_shared',
                       'top_folder': 'gizmos', 'top_folder_relink': 'gizmos', 'to_groups': True},
            'ocio': {'root_template': '{job}/_shared', 'root_template_relink': '/mnt/vendor/_shared',
                     'top_folder': 'ocio', 'top_folder_relink': 'ocio', 'relative': True},
        })
        self.assertEqual(settings_mod.errors_only(settings_mod.validate(self.cfg)), [])

        script = src + '/sq01_sh010_comp_v003.nk'
        stamp = '260101_1200_0200'
        base = tokens.place_tokens(self.cfg, 'bc', 'vendor', stamp)
        job_name = tokens.job_name(self.cfg, base)
        job_path = tokens.job_root(self.cfg, base) + '/' + job_name
        self.job = jobs.Job(job_name, job_path, stamp, 'bc', 'vendor', [jobs.JobScript(
            jobs.make_script_id(0, 'sq01_sh010_comp_v003.nk'), script, 'sq01_sh010_comp_v003.nk', '003',
            tokens.script_tags(self.cfg, 'bc', script),
            tokens.build_tokens(self.cfg, 'bc', 'vendor', script, stamp, job_path, job_name))])
        self.job_folder = jobs.write_job(self.job, self.cfg)
        self.pkg = job_path

        plate = src + '/plates/sh010_plate.%04d.exr'
        self.scan = ScanResult(
            files=[
                ScannedFile('Read1', 'Read', 'file', plate, plate, info={'colorspace': 'ACES', 'read_range': '1001-1003'}),
                ScannedFile('Read2', 'Read', 'file', plate, plate),                      # duplicate of Read1
                ScannedFile('Read3', 'Read', 'file', src + '/elements/smoke.mov', src + '/elements/smoke.mov',
                            disabled=True),
                ScannedFile('Read4', 'Read', 'file', src + '/elements/noext', src + '/elements/noext'),
                ScannedFile('Read5', 'Read', 'file', src + '/missing.%04d.exr', src + '/missing.%04d.exr'),
                ScannedFile('Read6', 'Read', 'proxy', plate, plate),                     # proxy knob
                ScannedFile('Write1', 'Write', 'file', src + '/renders/out.%04d.exr', src + '/renders/out.%04d.exr'),
                ScannedFile('Text1', 'Text', 'font', src + '/fonts/Arial.ttf', src + '/fonts/Arial.ttf', is_font=True),
            ],
            fonts=[ScannedFont('Text2', 'Text2', 'font', 'Arial', 'Regular', src + '/fonts/Arial.ttf')],
            ocio=OcioInfo('OCIO', 'custom', src + '/ocio/aces/config.ocio'),
            views=['main'])
        self.gizmos = [ScannedGizmo('MyGlow1', 'MyGlow', src + '/gizmos/MyGlow.gizmo')]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_pack(self, cfg=None):
        if cfg is not None:
            jobs.write_job(self.job, cfg)
        host = FakeHost(self.scan, self.gizmos)
        code = pack_job.main(['--job-dir', self.job_folder, '--id', self.job.scripts[0].id], host=host)
        return code, host

    def report(self):
        sid = self.job.scripts[0].id
        with open('{}/reports/{}.csv'.format(self.job_folder, sid), encoding='utf-8-sig') as f:
            rows = list(csv.DictReader(f))
        with open('{}/reports/{}.json'.format(self.job_folder, sid), encoding='utf-8') as f:
            data = json.load(f)
        return rows, data

    def test_full_pack(self):
        code, host = self.run_pack()
        rows, data = self.report()
        self.assertEqual(code, 0, data['summary']['errors'])
        pkg = self.pkg
        # sequence copied exactly (no _old file), into the clean_name folder
        plates = sorted(os.listdir(pkg + '/sq01_sh010/plates/sh010_plate.exr'))
        self.assertEqual(plates, ['sh010_plate.1001.exr', 'sh010_plate.1002.exr', 'sh010_plate.1003.exr'])
        # disabled mov still packed (elements category doesn't skip disabled)
        self.assertTrue(os.path.isfile(pkg + '/sq01_sh010/elements/Read3/smoke.mov'))
        # shared files
        self.assertTrue(os.path.isfile(pkg + '/_shared/fonts/Arial.ttf'))
        self.assertTrue(os.path.isfile(pkg + '/_shared/gizmos/MyGlow.gizmo'))
        self.assertTrue(os.path.isfile(pkg + '/_shared/ocio/aces/luts/a.spi3d'))
        self.assertTrue(host.converted)
        # write node outputs are not packed
        self.assertFalse(os.path.exists(pkg + '/sq01_sh010/plates/out.exr'))

        status = {(r['node_name'], r['knob']): r['status'] for r in rows}
        self.assertEqual(status[('Read1', 'file')], 'ok')
        self.assertEqual(status[('Read2', 'file')], 'duplicate')
        self.assertEqual(status[('Read4', 'file')], 'uncategorized')
        self.assertEqual(status[('Read5', 'file')], 'missing')
        self.assertEqual(status[('Write1', 'file')], 'skipped')
        read1 = [r for r in rows if r['node_name'] == 'Read1'][0]
        self.assertEqual(read1['frames'], '1001-1003')
        self.assertIn('ACES', read1['info'])

        # package script: relative to one folder above the script folder
        knobs, root = host.saved[pkg + '/sq01_sh010/sq01_sh010_comp_v003.nk']
        self.assertEqual(root['project_directory'], '[file dirname [file dirname [value root.name]]]')
        self.assertEqual(knobs[('Read1', 'file')], 'sq01_sh010/plates/sh010_plate.exr/sh010_plate.%04d.exr')
        self.assertEqual(knobs[('Read2', 'file')], knobs[('Read1', 'file')])
        self.assertIn(('Read6', 'proxy'), knobs)          # proxy relinked on its own knob (old bug C6)
        self.assertNotIn(('Read4', 'file'), knobs)
        self.assertEqual(root['customOCIOConfigPath'], '[file dirname [value root.name]]/../_shared/ocio/aces/config.ocio')
        self.assertIn('free_type_font_path', root)
        # target script: absolute relink paths (old bug C7: they were never used)
        knobs_t, _root_t = host.saved[pkg + '/sq01_sh010/sq01_sh010_comp_v003_target.nk']
        self.assertEqual(knobs_t[('Read1', 'file')], '/mnt/vendor/sq01_sh010/plates/sh010_plate.exr/sh010_plate.%04d.exr')
        self.assertTrue(os.path.isfile(pkg + '/sq01_sh010/sq01_sh010_comp_v003_source.nk'))

        # second run: everything identical -> skipped, still OK
        code, _host = self.run_pack()
        _rows, data = self.report()
        self.assertEqual(code, 0)
        self.assertEqual(data['summary']['stats']['files_copied'], 0)
        self.assertGreater(data['summary']['stats']['files_skipped'], 0)

    def test_failures_are_reported(self):
        cfg = settings_mod.complete(self.cfg)
        cfg['packing']['fail_on_missing'] = True
        code, _host = self.run_pack(cfg)
        _rows, data = self.report()
        self.assertEqual(code, 1)
        self.assertTrue(any('missing' in e for e in data['summary']['errors']))

    def test_target_collision(self):
        cfg = settings_mod.complete(self.cfg)
        # flat folder for everything: two different smoke.mov sources would collide
        touch(self.src + '/other/smoke.mov', b'different')
        self.scan.files.append(ScannedFile('Read7', 'Read', 'file', self.src + '/other/smoke.mov',
                                           self.src + '/other/smoke.mov'))
        cfg['categories']['elements']['path']['top_folder'] = 'flat'
        code, _host = self.run_pack(cfg)
        rows, data = self.report()
        self.assertEqual(code, 1)
        self.assertTrue(any('collision' in e for e in data['summary']['errors']))

    def test_missing_template_token_fails_loudly(self):
        cfg = settings_mod.complete(self.cfg)
        cfg['categories']['plates']['path']['root_template'] = '{job}/{EPISODE}'
        code, _host = self.run_pack(cfg)
        rows, data = self.report()
        self.assertEqual(code, 1)
        self.assertTrue(any('EPISODE' in e for e in data['summary']['errors']))

    def test_bad_job_input(self):
        self.assertEqual(pack_job.main(['--job-dir', self.tmp + '/nope', '--id', 'x'], host=FakeHost(self.scan)), 2)
        self.assertEqual(pack_job.main(['--job-dir', self.job_folder, '--id', 'nope'], host=FakeHost(self.scan)), 2)

    def test_dry_run(self):
        host = FakeHost(self.scan, self.gizmos)
        code = pack_job.main(['--job-dir', self.job_folder, '--id', self.job.scripts[0].id, '--dry-run'], host=host)
        self.assertEqual(code, 0)
        self.assertFalse(os.path.exists(self.pkg + '/sq01_sh010'))
        _rows, data = self.report()
        self.assertTrue(data['summary']['dry_run'])

    def test_deadline_command(self):
        cfg = settings_mod.complete(self.cfg)
        cfg['deadline']['Windows'] = 'C:/Deadline10/bin/deadlinecommand.exe'
        cfg['nuke']['Windows'] = 'C:/Program Files/Nuke15.2v4/Nuke15.2.exe'
        cfg['deadline_python']['Windows'] = '//srv/tools/pack nuke/pack_nuke.py'
        cfg['deadline_job'].update({'pool': 'io', 'group': '', 'priority': 40, 'LimitGroups': 'nuke'})
        cmd = deadline.build_command(cfg, self.job, self.job.scripts[0], 'Windows')
        self.assertEqual(cmd[0], 'C:/Deadline10/bin/deadlinecommand.exe')
        with open(cmd[1], encoding='utf-8') as f:
            job_info = f.read()
        with open(cmd[2], encoding='utf-8') as f:
            plugin_info = f.read()
        self.assertIn('Plugin=CommandLine', job_info)
        self.assertIn('BatchName=' + self.job.job_name, job_info)
        self.assertIn('LimitGroups=nuke', job_info)
        self.assertIn('Pool=io', job_info)
        self.assertNotIn('Group=', job_info)
        self.assertIn('Executable=C:/Program Files/Nuke15.2v4/Nuke15.2.exe', plugin_info)
        self.assertIn('"//srv/tools/pack nuke/pack_nuke.py"', plugin_info)   # quoted path with spaces
        self.assertIn('--id ' + self.job.scripts[0].id, plugin_info)

if __name__ == '__main__':
    unittest.main()
