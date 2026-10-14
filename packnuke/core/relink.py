"""Compute what to write back into a Nuke script after packing (pure; the Nuke host
applies the result).

Two scripts can be written:

* ``package`` - saved at ``nuke_scripts.package.path``; knobs point at the copies inside the
  package (``Target.nuke``). Relative paths are computed from where the script is saved.
* ``target``  - saved at ``nuke_scripts.target.path`` but meant to live at
  ``nuke_scripts.target.path_relink`` at the receiving place; knobs point at the
  ``*_relink`` locations and relative paths are computed from ``path_relink``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from . import paths, templates
from .plan import FONT, MEDIA, OCIO, ST_DUPLICATE, ST_OK, PackPlan

COLOR_PACKED = 0xB4E614FF     # lime green
COLOR_DUPLICATE = 0x0A882AFF  # deep green


@dataclass
class KnobOp:
    node: str
    knob: str
    value: str
    color: Optional[int] = None


@dataclass
class RelinkSpec:
    which: str
    save_path: str                      # where the script is written now
    location: str                       # where the script will live (relative paths are computed from here)
    relative: bool
    project_dir_knob: Optional[str]     # value for root.project_directory (None = leave)
    project_dir: str                    # the folder that value resolves to
    ops: List[KnobOp] = field(default_factory=list)
    root_ops: Dict[str, str] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def _tcl_script_dir(levels_up: int) -> str:
    expr = '[value root.name]'
    for _ in range(1 + max(0, int(levels_up))):
        expr = '[file dirname {}]'.format(expr)
    return expr


def _up(folder: str, levels: int) -> str:
    for _ in range(max(0, int(levels))):
        folder = paths.dirname(folder)
    return folder


def compute_relink(plan: PackPlan, cfg: Mapping[str, Any], tokens: Mapping[str, Any],
                   which: str) -> RelinkSpec:
    section = cfg['nuke_scripts'][which]
    save_path = paths.norm(templates.format_template(section['path'], tokens, strict=True))
    if which == 'target' and section.get('path_relink'):
        location = paths.norm(templates.format_template(section['path_relink'], tokens, strict=True))
    else:
        location = save_path
    relative = bool(section.get('relative'))
    script_dir = paths.dirname(location)

    project_dir_knob = None
    project_dir = ''
    if relative:
        if section.get('relative_custom_project'):
            project_dir = paths.norm(templates.format_template(
                section.get('relative_custom_project_template', ''), tokens, strict=True))
            project_dir_knob = project_dir
        else:
            above = int(section.get('relative_above_script', 0) or 0)
            project_dir = _up(script_dir, above)
            project_dir_knob = _tcl_script_dir(above)

    spec = RelinkSpec(which, save_path, location, relative, project_dir_knob, project_dir)
    mark = bool((cfg.get('packing') or {}).get('mark_nodes', True))

    def value_for(target_path: str) -> str:
        if not relative:
            return target_path
        rel = paths.relpath(target_path, project_dir)
        if rel is None:
            spec.warnings.append('{} is on a different drive than the project directory {}, '
                                 'kept absolute'.format(target_path, project_dir))
            return target_path
        return rel

    def tcl_from_script(target_path: str) -> str:
        """Path expressed relative to the script itself (for root knobs without project dir support)."""
        if not relative:
            return target_path
        rel = paths.relpath(target_path, script_dir)
        if rel is None:
            return target_path
        return '[file dirname [value root.name]]/' + rel

    font_dirs: List[str] = []
    for item in plan.items:
        if item.status not in (ST_OK, ST_DUPLICATE) or not item.primary:
            continue
        tgt = item.primary
        target_path = tgt.nuke if which == 'package' else tgt.relink_nuke
        target_dir = tgt.dir if which == 'package' else tgt.relink_dir
        if item.kind in (MEDIA, FONT) and item.relink_knob and item.knob:
            color = None
            if mark and item.kind == MEDIA:
                color = COLOR_DUPLICATE if item.status == ST_DUPLICATE else COLOR_PACKED
            spec.ops.append(KnobOp(item.node, item.knob, value_for(target_path), color))
        elif item.kind == FONT and target_dir not in font_dirs:
            font_dirs.append(target_dir)
        elif item.kind == OCIO:
            spec.root_ops['customOCIOConfigPath'] = tcl_from_script(target_path)
            spec.root_ops['OCIO_config'] = 'custom'
    if font_dirs:
        spec.root_ops['free_type_font_path'] = tcl_from_script(font_dirs[0])
        if len(font_dirs) > 1:
            spec.warnings.append('Fonts were packed into several folders, the project font path '
                                 'points to the first one only: {}'.format(font_dirs[0]))
    return spec
