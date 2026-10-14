"""Pack plan: turn what was found in a Nuke script into a list of items, their categories,
target paths and copy tasks. Pure Python - the Nuke side only supplies a ``ScanResult``.

    ScanResult  --build_plan()-->  PackPlan  --(copier)-->  results  --(relink)--> scripts
"""
from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from . import paths, sequences, settings as settings_mod, templates
from .filters import match_category

# item kinds
MEDIA, FONT, GIZMO, OCIO = 'media', 'font', 'gizmo', 'ocio'

# item status
ST_OK = 'ok'                    # will be / was packed
ST_MISSING = 'missing'          # no file found on disk
ST_UNCATEGORIZED = 'uncategorized'  # no category matched - left pointing at the original path
ST_SKIPPED = 'skipped'          # deliberately not packed (disabled, write node, setting off)
ST_DUPLICATE = 'duplicate'      # same files as another item, relinked to that item's copy
ST_ERROR = 'error'


# ------------------------------------------------------------------ scan records (from Nuke)

@dataclass
class ScannedFile:
    node: str
    node_class: str
    knob: str
    raw: str                 # knob value as typed
    path: str                # evaluated, absolute pattern (may contain %04d, ####, %V)
    disabled: bool = False
    disconnected: bool = False
    in_gizmo: bool = False
    project_relative: bool = False
    is_font: bool = False
    info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScannedFont:
    node: str
    node_class: str
    knob: str
    family: str = ''
    style: str = ''
    path: str = ''           # resolved font file ('' = could not resolve)
    index: Optional[int] = None
    disabled: bool = False
    disconnected: bool = False


@dataclass
class ScannedGizmo:
    node: str
    node_class: str
    path: str = ''           # .gizmo file ('' = not found on the plugin path)
    disabled: bool = False
    disconnected: bool = False


@dataclass
class OcioInfo:
    color_management: str = ''
    config: str = ''         # OCIO_config knob value
    config_path: str = ''    # custom config file actually used ('' = built-in config)
    from_env: bool = False


@dataclass
class ScanResult:
    files: List[ScannedFile] = field(default_factory=list)
    fonts: List[ScannedFont] = field(default_factory=list)
    gizmos: List[ScannedGizmo] = field(default_factory=list)
    ocio: OcioInfo = field(default_factory=OcioInfo)
    plugins: List[str] = field(default_factory=list)
    views: List[str] = field(default_factory=list)


# ------------------------------------------------------------------ plan

@dataclass
class Target:
    category: str
    dir: str            # folder in the package
    relink_dir: str     # folder at the target place
    nuke: str           # path to put in the knob (package script)
    relink_nuke: str    # path to put in the knob (target script)


@dataclass
class PackItem:
    id: int
    kind: str
    node: str = ''
    node_class: str = ''
    knob: str = ''
    source: str = ''                    # absolute source pattern
    files: List[str] = field(default_factory=list)
    sizes: List[int] = field(default_factory=list)
    frames: List[int] = field(default_factory=list)
    rel_files: List[str] = field(default_factory=list)  # OCIO: paths relative to the copied folder
    disabled: bool = False
    disconnected: bool = False
    info: str = ''
    status: str = ST_OK
    reason: str = ''
    categories: List[str] = field(default_factory=list)
    tokens: Dict[str, str] = field(default_factory=dict)
    targets: List[Target] = field(default_factory=list)
    duplicate_of: Optional[int] = None
    hashes: List[Optional[str]] = field(default_factory=list)
    copy_status: str = ''               # copied | skipped | partial | error
    errors: List[str] = field(default_factory=list)
    in_gizmo: bool = False
    relink_knob: bool = True            # False: nothing to write back into a knob (FreeType fonts, gizmos)

    @property
    def total_size(self) -> int:
        return sum(self.sizes)

    @property
    def primary(self) -> Optional[Target]:
        return self.targets[0] if self.targets else None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['total_size'] = self.total_size
        return d


@dataclass
class CopyEntry:
    src: str
    dst: str
    size: int
    item_ids: List[int] = field(default_factory=list)


@dataclass
class PackPlan:
    items: List[PackItem] = field(default_factory=list)
    copies: List[CopyEntry] = field(default_factory=list)
    plugins: List[str] = field(default_factory=list)
    ocio: OcioInfo = field(default_factory=OcioInfo)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def item(self, item_id: int) -> PackItem:
        return self.items[item_id]

    def to_dict(self) -> Dict[str, Any]:
        return {
            'items': [i.to_dict() for i in self.items],
            'copies': [asdict(c) for c in self.copies],
            'plugins': list(self.plugins),
            'ocio': asdict(self.ocio),
            'errors': list(self.errors),
            'warnings': list(self.warnings),
        }


def _color_info(info: Mapping[str, Any]) -> str:
    parts = []
    if info.get('transform_type') == 'display' and (info.get('display') or info.get('view')):
        parts.append('{}:{}'.format(info.get('display'), info.get('view')))
    elif info.get('colorspace'):
        parts.append(str(info['colorspace']))
    if info.get('raw'):
        parts.append('raw')
    if info.get('read_range'):
        parts.append('range {}'.format(info['read_range']))
    return '; '.join(parts)


class _Builder:
    def __init__(self, scan: ScanResult, cfg: Mapping[str, Any], tokens: Mapping[str, Any]):
        self.scan = scan
        self.cfg = cfg
        self.tokens = dict(tokens)
        self.plan = PackPlan(plugins=list(scan.plugins), ocio=scan.ocio)
        self._dst_owner: Dict[str, str] = {}   # dst (lower) -> src
        self._copy_index: Dict[str, int] = {}  # dst (lower) -> index into plan.copies

    # -------------------------------------------------------------- helpers
    def new_item(self, kind: str, **kw) -> PackItem:
        item = PackItem(id=len(self.plan.items), kind=kind, **kw)
        self.plan.items.append(item)
        return item

    def fmt(self, template: str, extra: Mapping[str, Any]) -> str:
        tok = dict(self.tokens)
        tok.update(extra)
        return paths.norm(templates.format_template(template, tok, strict=True))

    def add_copy(self, item: PackItem, src: str, dst: str, size: int) -> bool:
        key = dst.lower()
        owner = self._dst_owner.get(key)
        if owner is not None and paths.norm(owner).lower() != paths.norm(src).lower():
            item.errors.append('Target collision: {} would overwrite the copy of {}'.format(dst, owner))
            return False
        if owner is None:
            self._dst_owner[key] = src
            self._copy_index[key] = len(self.plan.copies)
            self.plan.copies.append(CopyEntry(src, dst, size, [item.id]))
        else:
            entry = self.plan.copies[self._copy_index[key]]
            if item.id not in entry.item_ids:
                entry.item_ids.append(item.id)
        return True

    def shared_target(self, section: Mapping[str, Any], category: str, extra: Mapping[str, Any],
                      name: str) -> Target:
        root = self.fmt(section.get('root_template', ''), extra)
        root_r = self.fmt(section.get('root_template_relink', ''), extra)
        top = self.fmt(section.get('top_folder', ''), extra) if section.get('top_folder') else ''
        top_r = self.fmt(section.get('top_folder_relink', ''), extra) if section.get('top_folder_relink') else ''
        d = templates.join_template(root, top)
        dr = templates.join_template(root_r, top_r)
        return Target(category, d, dr, d + '/' + name, dr + '/' + name)

    # -------------------------------------------------------------- media
    def build_media(self) -> None:
        cfg = self.cfg
        categories = settings_mod.media_categories(cfg) or {'default': settings_mod.DEFAULT_CATEGORY}
        packing = cfg.get('packing') or {}
        first_only = packing.get('category_match') == 'first'
        include_writes = bool(packing.get('include_write_nodes'))
        by_key: Dict[str, int] = {}

        for sf in self.scan.files:
            if sf.is_font:
                continue
            item = self.new_item(
                MEDIA, node=sf.node, node_class=sf.node_class, knob=sf.knob, source=paths.norm(sf.path),
                disabled=sf.disabled, disconnected=sf.disconnected, info=_color_info(sf.info),
                in_gizmo=sf.in_gizmo)

            if sf.node_class in settings_mod.WRITE_CLASSES and not include_writes:
                item.status, item.reason = ST_SKIPPED, 'output node ({})'.format(sf.node_class)
                continue

            key = item.source.lower()
            if key in by_key:
                prim = self.plan.items[by_key[key]]
                self._copy_from_primary(item, prim)
                continue
            by_key[key] = item.id

            res = sequences.resolve_files(item.source, self.scan.views)
            item.files, item.sizes, item.frames = res.files, res.sizes, res.frames
            if not res.files:
                item.status, item.reason = ST_MISSING, 'no files found for {}'.format(item.source)
                continue

            first = res.files[0]
            subject = {
                'File Name': paths.basename(first),
                'File Path': first,
                'Node Class': sf.node_class,
                'Knob Name': sf.knob,
            }
            reasons = set()
            for cname, cat in categories.items():
                ok, cat_tokens, reason = match_category(cat, subject, sf.disabled, sf.disconnected)
                if not ok:
                    if reason:
                        reasons.add(reason)
                    continue
                item.categories.append(cname)
                item.tokens.update(cat_tokens)
                if first_only:
                    break
            if not item.categories:
                if reasons & {'disabled', 'disconnected'} and 'filters' not in reasons:
                    item.status, item.reason = ST_SKIPPED, ' / '.join(sorted(reasons))
                else:
                    item.status, item.reason = ST_UNCATEGORIZED, 'no category matched'
                continue

            pattern_name = paths.basename(item.source)
            extra_base = dict(item.tokens)
            extra_base.update({
                'node': item.node, 'node_class': item.node_class, 'knob': item.knob,
                'clean_name': sequences.clean_name(pattern_name),
                'extension': os.path.splitext(pattern_name)[1].lstrip('.').lower(),
            })
            try:
                for cname in item.categories:
                    cat = categories[cname]
                    p = cat.get('path') or settings_mod.DEFAULT_CATEGORY['path']
                    extra = dict(extra_base, category=cname)
                    item.targets.append(self.shared_target(p, cname, extra, pattern_name))
            except templates.TemplateError as e:
                item.status, item.reason = ST_ERROR, str(e)
                item.errors.append(str(e))
                item.targets = []
                continue

            for tgt in item.targets:
                for f, size in zip(item.files, item.sizes):
                    self.add_copy(item, f, tgt.dir + '/' + paths.basename(f), size)
            if item.errors:
                item.status, item.reason = ST_ERROR, item.errors[0]

    def _copy_from_primary(self, item: PackItem, prim: PackItem) -> None:
        item.duplicate_of = prim.id
        item.files, item.sizes, item.frames = prim.files, prim.sizes, prim.frames
        item.categories, item.tokens, item.targets = prim.categories, prim.tokens, prim.targets
        item.status = ST_DUPLICATE if prim.status == ST_OK else prim.status
        item.reason = 'same files as node {}'.format(prim.node) if prim.status == ST_OK else prim.reason

    def finalize_duplicates(self) -> None:
        """Duplicates were linked before the primary finished; refresh them."""
        for item in self.plan.items:
            if item.duplicate_of is not None:
                self._copy_from_primary(item, self.plan.items[item.duplicate_of])

    # -------------------------------------------------------------- fonts / gizmos
    def _single_file_kind(self, kind: str, section: Mapping[str, Any], node: str, node_class: str,
                          knob: str, path: str, disabled: bool, disconnected: bool, info: str,
                          by_path: Dict[str, int], extra: Dict[str, Any], relink_knob: bool) -> None:
        item = self.new_item(kind, node=node, node_class=node_class, knob=knob, source=paths.norm(path),
                             disabled=disabled, disconnected=disconnected, info=info,
                             relink_knob=relink_knob)
        if not section.get('enabled', True):
            item.status, item.reason = ST_SKIPPED, '{} packing disabled in settings'.format(kind)
            return
        if not item.source:
            item.status, item.reason = ST_MISSING, 'file could not be resolved'
            return
        if section.get('skip_disabled') and disabled:
            item.status, item.reason = ST_SKIPPED, 'disabled'
            return
        if section.get('skip_disconnected') and disconnected:
            item.status, item.reason = ST_SKIPPED, 'disconnected'
            return
        key = item.source.lower()
        if key in by_path:
            self._copy_from_primary(item, self.plan.items[by_path[key]])
            return
        by_path[key] = item.id
        if not os.path.isfile(item.source):
            item.status, item.reason = ST_MISSING, 'file not found'
            return
        item.files = [item.source]
        item.sizes = [os.path.getsize(item.source)]
        item.categories = [kind]
        name = paths.basename(item.source)
        extra = dict(extra, node=node, node_class=node_class, clean_name=name,
                     category={FONT: 'fonts', GIZMO: 'gizmos'}.get(kind, kind))
        try:
            tgt = self.shared_target(section, kind, extra, name)
        except templates.TemplateError as e:
            item.status, item.reason = ST_ERROR, str(e)
            item.errors.append(str(e))
            return
        item.targets = [tgt]
        self.add_copy(item, item.source, tgt.nuke, item.sizes[0])
        if item.errors:
            item.status, item.reason = ST_ERROR, item.errors[0]

    def build_fonts(self) -> None:
        section = settings_mod.special(self.cfg, 'fonts')
        by_path: Dict[str, int] = {}
        for sf in self.scan.files:
            if sf.is_font:
                self._single_file_kind(FONT, section, sf.node, sf.node_class, sf.knob, sf.path,
                                       sf.disabled, sf.disconnected, 'font file', by_path, {'font': ''}, True)
        for f in self.scan.fonts:
            info = ', '.join(str(x) for x in (f.family, f.style, f.index) if x not in (None, ''))
            self._single_file_kind(FONT, section, f.node, f.node_class, f.knob, f.path, f.disabled,
                                   f.disconnected, info, by_path, {'font': f.family}, False)

    def build_gizmos(self) -> None:
        section = settings_mod.special(self.cfg, 'gizmos')
        by_path: Dict[str, int] = {}
        for g in self.scan.gizmos:
            self._single_file_kind(GIZMO, section, g.node, g.node_class, '', g.path, g.disabled,
                                   g.disconnected, '', by_path, {'class': g.node_class}, False)

    # -------------------------------------------------------------- OCIO
    def build_ocio(self) -> None:
        section = settings_mod.special(self.cfg, 'ocio')
        o = self.scan.ocio
        info = 'color_management={}; config={}; path={}{}'.format(
            o.color_management, o.config, o.config_path, ' (from $OCIO)' if o.from_env else '')
        item = self.new_item(OCIO, node='root', node_class='Root', knob='customOCIOConfigPath',
                             source=paths.norm(o.config_path), info=info, relink_knob=False)
        if not o.config_path:
            item.status, item.reason = ST_SKIPPED, 'no custom OCIO config'
            return
        if not section.get('enabled', True):
            item.status, item.reason = ST_SKIPPED, 'OCIO packing disabled in settings'
            return
        if not os.path.isfile(item.source):
            item.status, item.reason = ST_MISSING, 'OCIO config not found'
            return
        cfg_dir = paths.dirname(item.source)
        base = paths.dirname(cfg_dir)  # keep the config folder name in the package
        max_files = int(section.get('max_files', 5000) or 0)
        files: List[str] = []
        for d, _dirs, names in os.walk(cfg_dir):
            for n in names:
                files.append(paths.norm(os.path.join(d, n)))
                if max_files and len(files) > max_files:
                    item.status = ST_ERROR
                    item.reason = ('OCIO config folder {} has more than {} files - refusing to copy it '
                                   '(raise ocio.max_files if intended)'.format(cfg_dir, max_files))
                    item.errors.append(item.reason)
                    return
        files.sort()
        item.files = files
        item.sizes = [os.path.getsize(f) for f in files]
        item.rel_files = [paths.relpath(f, base) or paths.basename(f) for f in files]
        item.categories = [OCIO]
        try:
            tgt = self.shared_target(section, OCIO, {'category': OCIO}, paths.relpath(item.source, base) or '')
        except templates.TemplateError as e:
            item.status, item.reason = ST_ERROR, str(e)
            item.errors.append(str(e))
            return
        item.targets = [tgt]
        for f, rel, size in zip(files, item.rel_files, item.sizes):
            self.add_copy(item, f, tgt.dir + '/' + rel, size)
        if item.errors:
            item.status, item.reason = ST_ERROR, item.errors[0]

    def build(self) -> PackPlan:
        self.build_media()
        self.build_fonts()
        self.build_gizmos()
        self.build_ocio()
        self.finalize_duplicates()
        for item in self.plan.items:
            for e in item.errors:
                self.plan.errors.append('{} {}: {}'.format(item.kind, item.node, e))
            if item.status == ST_MISSING:
                self.plan.warnings.append('{} {} ({}): {}'.format(item.kind, item.node, item.knob, item.reason))
            if item.in_gizmo and item.status == ST_OK and not settings_mod.special(self.cfg, 'gizmos').get('to_groups'):
                self.plan.warnings.append(
                    'node {} is inside a gizmo: its file is copied but the relink will not persist '
                    '(enable "convert gizmos to groups" in the gizmos category)'.format(item.node))
        return self.plan


def build_plan(scan: ScanResult, cfg: Mapping[str, Any], tokens: Mapping[str, Any]) -> PackPlan:
    """Build the pack plan. ``cfg`` must be a complete settings dict."""
    return _Builder(scan, cfg, tokens).build()


def apply_copy_results(plan: PackPlan, results) -> None:
    """Fold copier results (same order as ``plan.copies``) back into the items."""
    per_item: Dict[int, List[str]] = {}
    for entry, res in zip(plan.copies, results):
        for iid in entry.item_ids:
            per_item.setdefault(iid, []).append(res.status)
            item = plan.items[iid]
            if res.status == 'error':
                item.errors.append('copy {} -> {}: {}'.format(entry.src, entry.dst, res.error))
        if res.hash:
            for iid in entry.item_ids:
                item = plan.items[iid]
                if item.duplicate_of is None:
                    try:
                        idx = item.files.index(entry.src)
                    except ValueError:
                        continue
                    if not item.hashes:
                        item.hashes = [None] * len(item.files)
                    item.hashes[idx] = res.hash
    for iid, statuses in per_item.items():
        item = plan.items[iid]
        if all(s == 'skipped' for s in statuses):
            item.copy_status = 'skipped'
        elif 'error' in statuses:
            item.copy_status = 'error' if all(s == 'error' for s in statuses) else 'partial'
            item.status = ST_ERROR
            item.reason = item.errors[0] if item.errors else 'copy failed'
        else:
            item.copy_status = 'copied'
    # duplicates mirror their primary
    for item in plan.items:
        if item.duplicate_of is not None:
            prim = plan.items[item.duplicate_of]
            item.copy_status = prim.copy_status
            if prim.status == ST_ERROR:
                item.status, item.reason = ST_ERROR, prim.reason
