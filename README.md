# Pack Nuke

Pack Nuke collects and relinks every file a Nuke script needs so the script works at
another place (studio to studio exchange). Packing runs on the Deadline farm, one job per script.

1. **GUI** (`pack_nuke_gui.py`). Finds Nuke scripts, builds a queue, previews output paths and
   writes the package job files. Then it submits to Deadline.
2. **Farm job** (`pack_nuke.py`, runs in `nuke -t`). Opens one script and builds a pack plan.
   It copies the files, saves relinked scripts and writes a report.

## Requirements

* GUI: Python 3.9+ with PySide6 (`pip install PySide6`).
* Farm: Nuke 13+ (Python 3.9+). Deadline's `deadlinecommand` must be reachable from the GUI machine.

## Code layout

```
pack_nuke.py            farm entry point  (nuke -t pack_nuke.py --job-dir <pkg>/_pack_nuke --id <id>)
pack_nuke_gui.py        GUI entry point
settings.json           example settings (schema_version 2)
settings.ini            GUI state, incl. presets_folder
packnuke/
  core/                 pure Python, no Nuke, no Qt, unit tested
    sequences.py        %04d / #### / %V handling, exact frame matching
    templates.py        {token} and nested {project[name]} templates, strict on the farm
    tokens.py           anatomy + script path tags + job/script tokens
    filters.py          category filters and script path tags (None-safe)
    plan.py             scan -> pack plan (categories, targets, dedup, collisions)
    copier.py           parallel, atomic, skip-identical copy with optional hashing
    relink.py           what to write back into the package / target scripts
    report.py           per-script CSV + JSON report
    jobs.py             job.json / settings.json / nuke_files.csv in the package
    settings.py         defaults, migration, validation
    scanner.py          fast parallel *.nk search
    versions.py         name / contains / version regex / first-last N filtering
    preflight.py        template checks before submitting
  nuke_io/host.py       the only code importing nuke (scan + relink + gizmo->group)
  farm/pack_job.py      farm orchestration, exit codes
  farm/deadline.py      Deadline submission (no Qt; reusable from Ayon)
  gui/                  PySide6 tabs
tests/                  python -m unittest discover -s tests
```

## GUI

### Get Nuke Scripts

* **Search** scans the root once for every `*.nk` and shows rows as folders are found, with
  progress in the status bar. **Stop** or `Ctrl+.` stops it.
* **Skip folders** (`render;plates;.*`) and **Max depth** prune the walk. This is the biggest
  speed-up on production trees.
* **Parallel**: `auto` uses 1 thread on local disks and 16 on network shares. Network listings
  are latency bound, so parallel listing is many times faster.
* **Filters** never rescan the disk, so changing them is instant: *Search for* (name patterns,
  `;` separated), *Only if contains*, *Version regex* (group 1) and *First / Last N versions*
  per folder.
* Select several rows (Shift/Ctrl click), then use **Mark selected**, **Unmark selected** or
  **Toggle** (Space). The right-click menu has the same actions plus reveal and copy path.
* **Send marked to Queue** adds the marked scripts (no duplicates).

### Queue

* The scripts to pack, with their script path tags in the *Tokens* column. Rows can be
  marked/unmarked, removed (Del) or cleared.
* The **Inspector** side panel shows every token of the selected script, one per line. It is
  resizable and can be hidden.
* **Package** section:
  * Source and target place.
  * Job root and job name. Both come from settings by default and can be edited; **Auto**
    resets them.
  * **New timestamp** and a check of the job name against `job_name_check`.
  * **Check** validates settings, places, template tokens per script and executables.
  * **Write job files only** creates the package folder.
  * **Run first locally** packs the first script with the local Nuke and streams its output
    into the Log tab.
  * **Send to Deadline** submits one job per script under a shared batch name. The job and
    plugin info files are kept in `_pack_nuke/deadline/`.

### Places

* Add, duplicate, rename or delete places, and set the current source or target.
* **Anatomy** is a key/value table. Nested keys use dots (`project.name` becomes `{project[name]}`).
* **Script path tags** is a table with source, regex, replace (`\1`), lower and upper case.
  The *Preview* column shows each tag's value for the preview script.
* To copy rows between places, use **Copy rows / Paste rows** (`Ctrl+C` / `Ctrl+V`, also
  through the system clipboard) or **Copy to place ▾**.
* **Output path preview** resolves every template (job root/name/folder, scripts, categories,
  fonts, gizmos, OCIO) for the first selected Queue script. With an empty queue it uses the
  first selected script in Get Nuke Scripts. Missing tokens are highlighted; farm-only tokens
  show as `<node>`.

### Settings

Settings come from the **loaded preset**, with the settings embedded in it. When no preset has
been loaded, they come from `settings.json` in the app folder. The file field shows which one
is in use.

* **Save** (`Ctrl+S`) writes back into that preset, or into that file.
* **Save as...** writes a plain `settings.json`.
* **Load** accepts either a `settings.json` or a preset file.

The sub-tabs:

* **Farm & Misc**:
  * Nuke, deadlinecommand and the farm `pack_nuke.py` path per OS.
  * Deadline job options.
  * Packing options: copy threads, skip identical, hashes, category match, missing files, Write
    nodes, node colours, gizmos to groups.
* **Nuke Scripts**:
  * Turns each of the source, package and target scripts on or off.
  * Sets their paths, plus the target's path at the receiving place.
  * Sets relative linking: folders above the script, or a custom project directory.
  * Every path is shown resolved for the preview script, with missing tokens highlighted.
* **Categories**:
  * Add, duplicate, rename, delete and reorder categories.
  * **fonts**, **gizmos** and **ocio** are built-in categories. They always exist and their names
    can't change, and they have no filters, because the scan decides what they contain. Their
    folders and options can be edited: pack on/off, skip disabled/disconnected,
    *convert gizmos to groups* and the OCIO *relative path* / *max files*.
  * Set the package and relink folder templates, the skip disabled/disconnected options and
    AND/OR filter combination.
  * The filters table has source, regex, check list, token name and invert columns.
  * A **Test** box takes a file path, node class and knob, and shows each filter's hit/value,
    whether the category matches, and the resolved package and target folders.
* **All settings (JSON)**: every value, editable; types are preserved.
* **Validation**: errors and warnings, such as bad regexes and typos like `/1` or `{2-4}`.

### Presets

* `settings.ini` → `presets_folder` sets where presets are kept (default `./presets`). Use a
  shared folder to share them between artists.
* A preset always contains the **complete settings**, plus the search root, skip folders,
  depth, filters, version regex, first/last N and source/target place.
* Loading or saving a preset makes it the settings source, so the Settings tab saves into it.
* The last loaded preset is restored on start. The last session's search and filter fields
  are kept on top of it.
* Presets saved by the previous version only referenced a settings file. On load, that file's
  content is taken into the preset; press Save to keep it.
* **Default source place** is selected when settings are loaded.

### Log

All messages, filtered by minimum level and text, with colour per level. Messages can be
cleared or saved, and errors also show in the status bar. The GUI also writes a rotating
`pack_nuke_gui.log`.

## Package layout

```
<job root>/<job name>/
  _pack_nuke/
    settings.json      settings used for this package
    job.json           places, timestamp, every script with all its tokens (JSON, nested ok)
    nuke_files.csv     human readable index
    reports/<id>.csv   one row per item: status, reason, categories, frames, sizes, paths, hashes
    reports/<id>.json  summary (errors, warnings, written scripts, stats) + full plan
  ...                  everything else is defined by the category / fonts / gizmos / ocio templates
```

## Farm job

`nuke -t pack_nuke.py --job-dir <pkg>/_pack_nuke --id <id> [--dry-run] [--verbose]`

* It scans File_Knobs (any knob, not just `file`), FreeType fonts, gizmos, the OCIO config
  (`$OCIO` or custom) and plugins.
* Item status, as shown in the report:

  | Status | Meaning |
  |---|---|
  | `ok` | packed |
  | `duplicate` | same files as another node; relinked to that copy |
  | `missing` | no files on disk |
  | `uncategorized` | no category matched; left pointing at the original path |
  | `skipped` | disabled/disconnected per category options, or Write-type outputs |
  | `error` | something failed |

* Two different source files mapped to the same target file are reported as a collision
  instead of overwriting each other.
* Copying runs in parallel. Each file is written to a temporary name and renamed into place,
  so parallel jobs can share `_shared/fonts` and similar folders. Identical files are skipped,
  so re-running a job is cheap.
* Scripts written:
  * **source**: an untouched copy of the original.
  * **package**: relinked to the copies. Paths are relative to the script folder, N levels
    above it, or a custom project folder.
  * **target**: relinked to the `*_relink` locations, with relative paths computed from
    `path_relink`, where the script will live at the receiving place.
* Fonts are relinked through the project font path. OCIO goes through `customOCIOConfigPath`.
  Gizmos can be converted to groups, with inputs and outputs reconnected.
* The report is always written. The exit code is non-zero when anything failed, so the Deadline
  job shows the failure. Missing files fail the job only with `packing.fail_on_missing`.

## Settings (settings.json)

See the `_comment` keys in `settings.json`. Settings from the previous version are migrated
when loaded:

* The top-level `fonts` / `gizmos` / `ocio` sections become the built-in categories
  (schema 3).
* `"Full Path"` becomes `"File Path"`.
* `is_source` / `is_target` are removed.
* Missing sections get defaults.

Notable keys:

| key | meaning |
|---|---|
| `copy.threads`, `copy.skip_identical` | farm copy behaviour |
| `packing.category_match` | `all` (copy into every matching category) or `first` |
| `packing.include_write_nodes` | also pack files referenced by Write-type nodes (off by default) |
| `packing.fail_on_missing`, `packing.mark_nodes` | |
| `categories.ocio.max_files` | safety limit for copying the OCIO config folder |
| `nuke_scripts.<source/package/target>.copy` | which scripts to write |

## Tests

```
python -m unittest discover -s tests
```

* `test_core.py` covers the core modules.
* `test_pack.py` runs full packs end-to-end with a fake Nuke host (copy, relink, report,
  collisions, missing tokens, dry run, Deadline command).
* `test_gui_smoke.py` drives every GUI tab against a tiny fake PySide6, so it runs without a
  display. It is skipped when real PySide6 is installed.

## To do

* Multi-shot deduplication for each package. Today, media used in 10 Nuke scripts is copied
  once, because copies of identical files are skipped, but it is still scanned 10 times.
  The next step is a combined plan per package.
* An ingest script that compares the current Nuke script (say v10 from a vendor) with an old
  script (say v0 from the studio). It would copy v10 to the same folder as v0 and relink media
  already present in v0, matching by file extension, number of files in the sequence, and hashes.
* An option to skip packing files that "the other place" already has. This needs a manifest
  of the target place.
* Ayon integration, using `packnuke.core` and `packnuke.farm.deadline`.
