"""Checks that can run in the GUI before anything is sent to the farm."""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, Tuple

from . import settings as settings_mod, templates

# tokens that only exist per file/node on the farm
DYNAMIC_TOKENS = ('category', 'node', 'node_class', 'knob', 'clean_name', 'extension', 'font', 'class')


def all_templates(cfg: Mapping[str, Any]) -> List[Tuple[str, str]]:
    """Every path template in the settings as (label, template)."""
    out: List[Tuple[str, str]] = []
    ns = cfg.get('nuke_scripts') or {}
    if (ns.get('source') or {}).get('copy', True):
        out.append(('Source script', ns['source'].get('path', '')))
    for which in ('package', 'target'):
        sec = ns.get(which) or {}
        if not sec.get('copy', True):
            continue
        out.append(('{} script'.format(which.capitalize()), sec.get('path', '')))
        if which == 'target' and sec.get('path_relink'):
            out.append(('Target script (at target place)', sec.get('path_relink', '')))
        if sec.get('relative') and sec.get('relative_custom_project'):
            out.append(('{} project dir'.format(which.capitalize()), sec.get('relative_custom_project_template', '')))
    for cname, cat in settings_mod.media_categories(cfg).items():
        p = cat.get('path') or {}
        out.append(('Category {}'.format(cname), templates.join_template(p.get('root_template', ''), p.get('top_folder', ''))))
        out.append(('Category {} (relink)'.format(cname),
                    templates.join_template(p.get('root_template_relink', ''), p.get('top_folder_relink', ''))))
    for kind in settings_mod.SPECIAL_CATEGORIES:
        sec = settings_mod.special(cfg, kind)
        if not sec.get('enabled', True):
            continue
        out.append((kind.capitalize(), templates.join_template(sec.get('root_template', ''), sec.get('top_folder', ''))))
        out.append(('{} (relink)'.format(kind.capitalize()),
                    templates.join_template(sec.get('root_template_relink', ''), sec.get('top_folder_relink', ''))))
    return out


def dynamic_tokens(cfg: Mapping[str, Any]) -> Dict[str, str]:
    """Placeholder values for tokens that are only known on the farm."""
    dyn = {k: '<{}>'.format(k) for k in DYNAMIC_TOKENS}
    for cat in (cfg.get('categories') or {}).values():
        for flt in cat.get('filters') or []:
            if flt.get('token_name'):
                dyn.setdefault(flt['token_name'], '<{}>'.format(flt['token_name']))
    return dyn


def check_templates(cfg: Mapping[str, Any], tokens: Mapping[str, Any]) -> List[str]:
    """Templates that can't be filled from ``tokens`` (+ farm-only tokens)."""
    tok = dict(dynamic_tokens(cfg))
    tok.update(tokens)
    problems = []
    for label, tpl in all_templates(cfg):
        missing = templates.missing_tokens(tpl, tok)
        if missing:
            problems.append('{}: "{}" is missing {}'.format(label, tpl, ', '.join(missing)))
    return problems


def preview_paths(cfg: Mapping[str, Any], tokens: Mapping[str, Any]) -> List[Tuple[str, str, str, List[str]]]:
    """(label, template, resolved, missing) for every template - for the Places preview."""
    tok = dict(dynamic_tokens(cfg))
    tok.update(tokens)
    out = []
    for label, tpl in all_templates(cfg):
        missing = templates.missing_tokens(tpl, tok)
        out.append((label, tpl, templates.format_template(tpl, tok, strict=False), missing))
    return out
