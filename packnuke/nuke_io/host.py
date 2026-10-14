"""Nuke host: reads a script into a :class:`ScanResult` and writes relinks back.

Everything Nuke-specific lives here so the rest of the code can be tested without Nuke
(tests use a fake host with the same methods).
"""
from __future__ import annotations

import logging
import os
from typing import List, Set

import nuke  # noqa: F401  (only importable inside Nuke)

from ..core import paths
from ..core.plan import OcioInfo, ScanResult, ScannedFile, ScannedFont, ScannedGizmo
from ..core.relink import RelinkSpec

log = logging.getLogger(__name__)

FONT_EXTENSIONS = ('.ttf', '.otf', '.ttc', '.pfb', '.pfa', '.dfont')
PLUGIN_EXTENSIONS = ('.dll', '.so', '.dylib')


def _knob_value(node, name):
    k = node.knob(name)
    if k is None:
        return None
    try:
        v = k.value()
    except Exception:
        v = None
    if v is None:
        try:
            v = k.getValue()
        except Exception:
            v = None
    return v


class NukeHost:
    def open_script(self, path: str) -> None:
        try:
            nuke.scriptOpen(path)
        except RuntimeError as e:
            # nuke -t raises for missing plugins / unknown knobs even though the script loaded
            loaded = paths.norm(nuke.root().name() or '')
            if loaded.lower() != paths.norm(path).lower():
                raise
            log.warning('Script opened with errors (packing continues): %s', e)

    def save_script_as(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        nuke.scriptSaveAs(path, 1)

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _all_nodes():
        return nuke.allNodes(recurseGroups=True)

    @staticmethod
    def _parent_of(node):
        """Parent group/gizmo of a node via its full name (works in every Nuke version)."""
        full = node.fullName()
        if '.' not in full:
            return nuke.root()
        return nuke.toNode(full.rsplit('.', 1)[0]) or nuke.root()

    @classmethod
    def _in_gizmo(cls, node) -> bool:
        full = node.fullName()
        while '.' in full:
            full = full.rsplit('.', 1)[0]
            parent = nuke.toNode(full)
            if parent is not None and isinstance(parent, nuke.Gizmo):
                return True
        return False

    @staticmethod
    def _connected_set(nodes) -> Set[str]:
        """Full names of nodes that feed at least one other node (single pass, no dependent())."""
        used: Set[str] = set()
        for n in nodes:
            try:
                count = n.inputs()
            except Exception:
                continue
            for i in range(count):
                inp = n.input(i)
                if inp is not None:
                    used.add(inp.fullName())
        return used

    @staticmethod
    def _project_dir() -> str:
        try:
            return paths.norm(nuke.root()['project_directory'].evaluate() or '')
        except Exception:
            return ''

    @staticmethod
    def _evaluate(node, knob, raw: str) -> str:
        """Evaluate TCL in a file path but keep frame/view tokens (%04d, ####, %V)."""
        if '[' not in raw and '$' not in raw:
            return raw
        if knob.name() == 'file':
            try:
                v = nuke.filename(node)
                if v:
                    return v
            except Exception:
                pass
        try:
            v = nuke.tcl('subst', '-nobackslashes', raw)
            if isinstance(v, str) and v:
                return v
        except Exception:
            pass
        try:
            v = knob.evaluate()
            if isinstance(v, str) and v:
                log.warning('%s.%s: expression evaluated at the current frame: %s', node.fullName(), knob.name(), v)
                return v
        except Exception:
            pass
        return raw

    # ------------------------------------------------------------------ scanning
    def scan_gizmos(self) -> List[ScannedGizmo]:
        nodes = self._all_nodes()
        used = self._connected_set(nodes)
        out: List[ScannedGizmo] = []
        plugin_dirs = [paths.norm(p) for p in nuke.pluginPath()]
        for n in nodes:
            if not isinstance(n, nuke.Gizmo):
                continue
            cls = n.Class()
            path = ''
            try:
                path = paths.norm(n.filename() or '')
            except Exception:
                path = ''
            if not path or not os.path.isfile(path):
                name = cls if cls.lower().endswith('.gizmo') else cls + '.gizmo'
                for d in plugin_dirs:
                    cand = d + '/' + name
                    if os.path.isfile(cand):
                        path = cand
                        break
            out.append(ScannedGizmo(
                node=n.fullName(), node_class=cls, path=path if os.path.isfile(path) else '',
                disabled=bool(_knob_value(n, 'disable')),
                disconnected=self._disconnected(n, used)))
        return out

    @staticmethod
    def _disconnected(node, used: Set[str]) -> bool:
        if node.fullName() in used:
            return False
        try:
            for i in range(node.inputs()):
                if node.input(i) is not None:
                    return False
        except Exception:
            pass
        return True

    def scan(self) -> ScanResult:
        res = ScanResult()
        try:
            res.views = list(nuke.views())
        except Exception:
            res.views = []
        res.ocio = self._ocio()
        res.plugins = self._plugins()
        project_dir = self._project_dir()
        fonts_db = None

        nodes = self._all_nodes()
        used = self._connected_set(nodes)
        for n in nodes:
            full = n.fullName()
            cls = n.Class()
            disabled = bool(_knob_value(n, 'disable'))
            disconnected = self._disconnected(n, used)
            in_gizmo = self._in_gizmo(n)
            for kname, knob in n.knobs().items():
                kclass = knob.Class()
                if kclass == 'File_Knob':
                    raw = knob.value() or ''
                    if not raw.strip():
                        continue
                    value = paths.norm(self._evaluate(n, knob, raw))
                    rel = False
                    if not paths.is_absolute(value) and project_dir:
                        value = paths.join(project_dir, value[2:] if value.startswith('./') else value)
                        rel = True
                    res.files.append(ScannedFile(
                        node=full, node_class=cls, knob=kname, raw=raw, path=value,
                        disabled=disabled, disconnected=disconnected, in_gizmo=in_gizmo,
                        project_relative=rel, is_font=value.lower().endswith(FONT_EXTENSIONS),
                        info=self._media_info(n, value)))
                elif kclass == 'FreeType_Knob':
                    family, style = self._font_value(knob)
                    if not family:
                        continue
                    if fonts_db is None:
                        fonts_db = self._fonts_db()
                    path, index = '', None
                    for f in fonts_db:
                        if f[0] == family and f[1] == style:
                            path, index = paths.norm(f[2]), (f[3] if len(f) > 3 else None)
                            break
                    res.fonts.append(ScannedFont(
                        node=full, node_class=cls, knob=kname, family=family, style=style, path=path,
                        index=index, disabled=disabled, disconnected=disconnected))
        return res

    @staticmethod
    def _font_value(knob):
        try:
            v = knob.getValue()
        except Exception:
            v = None
        if isinstance(v, (list, tuple)) and len(v) >= 2:
            return str(v[0]), str(v[1])
        if isinstance(v, (list, tuple)) and len(v) == 1:
            return str(v[0]), ''
        return '', ''

    @staticmethod
    def _fonts_db():
        try:
            return [f for f in nuke.getFonts() if isinstance(f, (list, tuple)) and len(f) >= 3]
        except Exception:
            return []

    @staticmethod
    def _media_info(node, path: str) -> dict:
        info = {}
        cs = _knob_value(node, 'colorspace')
        if cs is not None:
            cs = str(cs)
            if cs.startswith('default'):
                # "default (sRGB)" -> keep what Nuke shows; plain "default" -> guess from root LUTs
                if cs == 'default':
                    try:
                        lut = 'floatLut' if path.lower().endswith('.exr') else 'int8Lut'
                        cs = 'default ({})'.format(nuke.root()[lut].value())
                    except Exception:
                        pass
            info['colorspace'] = cs
        tt = _knob_value(node, 'transformType')
        if tt is not None:
            info['transform_type'] = str(tt)
            info['display'] = _knob_value(node, 'ocioDisplay')
            info['view'] = _knob_value(node, 'ocioView')
        raw = _knob_value(node, 'raw')
        if raw:
            info['raw'] = True
        if node.Class() == 'Read':
            first, last = _knob_value(node, 'first'), _knob_value(node, 'last')
            try:
                info['read_range'] = '{}-{}'.format(int(float(first)), int(float(last)))
            except (TypeError, ValueError):
                pass
        return info

    @staticmethod
    def _ocio() -> OcioInfo:
        root = nuke.root()
        cm = _knob_value(root, 'colorManagement')
        cfg = _knob_value(root, 'OCIO_config')
        info = OcioInfo(color_management=str(cm or ''), config=str(cfg or ''))
        if cm is not None and str(cm) != 'OCIO':
            return info
        env = os.environ.get('OCIO')
        if env:
            info.config_path = paths.norm(os.path.abspath(env))
            info.from_env = True
        elif str(cfg) == 'custom' and root.knob('customOCIOConfigPath') is not None:
            try:
                p = root['customOCIOConfigPath'].evaluate()
            except Exception:
                p = _knob_value(root, 'customOCIOConfigPath')
            if p:
                info.config_path = paths.norm(os.path.abspath(p))
        return info

    @staticmethod
    def _plugins() -> List[str]:
        try:
            exe_dir = os.path.normcase(os.path.dirname(os.path.abspath(nuke.env['ExecutablePath'])))
        except Exception:
            exe_dir = ''
        out = []
        try:
            loaded = nuke.plugins()
        except Exception:
            loaded = []
        for p in loaded:
            if not str(p).lower().endswith(PLUGIN_EXTENSIONS):
                continue
            if exe_dir and os.path.normcase(os.path.abspath(p)).startswith(exe_dir):
                continue
            out.append(paths.norm(p))
        return out

    # ------------------------------------------------------------------ gizmos -> groups
    def convert_gizmos_to_groups(self) -> List[str]:
        """Convert every gizmo (also nested ones) to a group, keeping inputs AND outputs."""
        messages: List[str] = []
        failed: Set[str] = set()
        for _ in range(10000):
            todo = [n for n in self._all_nodes() if isinstance(n, nuke.Gizmo) and n.fullName() not in failed]
            if not todo:
                break
            g = todo[0]
            name = g.fullName()
            try:
                self._gizmo_to_group(g)
                messages.append('converted gizmo {} to group'.format(name))
            except Exception as e:
                failed.add(name)
                messages.append('failed to convert gizmo {}: {}'.format(name, e))
        return messages

    @classmethod
    def _gizmo_to_group(cls, g) -> None:
        parent = cls._parent_of(g)
        with parent:
            gname = g.fullName()
            name = g.name()
            x, y = g.xpos(), g.ypos()
            inputs = [g.input(i) for i in range(g.inputs())]
            outputs = []
            for d in g.dependent(nuke.INPUTS | nuke.HIDDEN_INPUTS, False):
                for i in range(d.inputs()):
                    inp = d.input(i)
                    if inp is not None and inp.fullName() == gname:
                        outputs.append((d, i))
            for n in nuke.selectedNodes():
                n.setSelected(False)
            g.setSelected(True)
            grp = g.makeGroup()
            grp.setSelected(False)
            nuke.delete(g)
            grp.setName(name)
            grp.setXYpos(x, y)
            for i in range(grp.inputs()):
                grp.setInput(i, None)
            for i, inp in enumerate(inputs):
                if inp is not None:
                    grp.setInput(i, inp)
            for d, i in outputs:
                d.setInput(i, grp)

    # ------------------------------------------------------------------ relink
    def apply_relink(self, spec: RelinkSpec) -> List[str]:
        warnings: List[str] = []
        root = nuke.root()
        # TCL like [value root.name] must resolve against the script being written
        try:
            root['name'].setValue(spec.save_path)
        except Exception as e:
            warnings.append('relink: could not set root.name: {}'.format(e))
        if spec.project_dir_knob is not None:
            root['project_directory'].setValue(spec.project_dir_knob)
        for op in spec.ops:
            node = nuke.toNode(op.node)
            if node is None:
                warnings.append('relink: node {} not found'.format(op.node))
                continue
            knob = node.knob(op.knob)
            if knob is None:
                warnings.append('relink: knob {}.{} not found'.format(op.node, op.knob))
                continue
            try:
                knob.setValue(op.value)
                if op.color is not None and node.knob('tile_color') is not None:
                    node['tile_color'].setValue(op.color)
            except Exception as e:
                warnings.append('relink: {}.{}: {}'.format(op.node, op.knob, e))
        # OCIO_config before the path, so the path is read as a custom config
        order = sorted(spec.root_ops, key=lambda k: 0 if k == 'OCIO_config' else 1)
        for name in order:
            if root.knob(name) is None:
                warnings.append('relink: root knob {} not available in this Nuke version'.format(name))
                continue
            try:
                root[name].setValue(spec.root_ops[name])
            except Exception as e:
                warnings.append('relink: root.{}: {}'.format(name, e))
        return warnings
