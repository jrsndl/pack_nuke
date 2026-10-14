"""Per-script packing report (CSV for spreadsheets, JSON with everything)."""
from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict, List, Mapping, Optional

from . import sequences
from .copier import combined_hash, human_size
from .plan import PackPlan

COLUMNS = [
    'type', 'status', 'reason', 'copy_status', 'categories', 'info', 'node_class', 'node_name', 'knob',
    'file_name', 'extension', 'file_number', 'frames', 'size', 'size_human', 'node_disabled',
    'node_disconnected', 'source', 'package_path', 'relink_path', 'file_hash', 'hash_for_all',
    'duplicate_of', 'place_source', 'place_target', 'timestamp',
]


def report_rows(plan: PackPlan, tokens: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for item in plan.items:
        file_name = item.source.rsplit('/', 1)[-1] if item.source else ''
        hashes = item.hashes or []
        dup = plan.items[item.duplicate_of].node if item.duplicate_of is not None else ''
        rows.append({
            'type': item.kind,
            'status': item.status,
            'reason': item.reason,
            'copy_status': item.copy_status,
            'categories': ', '.join(item.categories),
            'info': item.info,
            'node_class': item.node_class,
            'node_name': item.node,
            'knob': item.knob,
            'file_name': file_name,
            'extension': file_name.rsplit('.', 1)[-1] if '.' in file_name else '',
            'file_number': len(item.files),
            'frames': sequences.frame_ranges(item.frames),
            'size': item.total_size,
            'size_human': human_size(item.total_size),
            'node_disabled': item.disabled,
            'node_disconnected': item.disconnected,
            'source': item.source,
            'package_path': item.primary.nuke if item.primary else '',
            'relink_path': item.primary.relink_nuke if item.primary else '',
            'file_hash': hashes[0] if len(hashes) == 1 and hashes[0] else '',
            'hash_for_all': combined_hash(hashes) if len(hashes) > 1 else '',
            'duplicate_of': dup,
            'place_source': tokens.get('place_source', ''),
            'place_target': tokens.get('place_target', ''),
            'timestamp': tokens.get('timestamp', ''),
        })
    for plugin in plan.plugins:
        row = {c: '' for c in COLUMNS}
        row.update({'type': 'plugin', 'status': 'info', 'info': plugin, 'source': plugin,
                    'timestamp': tokens.get('timestamp', '')})
        rows.append(row)
    return rows


def write_report(folder: str, row_id: str, plan: Optional[PackPlan], tokens: Mapping[str, Any],
                 summary: Mapping[str, Any]) -> Dict[str, str]:
    """Write ``<row_id>.csv`` and ``<row_id>.json`` into ``folder``. Returns the paths."""
    os.makedirs(folder, exist_ok=True)
    csv_path = os.path.join(folder, row_id + '.csv').replace('\\', '/')
    json_path = os.path.join(folder, row_id + '.json').replace('\\', '/')
    rows = report_rows(plan, tokens) if plan else []
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, COLUMNS)
        w.writeheader()
        w.writerows(rows)
    data = {
        'summary': dict(summary),
        'tokens': dict(tokens),
        'plan': plan.to_dict() if plan else None,
    }
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    return {'csv': csv_path, 'json': json_path}
