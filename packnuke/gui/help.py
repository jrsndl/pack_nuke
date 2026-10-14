"""Tooltip texts (simple in-app help), in one place.

``button()`` and ``label()`` in widgets.py look their text up here when no explicit tip is
given; tabs call :func:`apply` for input fields.
"""
from __future__ import annotations

from typing import Iterable, Tuple

TIPS = {
    # ---------------------------------------------------------------- tabs
    'tab:Get Nuke Scripts': 'Find Nuke scripts on disk, filter them and send them to the Queue.',
    'tab:Queue': 'Scripts that will be packed, their tokens, and the package / Deadline submission.',
    'tab:Places': 'Edit the places (studios) and preview where every file of a package will go.',
    'tab:Settings': 'settings.json: executables, Deadline job, packing options and all raw settings.',
    'tab:Presets': 'Save and load named snapshots of the search, filters, places and settings file.',
    'tab:Log': 'Everything the application reports, filterable by level.',

    # ---------------------------------------------------------------- Get Nuke Scripts
    'Search root:': 'Folder searched (recursively) for *.nk files. Enter starts the search.',
    'Search': 'Find every *.nk under the search root. Filters below then work on that list without '
              'searching again.',
    'Stop': 'Stop the running search (Ctrl+.). Rows found so far are kept.',
    'Skip folders:': 'Folder names that are never entered, separated by ";". Wildcards allowed '
                     '(e.g. render;plates;.*). Skipping large render/plate folders is the best speed-up.',
    'Max depth:': 'How many folder levels below the search root are searched. "unlimited" = all.',
    'Parallel:': 'Folders listed at the same time. auto = 1 on local disks, 16 on network shares.',
    'Search for:': 'File name patterns, separated by ";" (e.g. *_comp_v???.nk). Case-insensitive.',
    'Only if contains:': 'Keep only scripts whose full path contains this text (case-insensitive). '
                         'Several alternatives: a;b.',
    'Version regex:': 'Regular expression matched against the file name; group 1 is the version '
                      '(e.g. .*_v(\\d{3})\\.nk). Empty = no versions, every script is kept.',
    'First versions:': 'Keep the first N versions of every folder.',
    'Last versions:': 'Keep the last N versions of every folder. Can be combined with First versions.',
    'Mark all': 'Mark every row in the table.',
    'Mark none': 'Unmark every row in the table.',
    'Mark selected': 'Mark the highlighted rows (click, Shift+click, Ctrl+click to highlight).',
    'Unmark selected': 'Unmark the highlighted rows.',
    'Toggle selected': 'Flip the mark of the highlighted rows (Space).',
    'Send marked to Queue  →': 'Add the marked scripts to the Queue tab (scripts already there are skipped).',
    'scripts_table': 'Found scripts. Checkbox = marked. Double click opens the folder; right click for more. '
                     'Click a header to sort.',

    # ---------------------------------------------------------------- Queue
    'queue_table': 'Scripts to pack. Only marked rows are packed. Del removes the highlighted rows. '
                   'Tokens column = tags parsed from the script path.',
    'Remove selected': 'Remove the highlighted rows from the queue (Del).',
    'Clear queue': 'Remove every script from the queue.',
    'Inspector': 'Show / hide the token inspector. Drag the splitter to resize it.',
    'Script path tags only': 'Show only the tags parsed from the script path, not all tokens.',
    'inspector_table': 'All tokens of the highlighted script, as used in templates ({SHOT}, {project[name]} ...). '
                       'Bold = parsed from the script path. Ctrl+C copies.',
    'Source place:': 'Place the scripts come from. Its anatomy and script path tags fill the tokens.',
    '→  Target place:': 'Place receiving the package.',
    '⇄': 'Swap source and target place.',
    'Job root:': 'Folder where the package folder is created. Comes from settings job.job_root.',
    'Auto': 'Go back to the value computed from the settings.',
    'Job name:': 'Package folder name. Comes from settings job.job_name_default and is checked '
                 'against job.job_name_check.',
    'New timestamp': 'Use the current time for {timestamp} (job name, tokens).',
    'Job folder:': 'Full package folder = job root / job name. Available as {job} in templates.',
    'Check': 'Validate settings, places, job name, template tokens of every marked script and the '
             'executables, without writing anything.',
    'Write job files only': 'Create the package folder with _pack_nuke/settings.json, job.json and '
                            'nuke_files.csv, without submitting.',
    'Run first locally': 'Write the job files and pack the first marked script on this machine '
                         '(nuke -t). Output goes to the Log tab.',
    'Send to Deadline': 'Write the job files and submit one Deadline job per marked script.',

    # ---------------------------------------------------------------- Places
    'Places': 'Places defined in settings.json. Double click to rename.',
    'Add': 'Create a new, empty place.',
    'Duplicate': 'Copy the selected place under a new name.',
    'Rename': 'Rename the selected place.',
    'Delete': 'Delete the selected item.',
    'Use as source': 'Make the selected place the source place (Queue tab).',
    'Use as target': 'Make the selected place the target place (Queue tab).',
    'anatomy_table': 'Tokens of this place. Nested keys use dots: project.name is used as {project[name]}. '
                     'Ctrl+C / Ctrl+V copy rows (also between places), Del removes.',
    'Add row': 'Add an anatomy key.',
    'Remove rows': 'Remove the highlighted anatomy rows (Del).',
    'Copy rows': 'Copy the highlighted rows (all rows if none highlighted) to the clipboard (Ctrl+C).',
    'Paste rows': 'Paste rows from the clipboard into this place; same keys are overwritten (Ctrl+V).',
    'Copy to place ▾': 'Copy the highlighted rows (or all rows) directly into another place.',
    'Use script path tags for this place': 'Parse extra tokens ({SHOT}, {TASK} ...) from each Nuke script path.',
    'tags_table': 'Name = token name. Source = file name or full path. Search = regex. Replace = result '
                  'using group references like \\1 (empty = group 1). Lower/Upper change case. '
                  'Preview = result for the preview script.',
    'Add tag': 'Add a script path tag.',
    'Remove': 'Remove the highlighted tags (Del).',
    'Up': 'Move the current tag up (later tags win when names repeat).',
    'Down': 'Move the current tag down.',
    'Copy tags': 'Copy the highlighted tags (all if none highlighted) to the clipboard (Ctrl+C).',
    'Paste tags': 'Paste tags from the clipboard; tags with the same name are replaced (Ctrl+V).',
    'preview_tree': 'Every output path resolved for the preview script. Red = missing tokens (hover for details). '
                    '<node>, <category> ... are only known on the farm.',
    'Refresh': 'Refresh the list.',

    # ---------------------------------------------------------------- Settings
    'Settings file:': 'Where the settings come from: a loaded preset (settings embedded in it) or a settings.json. '
                      'They are copied into every package.',
    'Load': 'Load the settings from the file (a settings.json or a preset). Unsaved changes are lost (you are asked first).',
    'Save': 'Save the current settings (Ctrl+S) - into the loaded preset, or into the settings.json file.',
    'Save as...': 'Save the current settings as a plain settings.json file.',
    'Open in editor': 'Open settings.json in the default editor (use Load afterwards).',
    'Expand all': 'Expand every section.',
    'Collapse all': 'Collapse every section.',
    'Validate': 'Check the settings for errors and likely typos.',
    'Pool:': 'Deadline pool for the packing jobs.',
    'Group:': 'Deadline group (machines allowed to pack).',
    'Priority:': 'Deadline job priority (0-100).',
    'Department:': 'Deadline department field.',
    'Limit groups:': 'Deadline limits, comma separated.',
    'Comment:': 'Deadline job comment.',
    'Copy threads:': 'Files copied in parallel by each farm job.',
    'json_tree': 'All settings. Double click a value to edit it; the type (true/false, number, text) is kept.',

    # ---------------------------------------------------------------- Presets
    'Presets folder:': 'Folder holding presets (stored in settings.ini as presets_folder). '
                       'Point several artists to the same folder to share presets.',
    'Open': 'Open the folder in the file browser.',
    'Presets': 'Saved presets. Double click loads.',
    'Preset content': 'What the selected preset contains.',
    'Name:': 'Name of the preset to save (an existing name is overwritten after confirmation).',
    'Save preset': 'Save the complete settings plus the current search, filters and places as a preset.',
    'Default source place:': 'Source place selected automatically when settings are loaded.',

    # ---------------------------------------------------------------- Log
    'Show level:': 'Minimum level shown. Debug shows everything.',
    'Auto scroll': 'Keep the newest message visible.',
    'Clear': 'Remove all messages from the view.',
    'Save...': 'Save the shown messages to a text file.',
    'log_filter': 'Show only messages containing this text.',
}


def tip(key: str) -> str:
    return TIPS.get(key, '')


def apply(pairs: Iterable[Tuple[object, str]]) -> None:
    """Set tooltips ``[(widget, key), ...]`` where the widget has none yet."""
    for widget, key in pairs:
        text = TIPS.get(key, key if ' ' in key else '')
        if text and not widget.toolTip():
            widget.setToolTip(text)
