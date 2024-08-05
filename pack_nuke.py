import datetime
import glob
import hashlib
import logging
import os
import platform
import pprint
import re
import shutil
import subprocess
import time
import timeit

import nuke

def get_default_category() -> dict:
    """Get the default category if not specified by settings

    Returns:
         dict: Default category
    """
    default_category = {
        "default_category": {
            "path": {
                "root_template": "{job}/{folder[name]}/{category}",
                "root_template_relink": "{job}/{folder[name]}/{category}",
                "top_folder": "{node}",
                "top_folder_relink": "{node}"
            },
            "filter_options": {
                "skip_disconnected": True,
                "skip_disabled": True,
                "combine_filters": "AND"
            },
            "filters": [
                {
                    "source": "File Name",
                    "search": ".*\.(\w{2,4})$",
                    "check": [],
                    "token_name": "extension",
                    "invert": False
                }
            ]
        }
    }
    return default_category


def get_nuke_pack_project_settings() -> dict:
    """Get the project settings

    Returns:
         dict: all nuke pack project settings
    """

    # for testing only
    # TODO get project settings

    settings = \
        {"toVendor1": {
            "job": {
                "job_name_default": "PackNuke_{place_source}2{place_target}_{timestamp}",
                "job_name_check": "^PackNuke_(.+)2(.+)_(\d{6}_\d{4})_([-]?\d{4})[_]?(?:.*)$",
                "job_root": "{root[work]}/{project[name]}/out/packNuke/{place_source}2{place_target}"
            },
            "nuke_scripts": {
                "source": {
                    "copy": True,
                    "path": "{job}/{folder[name]}/{script_name}_source.nk"
                },
                "package": {
                    "copy": True,
                    "path": "{job}/{folder[name]}/{script_name}_check.nk",
                    "path_relink": "/vendor1_relink_root/{folder[name]}/nuke/{script_name}_check.nk",
                    "relative": True,
                    "relative_custom_project": False,
                    "relative_custom_project_template": "{job}",
                    "relative_above_script": 1
                },
                "target": {
                    "copy": True,
                    "path": "{job}/{folder[name]}/{script_name}_target.nk",
                    "path_relink": "/vendor1_relink_root/{folder[name]}/nuke/{script_name}_target.nk",
                    "relative": True,
                    "relative_custom_project": False,
                    "relative_custom_project_template": "{job}",
                    "relative_above_script": 2
                }
            },
            "hashes": {
                "hashes_generate": True
            },
            "places": {
                "studio": {
                    "long_name": "Great Studio",
                    "use_nuke_path": False,
                    "path_regex": "^.*\/(DP\d4_.*)\/.*$"
                },
                "vendor1": {
                    "long_name": "Amazing Vendor",
                    "use_nuke_path": False,
                    "path_regex": "^.*(projects).*$"
                }
            },
            "categories": {
                "test_category": {
                    "path": {
                        "root_template": "{job}/{folder[name]}/{category}",
                        "root_template_relink": "{job}/{folder[name]}/{category}",
                        "top_folder": "{clean_name}_{node}",
                        "top_folder_relink": "{clean_name}_{node}"
                    },
                    "filter_options": {
                        "skip_disconnected": True,
                        "skip_disabled": True,
                        "combine_filters": "OR"
                    },
                    "filters": [
                        {
                            "source": "File Name",
                            "search": ".*\.(\w{2,4})$",
                            "check": ["exr", "jpg", "jpeg", "mov"],
                            "token_name": "extension",
                            "invert": False
                        },
                        {
                            "source": "Full Path",
                            "search": ".*\/(v\d\d\d)\/.*",
                            "check": [],
                            "token_name": "version_from_path",
                            "invert": False
                        },
                        {
                            "source": "Node Class",
                            "search": "Read Write",
                            "check": [],
                            "token_name": "class_read_write",
                            "invert": False
                        }
                    ]
                }
            },
            "fonts": {
                "enabled": True,
                "root_template": "{job}/_shared",
                "root_template_relink": "/vendor1_relink_root/_shared",
                "top_folder": "fonts",
                "top_folder_relink": "fonts",
                "skip_disconnected": True,
                "skip_disabled": True
            },
            "gizmos": {
                "enabled": True,
                "to_groups": True,
                "root_template": "{job}/_shared",
                "root_template_relink": "/vendor1_relink_root/_shared",
                "top_folder": "gizmos",
                "top_folder_relink": "gizmos",
                "skip_disconnected": True,
                "skip_disabled": True
            },
            "ocio": {
                "enabled": True,
                "root_template": "{job}/_shared/ocio",
                "root_template_relink": "/vendor1_relink_root/_shared/ocio",
                "top_folder": "",
                "top_folder_relink": "",
                "subfolders": True,
                "relative": True
            }
        }
    }
    return settings


def get_anatomy() -> dict:
    """Get the folder anatomy

    Returns:
         dict: project anatomy of one folder
    """
    # for testing only
    # TODO get anatomy

    anatomy = {
        "root[work]": "z:",
        "root": {
            "work": "z:"
        },
        "studio[name]": "Dazzle",
        "studio[code]": "dzl",
        "user": "john.doe",
        "project": {
            "name": "T027_cgTests_Sept23",
            "code": "dp1234_prj",
        },
        "asset": "mw_119_12_0340",
        "folder": {
            "name": "mw_119_12_0340"
        },
        "hierarchy": "shots/114_23",
        "parent": "114_23",
        "task[name]": "comp",
        "task[type]": "Compositing",
        "task[short]": "comp",
        "app": "nuke",
        "d": "30",
        "dd": "26",
        "ddd": "Thu",
        "dddd": "Thursday",
        "m": "5",
        "mm": "07",
        "mmm": "May",
        "mmmm": "May",
        "yy": "24",
        "yyyy": "2024",
        "H": "10",
        "HH": "10",
        "h": "10",
        "hh": "10",
        "ht": "AM",
        "M": "23",
        "MM": "23",
        "S": "6",
        "SS": "06",
        "username": "john.doe",
        "family": "render",
        "subset": "renderCompMain",
        "version": 1,
        "resolution_width": 4096,
        "resolution_height": 2160,
        "pixel_aspect": 1.0,
        "fps": 25.0,
        "workfile": "path/to/workfile.nk"
    }
    return anatomy


def action_dialog():
    # for testing
    # TODO make action dialog, get use input, return anatomy for every workfile

    class Default(dict):
        def __missing__(self, key):
            return key

    def my_time():
        """
        Used for timestamping packages
        Stores UTC time, and adds UTC offset for user comfort
        Offset assumes plus sign, unless - present
        :return:
        """
        # get utc time YYMMDD-HHMM_
        utc = datetime.datetime.now(datetime.timezone.utc).strftime('%y%m%d_%H%M_')
        # get utc to local time offset, this is just for user
        offset = datetime.datetime.now(datetime.timezone.utc).astimezone().strftime('%z').replace('+', '')
        return utc + offset


    # get project settings
    settings = get_nuke_pack_project_settings()
    profile_name_first = list(settings)[0]

    profile_names = " ".join(list(settings))
    job_default_folder = settings[profile_name_first]["job"]["job_name_default"]
    job_default_check = settings[profile_name_first]["job"]["job_name_check"]
    job_default_path = settings[profile_name_first]["job"]["job_root"]

    # places
    job_places = list(settings[profile_name_first]["places"].keys())
    if job_places is None or len(job_places) < 2:
        print("Bad config, need two or more places")
    # current place can be defined by environment
    _place_target = job_places[1]
    if os.environ.get('PACK_NUKE_PLACE') is not None:
        _place_source = os.environ.get('PACK_NUKE_PLACE')
        if _place_source == job_places[1]:
            _place_target = job_places[0]
    else:
        _place_source = job_places[0]

    # Get project anatomy, and extend it with more tokens
    _timestamp = my_time()
    anatomy = get_anatomy()
    more_tokens = {
        "place_source": _place_source,
        "place_target": _place_target,
        "timestamp": _timestamp
    }
    anatomy.update(more_tokens)


    # show dialog
    # TODO

    # fake user input
    user_job_folder = job_default_folder.format_map(Default(anatomy)).replace("\\", "/")
    user_job_path = job_default_path.format_map(Default(anatomy)).replace("\\", "/")
    user_job_profile = profile_name_first
    place_source = _place_source
    place_target = _place_target

    # validate user input
    if not re.match(job_default_check, user_job_folder):
        print("Error! Make sure folder name matches convention:\n{}\n{}".format(job_default_check, user_job_folder))

    job_destination = user_job_path + "/" + user_job_folder  # no backslash, nuke hates it

    # now get a list of "workfile anatomies"
    # will fake it for now
    anatomy = get_anatomy()
    more_tokens = {
        "place_source": place_source,
        "place_target": place_target,
        "timestamp": _timestamp,
        'job': job_destination,  # add job name
        'job_path': user_job_path,
        'job_folder': user_job_folder
    }
    anatomy.update(more_tokens)
    anatomies = [anatomy]  # fake it for one Nuke script, for testing

    return anatomies, job_destination, settings.get(user_job_profile)


class PackNukeScript:
    def __init__(self, anatomy, job_destination, settings):

        self.anatomy = anatomy
        self.job_destination = job_destination
        self.settings = settings

        self.ocio = {}
        self.media_items = []
        self.font_items = []
        self.gizmo_items = []
        self.loaded_plugins = []
        self.categories = {}
        self.media_copy_list = []

    def file_sequence_to_glob(self, path):
        """
        Helper function to convert a full path with printf or hash file sequence notation to glob filter
        foo\bar%04d.exr -> foo/bar.????.exr
        foo\bar###.exr -> foo/bar.???.exr
        foo/bar -> foo/bar
        """

        path = path.replace('\\', '/')
        path_only = path.split('/')[:-1]
        name = path.split('/')[-1]
        if '#' in name:
            name.replace('#', '?')
            path = path_only + '/' + name
        elif '%' in name:
            result = re.search(r'(.*)(%\d+d)(.*)', name)
            printf_count = -1
            try:
                wildcards = '#' * int(result.group(2))
                path = path_only + '/' + result.group(1) + wildcards + result.group(3)
            except Exception as e:
                # no printf used
                pass
        return path

    def bytes_to_string(self, size_bytes):
        size_bytes = float(size_bytes)
        KB = float(1024)
        MB = float(KB ** 2)  # 1.048.576
        GB = float(KB ** 3)  # 1.073.741.824
        TB = float(KB ** 4)  # 1.099.511.627.776

        if size_bytes < KB:
            return '{0} {1}'.format(size_bytes, 'B')
        elif KB <= size_bytes < MB:
            return '{0:.2f} KB'.format(size_bytes / KB)
        elif MB <= size_bytes < GB:
            return '{0:.2f} MB'.format(size_bytes / MB)
        elif GB <= size_bytes < TB:
            return '{0:.2f} GB'.format(size_bytes / GB)
        elif TB <= size_bytes:
            return '{0:.2f} TB'.format(size_bytes / TB)

    def eval_tcl(self, text):
        val = ''
        try:
            val = nuke.tcl("[return \"" + text + "\"]")
        except Exception as e:
            # TCL not working for this string
            pass

        # only allow string type to be returned
        if type(val) is not str:
            val = text

        return val

    def prepend_project_directory(self, path, project_dir=None, evaluate_project_directory=True):
        """
        prepend_project_directory: merge project directory with path.
        :param path: Path to be merged with
        :param project_dir: Project directory
        :return:
        """

        if not project_dir:
            if evaluate_project_directory:
                # Project directory can be TCL or Python expression, evaluate to path
                project_dir = nuke.root()['project_directory'].evaluate()
            else:
                project_dir = nuke.root()['project_directory'].getValue()

        full_path = path
        if project_dir:
            project_dir.replace('\\', '/')
            project_dir.rstrip('/')
            if project_dir == '':
                project_dir = None
        if path and project_dir:
            path.replace('\\', '/')
            if path.startswith('./'):
                full_path = project_dir + path[1:]
            elif path.startswith('/'):
                full_path = project_dir + path
            else:
                full_path = project_dir + '/' + path

        return full_path

    def get_real_knob_paths(self, knob_path):
        """
        Returns all paths one file knob could refer to.
        Paths are absolute, no backslashes.

        :param knob_path:
        :return: list of absolute paths
        """

        # container for all found paths in sequence
        paths = []
        # all versions of knob_path (stereo views, %v)
        view_files = []
        # project directory relative path
        project_dir = False

        # check if stereo files are used
        if r'%v' in knob_path or r'%V' in knob_path:
            # get all stereo views in the comp
            view_return = nuke.root().knob('views').toScript()
            for rtn in view_return.split('\n'):
                # get each view name in the nuke comp
                view = rtn.split(' ')[-2]
                # replace in path and append to view_files
                view_files.append(knob_path.replace(r'%v', view).replace(r'%V', view))
        else:
            # if if stereo files not used, do not replace anything
            view_files = [knob_path]

        # overwrite knob_path value with new value per view
        # TODO per view file hashes
        for knob_path in view_files:

            # get TCL evaluated string
            knob_path_tcl = self.eval_tcl(knob_path)
            path_with_hashes = knob_path_tcl

            # get parent directory
            knob_path_parent_dir = os.path.dirname(knob_path_tcl)

            # try appending project root folder, if the dir does not exist
            if not os.path.exists(knob_path_parent_dir):
                knob_path_project_dir = self.prepend_project_directory(knob_path_parent_dir)
                if os.path.isdir(knob_path_project_dir):
                    project_dir = True
                    knob_path_parent_dir = knob_path_project_dir
                    knob_path_tcl = self.prepend_project_directory(knob_path_tcl)

            # check if the parent dir exists
            if os.path.exists(knob_path_parent_dir):
                # if it does, get the filename
                filename = knob_path_tcl.split('/')[-1]
                # get number from printf notation as int
                printf_count = -1
                try:
                    # regex pattern for printf notation (only get first result of found printf notations)
                    regex = re.compile('%..d')
                    regex_file = regex.findall(filename)[0]
                    printf_count = int(regex_file[1:-1])
                except Exception as e:
                    # no printf used
                    pass

                # if printf notation is used for the sequence
                if printf_count > 0:
                    # make wildcard string (e.g. '????') for glob with same length as #
                    wildcards = ''
                    for i in range(printf_count):
                        wildcards += '?'
                    wildcard_path = knob_path_tcl.replace(regex_file, wildcards)
                    # get all files in directory
                    files = glob.glob(wildcard_path)
                    for each_file in files:
                        paths.append(each_file.replace('\\', '/'))
                    path_with_hashes = wildcard_path.replace('?', '#')

                # if hash notation is used for the sequence
                elif '#' in filename:
                    # split by #
                    filename_split = filename.split('#')
                    # count amount of #
                    wildcard_count = len(filename_split) - 2
                    # make wildcard string (e.g. '????') for glob with same length as #
                    wildcards = ''
                    for i in range(wildcard_count + 1):
                        wildcards += '?'
                    # get full filename with wildcard replaced
                    filename = filename_split[-len(filename_split)] + wildcards + filename_split[-1]
                    # full file path
                    wildcard_path = os.path.join(knob_path_parent_dir, filename).replace('\\', '/')

                    # get all files that match wildcard pattern
                    files = glob.glob(wildcard_path)
                    for each_file in files:
                        paths.append(each_file.replace('\\', '/'))
                    path_with_hashes = wildcard_path.replace('?', '#')

                # if not a sequence
                else:
                    # append this file to paths, if it exists
                    if os.path.isfile(knob_path_tcl):
                        paths.append(knob_path_tcl)

                    # check if it is a relative (project directory) path
                    elif os.path.isfile(self.prepend_project_directory(knob_path_tcl)):
                        paths.append(self.prepend_project_directory(knob_path_tcl))

        # return result
        return paths, project_dir, path_with_hashes.replace('#', '?')

    def read_comp_data(self):
        """
        Gets all file knobs in Nuke file
        Runs them through get_real_knob_paths()
        Gets size of every file
        Calculates media_item total size
        Notes disabled nodes
        Makes media_item
        Merges duplicities
        :return:
        """

        def get_ocio():
            """
            Gets OCIO config details
            """

            all_files = []
            total_size = 0
            hash_for_all = ''
            color_management = nuke.root().knob('colorManagement').value()
            custom_path = ''
            cfg = nuke.root().knob('OCIO_config').value()

            if os.environ.get('OCIO') is not None:
                # env has precedence
                custom_path = os.path.abspath(os.environ.get('OCIO')).replace("\\", "/")
                cfg = 'custom' # pretend it is not set by environment
            else:

                if cfg == 'custom':
                    # read custom
                    custom_path = os.path.abspath(nuke.root().knob('customOCIOConfigPath').evaluate()).replace("\\", "/")

            if custom_path != '':
                files = glob.glob(os.path.dirname(custom_path) + '/**', recursive=True)
                files = [f.replace("\\", "/") for f in files if os.path.isfile(f)]
                if files is not None and len(files) > 0:
                    # get total file size
                    all_hashes = ''
                    for each_file in files:
                        size = os.path.getsize(each_file)
                        total_size += size
                        my_hash = get_file_hash(each_file)
                        all_hashes += my_hash
                        all_files.append({'path': each_file, 'size': size, 'hash': my_hash})
                    hash_for_all = hashlib.blake2b(all_hashes.encode()).hexdigest()

                self.ocio = {
                    'color_management': color_management,
                    'ocio_config': cfg,
                    'custom_path': custom_path,
                    'all_files': all_files,
                    'hash_for_all': hash_for_all,
                    'total_size': total_size
                }

            return self.ocio

        def is_node_disconnected(node):

            disconnected = False
            # can have outputs and has no outputs
            no_outs = False
            no_ins = False
            if node.dependent() == []:
                no_outs = True
            if node.dependencies() == []:
                no_ins = True
            if no_outs and no_ins:
                disconnected = True

            return disconnected

        def is_node_gizmo(node):
            # check if a node is a gizmo, and if so, return the full name

            if type(node) == nuke.Gizmo:
                return node.Class() if node.Class().endswith('.gizmo') else node.Class() + '.gizmo'
            else:
                return ''

        def get_knob_value(node, knob_name):
            """Return the value of a knob or return None if it is missing"""
            value = None
            if not isinstance(node.knob(knob_name), type(None)):
                value = node.knob(knob_name).value()
                if value is None:
                    value = node.knob(knob_name).getValue()
            return value

        def get_loaded_plugins():

            libs = ['.dll', '.so', '.dylib', '.pdb']

            nuke_exe = nuke.env["ExecutablePath"].split('/')
            nuke_exe_folder = '/'.join(nuke_exe[:-1])
            custom_plugins = []
            loaded_plugins = nuke.plugins()
            for plugin in loaded_plugins:
                if any(lib in plugin for lib in libs):
                    # skip loaded plugins in nuke/plugins folder
                    if nuke_exe_folder not in plugin:
                        custom_plugins.append(plugin)
            return custom_plugins

        def get_file_hash(path):
            my_hash = None
            if self.settings['hashes']['hashes_generate']:
                one_file = open(path, 'rb')
                try:
                    # read all file at once, memory hungry but faster
                    my_hash = hashlib.blake2b(one_file.read()).hexdigest()
                finally:
                    one_file.close()
            return my_hash

        def store_gizmo_item(gizmo_name, gizmo_items, each_node, node_disabled, node_disconnected):

            if gizmo_name != '':

                gizmo_path_found = False
                gizmo_path = ''
                for each_plugin_path in nuke.pluginPath():
                    gizmo_path = os.path.join(each_plugin_path, gizmo_name).replace('\\', '/')
                    if os.path.isfile(gizmo_path):
                        gizmo_path_found = True
                        break
                if gizmo_path_found:
                    if os.path.isfile(gizmo_path):
                        gizmo_item = {
                            'gizmo_name': gizmo_name,
                            'path': gizmo_path,
                            'node_name': each_node.fullName(),
                            'node_class': each_node.Class(),
                            'node_disabled': node_disabled,
                            'node_disconnected': node_disconnected,
                            'node': each_node,
                            'size': os.path.getsize(gizmo_path),
                            'file_hash': get_file_hash(gizmo_path),
                            'duplicate_of': None,
                        }
                        gizmo_items.append(gizmo_item)

            return gizmo_items

        def get_font_info(font_items):
            """
            fill missing info from getFonts
            if font path is known, get family, style, index
            if font path is not known, get path
            get file size and hash
            """

            # see https://learn.foundry.com/nuke/content/comp_environment/effects/fonts_properties.html
            # https://learn.foundry.com/nuke/developers/latest/pythondevguide/_autosummary/nuke.getFonts.html

            # list of lists: [font_family, font_style, path, index]
            all_fonts = nuke.getFonts()

            if font_items and len(font_items) > 0:
                # get all fonts as list of lists ["Open Sans", "Regular", "fontapath", somenumber]:

                for found_font in font_items:
                    if found_font['path']:
                        # path is known, what is the font family & style?
                        for font in all_fonts:
                            if found_font['path'] == font[2]:
                                found_font['font_family'] = font[0]
                                found_font['font_style'] = font[1]
                                found_font['font_index'] = font[3]
                                break
                    else:
                        # need to find the path
                        to_match = found_font['font_family'] + found_font['font_style']
                        found_font['path'] = None
                        for font in all_fonts:
                            check = font[0] + font[1]
                            if to_match == check:
                                found_font['path'] = font[2]
                                found_font['font_index'] = font[3]
                                break

                # now path is there, get size and hash
                for found_font in font_items:
                    found_font['size'] = os.path.getsize(found_font['path'])
                    found_font['file_hash'] = get_file_hash(found_font['path'])

            return font_items

        def get_media_item(node, knob, path, disabled, disconnected):
            # get real paths (file path list + project dir bool)
            real_knob_paths, project_dir, path_with_question_marks = self.get_real_knob_paths(path)

            # make new list for new paths with their per-file size included
            all_files = []

            # get total file size
            total_size = 0
            if real_knob_paths is None:
                return None

            all_hashes = ''
            for each_file in real_knob_paths:
                size = os.path.getsize(each_file)
                total_size += size
                my_hash = get_file_hash(each_file)
                all_hashes += my_hash
                all_files.append({'path': each_file, 'size': size, 'hash': my_hash})
            hash_for_all = hashlib.blake2b(all_hashes.encode()).hexdigest()

            # transform type in Nuke 15+, being colorspace/display
            # the display value needs ocioDisplay, ocioView
            _type = get_knob_value(node, 'transformType')
            if _type is None:
                _type = 'colorspace'
            _cs = get_knob_value(node, 'colorspace')
            # for default colorspace, do a wild guess by nuke defaults and file extension
            if _cs is not None and _cs == 'default':
                file_name = path_with_question_marks.split('/')[-1]
                extension = file_name.split('.')[-1]
                _cs = nuke.root()['floatLut'].value()
                if extension != 'exr':
                    _cs = nuke.root()['int8Lut'].value()

            _read_range = '-'
            if node.Class() == 'Read':
                _first = get_knob_value(node, 'first')
                _last = get_knob_value(node, 'last')
                if _first is not None and _last is not None:
                    _read_range = f'{int(str(_first).strip())}-{int(str(_last).strip())}'

            item = {
                'node': node,
                'color_space': _cs,
                'color_transformType': _type,
                'color_display': get_knob_value(node, 'ocioDisplay'),
                'color_view': get_knob_value(node, 'ocioView'),
                'color_raw': get_knob_value(node, 'raw'),
                'read_range': _read_range,
                'knob': knob,
                'node_class': node.Class(),
                'node_name': node.fullName(),
                'found_path': path,
                'found_path_filter': path_with_question_marks,
                'all_files': all_files,
                'hash_for_all': hash_for_all,
                'total_size': total_size,
                'project_dir': project_dir,
                'node_disabled': disabled,
                'node_disconnected': disconnected,
                'categories': [],
                'category_files': {},
                'tokens': {},
                'duplicate_of': None,
                'exist_on_target': False
            }
            return item


        # OCIO first
        get_ocio()

        # progress bar total value
        all_nodes = nuke.allNodes(recurseGroups=True)
        progress_total = len(all_nodes)

        # container for all loaded files
        media_items = []
        gizmo_items = []
        font_items = []

        # collect all knobs with files in them
        i_node = 0
        for each_node in all_nodes:

            # is node disabled?
            node_disabled = False
            if each_node.knob('disable') and each_node['disable'].getValue():
                node_disabled = True

            # is node disconnected?
            node_disconnected = is_node_disconnected(each_node)

            # check if node is a gizmo
            gizmo_name = is_node_gizmo(each_node)
            if gizmo_name != '':
                gizmo_items = store_gizmo_item(gizmo_name, gizmo_items, each_node, node_disabled, node_disconnected)

            # Check all knobs in Node
            for each_knob in each_node.knobs():
                curr_knob = each_node[each_knob]

                # File resource
                if curr_knob.Class() == 'File_Knob':
                    # only add if a path has been entered
                    found_path = curr_knob.getValue()
                    if '[' in found_path:
                        found_path = curr_knob.evaluate()
                    if found_path != '':
                        if found_path.endswith('.ttf'):
                            one_font = {
                                'font_family': None,
                                'font_style': None,
                                'font_index': None,
                                'node': each_node,
                                'knob': curr_knob,
                                'knob_type': 'File_Knob',
                                'node_class': str(each_node.Class()),
                                'node_name': str(each_node.fullName()),
                                'node_disabled': node_disabled,
                                'node_disconnected': node_disconnected,
                                'path': found_path.replace('\\', '/'),
                                'duplicate_of': None,
                                'font_files': {}
                            }
                            font_items.append(one_font)

                        else:
                            # file knob that is not a font
                            media_item = get_media_item(each_node, curr_knob, found_path, node_disabled,
                                                        node_disconnected)
                            if media_item is not None:
                                media_items.append(media_item)

                # Font resource
                elif curr_knob.Class() == 'FreeType_Knob':
                    # returns ["Open Sans", "Regular"]
                    found_font_knob = curr_knob.getValue()
                    if found_font_knob and len(found_font_knob) == 2:
                        one_font = {
                            'font_family': found_font_knob[0],
                            'font_style': found_font_knob[1],
                            'font_index': None,
                            'node': each_node,
                            'knob': curr_knob,
                            'knob_type': 'FreeType_Knob',
                            'node_class': str(each_node.Class()),
                            'node_name': str(each_node.fullName()),
                            'node_disabled': node_disabled,
                            'node_disconnected': node_disconnected,
                            'path': None,
                            'duplicate_of': None,
                            'font_files': {}
                        }
                        font_items.append(one_font)

            percent = int(round(float(i_node) / float(progress_total) * 100 / 2))
            # print('Done {}% of Nodes'.format(percent))
            i_node += 1

        self.media_items = media_items
        self.font_items = get_font_info(font_items)
        self.gizmo_items = gizmo_items
        self.loaded_plugins = get_loaded_plugins()

    def make_report(self):

        # save report (start)
        report = []
        for one in self.media_items:
            if one['duplicate_of'] is None:
                number_of_files = len(one['all_files'])
                if number_of_files == 1:
                    hash = one['all_files'][0]['hash']
                else:
                    hash = ''
                file_name = one['found_path_filter'].split('/')[-1]
                extension = file_name.split('.')[-1]
                if one['color_space'] is not None and one['color_space'] is None:
                    color_info = one['color_space']
                elif one['color_transformType'] is not None and one['color_transformType'] == 'display':
                    color_info = f"{one['color_display']}:{one['color_view']}"
                else:
                    color_info = ''
                if one['color_raw'] is not None and one['color_raw']:
                    color_info += ':raw'

                item = {
                    'type': 'media',
                    'categories': ', '.join(one['categories']),
                    'info': color_info,
                    'node_class': one['node_class'],
                    'node_name': one['node_name'],
                    'file_name': file_name,
                    'extension': extension,
                    'size': one['total_size'],
                    'node_disabled': one['node_disabled'],
                    'node_disconnected': one['node_disconnected'],
                    'path': one['found_path'],
                    'file_hash': hash,
                    'file_number': number_of_files,
                    'hash_for_all': one['hash_for_all'],
                    'place_source': self.anatomy['place_source'],
                    'place_target': self.anatomy['place_target'],
                    'timestamp': self.anatomy['timestamp']
                }
                report.append(item)

        for one in self.font_items:
            if one['duplicate_of'] is None:
                file_name = one['path'].split('/')[-1]
                extension = file_name.split('.')[-1]
                font_info = f"{one['font_family']}, {one['font_style']}, {one['font_index']}"
                item = {
                    'type': 'fonts',
                    'info': font_info,
                    'node_class': one['node_class'],
                    'node_name': one['node_name'],
                    'file_name': file_name,
                    'extension': extension,
                    'size': one['size'],
                    'categories': 'font',
                    'node_disabled': one['node_disabled'],
                    'node_disconnected': one['node_disconnected'],
                    'path': one['path'],
                    'file_hash': one['file_hash'],
                    'file_number': 1,
                    'hash_for_all': '',
                    'place_source': self.anatomy['place_source'],
                    'place_target': self.anatomy['place_target'],
                    'timestamp': self.anatomy['timestamp']
                }
                report.append(item)

        for one in self.gizmo_items:
            if one['duplicate_of'] is None:
                file_name = one['path'].split('/')[-1]
                extension = file_name.split('.')[-1]
                item = {
                    'type': 'gizmos',
                    'info': '',
                    'node_class': one['node_class'],
                    'node_name': one['node_name'],
                    'file_name': file_name,
                    'extension': extension,
                    'size': one['size'],
                    'categories': 'gizmo',
                    'node_disabled': one['node_disabled'],
                    'node_disconnected': one['node_disconnected'],
                    'path': one['path'],
                    'file_hash': one['file_hash'],
                    'file_number': 1,
                    'hash_for_all': '',
                    'place_source': self.anatomy['place_source'],
                    'place_target': self.anatomy['place_target'],
                    'timestamp': self.anatomy['timestamp']
                }
                report.append(item)

        self.report = report


    def media_items_to_categories(self):

        def is_media_item_matching(media_item, paths, filter_options, filter_list):

            def match_regex(filter, source):
                """
                Checks if the filter matches the source by regex
                """
                try:
                    _re = re.compile(filter['search'])
                except:
                    return None

                result = re.search(filter['search'], source)
                if filter['check']:
                    # we have something to check agains
                    if result.group(1) in filter['check']:
                        if not filter['invert']:
                            # print("Match_regex matched")
                            return result.group(1)
                        else:
                            # print("Match_regex not matched, 'cause of invert")
                            return None
                    else:
                        if not filter['invert']:
                            # print("Match_regex not matched.")
                            return None
                        else:
                            # print("Match_regex matched, 'cause of invert.")
                            return result.group(1)
                else:
                    # not looking for match, just if regex found something
                    if not filter['invert']:
                        return result.group(1)
                    else:
                        return None

            def match_node_class(my_filter, node_class):
                """
                Filter check is ignored, only matches the class name
                """
                if node_class is None:
                    return None

                node_list = my_filter['search'].strip().split(' ')
                if node_list is None or len(node_list) == 0:
                    return None

                if node_class in node_list:
                    if not my_filter['invert']:
                        # print("Match_class matched")
                        return node_class
                    else:
                        # print("Match_class not matched, 'cause of invert")
                        return None
                else:
                    if not my_filter['invert']:
                        # print("Match_class not matched")
                        return None
                    else:
                        # print("Match_class matched, 'cause of invert")
                        return node_class

            if filter_options['skip_disconnected'] and media_item['node_disconnected']:
                # should skip disconnected
                # print("Media Item {} skipped: disconnected".format(media_item['node_name']))
                return False, None
            if filter_options['skip_disabled'] and media_item['node_disabled']:
                # should skip disabled
                # print("Media Item {} skipped: disabled".format(media_item['node_name']))
                return False, None
            if media_item['all_files'] and len(media_item['all_files']) > 0:
                full_path = media_item['all_files'][0]['path']
                _dir, file_name = os.path.split(full_path)
            else:
                # print("Media Item {} skipped: no file found".format(media_item['node_name']))
                # no file, no match
                return False, None

            matches = 0
            tokens = {}
            for one_filter in filter_list:
                match = None
                if one_filter['source'] == 'File Name':
                    match = match_regex(one_filter, source=file_name)
                elif one_filter['source'] == 'File Path':
                    match = match_regex(one_filter, source=full_path)
                elif one_filter['source'] == 'Node Class':
                    match = match_node_class(one_filter, media_item['node_class'])

                if match is not None:
                    tokens[one_filter['token_name']] = match
                    matches += 1
            # print("Tokens {}, matches {}".format(tokens, matches))

            if (filter_options['combine_filters'].lower() == 'and' and matches == len(filter_list)) or (
                    filter_options['combine_filters'].lower() == 'or' and matches > 0):
                # media item is matching filter!
                return True, tokens
            else:
                return False, tokens

        self.categories = self.settings.get('categories')
        default_category = get_default_category()
        if not self.categories:
            # no categories defined, take default
            self.categories = default_category

        for category_name, category in self.categories.items():
            # get path options
            paths = category.get('path')
            if not paths:
                paths = default_category['default_category']['path']
            # get filter options
            filter_options = category.get('filter_options')
            if not filter_options:
                filter_options = default_category['default_category']['filter_options']
            # get filters
            filter_list = category.get('filters')
            if not filter_list:
                filter_list = default_category['default_category']['filters']

            for media_item in self.media_items:
                # print("media_items_to_categories: checking {} {}".format(media_item['node_name'], category_name))
                matching, more_tokens = is_media_item_matching(media_item, paths, filter_options, filter_list)
                if matching:
                    # add category name to media item
                    cats = media_item.get('categories')
                    if cats is not None:
                        media_item['categories'].append(category_name)
                    else:
                        media_item['categories'] = [category_name]
                    # add tokens to media item
                    tokens = media_item.get('tokens')
                    if tokens is not None:
                        media_item['tokens'].update(more_tokens)
                    else:
                        media_item['tokens'] = more_tokens
                else:
                    pass
                    # print("Media Item from node {} doesn't match the category name {}".format(media_item['node_name'], category_name))

    def find_media_duplicities(self):

        for media_item in self.media_items:
            if media_item['duplicate_of'] is None:
                for check_item in self.media_items:
                    if check_item == media_item:
                        continue
                    if media_item['all_files'] == check_item['all_files']:
                        check_item['duplicate_of'] = media_item

    def find_font_duplicities(self):

        for font_item in self.font_items:
            if font_item['duplicate_of'] is None:
                for check_item in self.font_items:
                    if check_item == font_item:
                        continue
                    if font_item['path'] == check_item['path']:
                        check_item['duplicate_of'] = font_item

    def find_gizmo_duplicities(self):

        for gizmo_item in self.gizmo_items:
            if gizmo_item.get('duplicate_of') is None:
                for check_item in self.gizmo_items:
                    if check_item == gizmo_item:
                        continue
                    if gizmo_item['path'] == check_item['path']:
                        check_item['duplicate_of'] = gizmo_item

    def media_items_to_paths(self):
        """
        Fills media_item['category_files'][category_name]
        template and template_relink are paths with tokens filled
        target and relink are list of paths for every file
        """

        class Default(dict):
            def __missing__(self, key):
                return key

        for media_item in self.media_items:
            cats = media_item.get('categories')
            all_tokens = {**self.anatomy, **media_item['tokens']}

            # get nuke compatible file name from glob filter, ie foo.????.exr -> foo.%04d.exr
            nuke_filter = os.path.basename(media_item['found_path_filter'])
            #print(f" Filter before {nuke_filter}")
            try:
                glob_split = re.match('([^\?]+)(\?*)([^\?]+)', nuke_filter)
                if glob_split.group(2):
                    nuke_filter = glob_split.group(1) + '%0' + str(len(glob_split.group(2))) + 'd' + glob_split.group(3)
                    #print(f" Filter after {nuke_filter} {glob_split.group(2)}")
            except:
                # no ? in file name, so it is a single file
                pass

            # get filename but skip file sequence counter, use glob filter
            _ = os.path.basename(media_item['found_path_filter']).split('?')
            clean_name = _[0].rstrip('._-')
            if len(_) > 1:
                 clean_name += _[-1]

            all_file_names = []
            for one_file in media_item['all_files']:
                all_file_names.append(one_file['path'].split('/')[-1])

            if cats is not None:
                for one_category in cats:
                    all_tokens['category'] = one_category
                    all_tokens['node'] = media_item['node_name']
                    all_tokens['node_class'] = media_item['node_class']
                    all_tokens['clean_name'] = clean_name

                    cat_set = self.settings['categories'][one_category]
                    r_t = cat_set['path']['root_template'].format(**all_tokens).replace("\\", "/")
                    r_t_r = cat_set['path']['root_template_relink'].format(**all_tokens).replace("\\", "/")
                    t_f = cat_set['path']['top_folder'].format(**all_tokens).replace("\\", "/")
                    t_f_r = cat_set['path']['top_folder_relink'].format(**all_tokens).replace("\\", "/")

                    targets = []
                    relinks = []
                    for one_file in all_file_names:
                        target = r_t + '/' + t_f + '/' + one_file
                        targets.append(target)
                        relinks.append(r_t_r + '/' + t_f_r + '/' + one_file)

                    media_item['category_files'][one_category] = {
                        'template': r_t + '/' + t_f,
                        'template_relink': r_t_r + '/' + t_f_r,
                        'target': targets,
                        'target_nuke': r_t + '/' + t_f + '/' + nuke_filter,
                        'target_exists': False,
                        'relink': relinks,
                        'relink_nuke': r_t_r + '/' + t_f_r + '/' + nuke_filter
                    }

    def font_items_to_paths(self):
        """
        Fills font_item['font_files']
        template and template_relink are paths with tokens filled
        target and relink are list of paths for every file
        """

        _stngs = self.settings['fonts']
        for font_item in self.font_items:
            tokens = {
                'node': font_item['node_name'],
                'class': font_item['node_class'],
                'font': font_item['font_family'],
                'clean_name': os.path.basename(font_item['path'])
            }
            all_tokens = {**self.anatomy, **tokens}
            file_name = font_item['path'].split('/')[-1]

            r_t = _stngs['root_template'].format(**all_tokens).replace("\\", "/")
            r_t_r = _stngs['root_template_relink'].format(**all_tokens).replace("\\", "/")

            t_f = _stngs['top_folder'].format(**all_tokens).replace("\\", "/")
            if t_f != '':
                _template_full = r_t + '/' + t_f
            else:
                _template_full = r_t

            t_f_r = _stngs['top_folder_relink'].format(**all_tokens).replace("\\", "/")
            if t_f_r != '':
                _template_full_relink = r_t_r + '/' + t_f_r
            else:
                _template_full_relink = r_t_r

            font_item['font_files'] = {
                'path': font_item['path'],
                'template': _template_full,
                'template_relink': _template_full_relink,
                'target': _template_full + '/' + file_name,
                'target_exists': False,
                'relink': _template_full_relink + '/' + file_name
            }

    def ocio_to_paths(self):

        self.ocio['files'] = []
        if self.ocio['color_management'] != 'OCIO' or self.ocio['ocio_config'] != 'custom' or self.ocio['custom_path'] == '':
            return

        _stngs = self.settings['ocio']
        custom_folder = os.path.dirname(self.ocio['custom_path']).replace('\\', '/')
        custom_folder_up = '/'.join(custom_folder.split('/')[:-1])
        all_tokens = {**self.anatomy}
        for one_file in self.ocio['all_files']:
            path = one_file['path']
            path_end = path
            if path.startswith(custom_folder_up):
                path_end = path[len(custom_folder_up):].lstrip('/')

            r_t = _stngs['root_template'].format(**all_tokens).replace("\\", "/")
            r_t_r = _stngs['root_template_relink'].format(**all_tokens).replace("\\", "/")
            t_f = _stngs['top_folder'].format(**all_tokens).replace("\\", "/")
            if t_f != '':
                _template_full = r_t + '/' + t_f
            else:
                _template_full = r_t
            t_f_r = _stngs['top_folder_relink'].format(**all_tokens).replace("\\", "/")
            if t_f_r != '':
                _template_full_relink = r_t_r + '/' + t_f_r
            else:
                _template_full_relink = r_t_r

            item = {
                'path': path,
                'template': _template_full,
                'template_relink': _template_full_relink,
                'target': _template_full + '/' + path_end,
                'target_exists': False,
                'relink': _template_full_relink + '/' + path_end
            }
            self.ocio['files'].append(item)

    def gizmo_items_to_paths(self):
        """
        Fills gizmo_item['gizmo_files']
        template and template_relink are paths with tokens filled
        target and relink are list of paths for every file
        """

        _stngs = self.settings['gizmos']
        for item in self.gizmo_items:
            tokens = {
                'node': item['node_name'],
                'class': item['node_class'],
                'clean_name': os.path.basename(item['path'])
            }
            all_tokens = {**self.anatomy, **tokens}
            file_name = item['path'].split('/')[-1]

            r_t = _stngs['root_template'].format(**all_tokens).replace("\\", "/")
            r_t_r = _stngs['root_template_relink'].format(**all_tokens).replace("\\", "/")

            t_f = _stngs['top_folder'].format(**all_tokens).replace("\\", "/")
            if t_f != '':
                _template_full = r_t + '/' + t_f
            else:
                _template_full = r_t

            t_f_r = _stngs['top_folder_relink'].format(**all_tokens).replace("\\", "/")
            if t_f_r != '':
                _template_full_relink = r_t_r + '/' + t_f_r
            else:
                _template_full_relink = r_t_r

            item['gizmo_files'] = {
                'path': item['path'],
                'template': _template_full,
                'template_relink': _template_full_relink,
                'target': _template_full + '/' + file_name,
                'target_exists': False,
                'relink': _template_full_relink + '/' + file_name
            }

    def execute_command(self, command):

        command_as_string = ' '.join(command)
        # print("Executing command: {}".format(command_as_string))

        process = subprocess.run(command_as_string,
                                 capture_output=True,
                                 shell=True,
                                 check=False)

        return_code = process.returncode
        output = process.stdout.decode('utf8', 'ignore').strip('\n')
        error = process.stderr.decode('utf8', 'ignore').strip('\n')
        return return_code, output, error

    def copy_sequence(self, source_folder, destination_folder, file_name_filter):

        return_code = None
        output = None
        error = None

        # print("Copying sequence files {}/{} to {}".format(source_folder, file_name_filter, destination_folder))

        if platform.system() == 'Windows':
            return_code, output, error = self.execute_command(
                ['robocopy', source_folder, destination_folder, file_name_filter])
        elif platform.system() == 'Linux':
            return_code, output, error = self.execute_command(
                ['rsync', '-avh', '--progress', '--stats', source_folder + '/' + file_name_filter,
                 destination_folder + '/'])
        else:
            for file in glob.glob(source_folder + '/' + file_name_filter):
                shutil.copy(file, destination_folder)
            return_code = 0
            output = ''
            error = ''
        return return_code, output, error

    def copy_file(self, source, target):

        # print("Copying file {} to {}".format(source, target))
        shutil.copy2(source, target)
        return 0

    def copy_media(self):
        start = timeit.timeit()

        for media_item in self.media_items:
            if media_item['duplicate_of'] is None:
                source_folder = '/'.join(media_item['found_path_filter'].split('/')[:-1])
                file_name_filter = None
                if '?' in media_item['found_path_filter']:
                    file_name_filter = media_item['found_path_filter'].split('/')[-1]
                for one_category, paths in media_item['category_files'].items():
                    # make sure the target folder exists
                    destination_folder = '/'.join(paths['target'][0].split('/')[0:-1])
                    os.makedirs(destination_folder, exist_ok=True)
                    if file_name_filter:
                        return_code, output, error = self.copy_sequence(source_folder, destination_folder,
                                                                        file_name_filter)
                    else:
                        # might not be file sequence, will loop all files anyway, just in case
                        for i in range(0, len(media_item['all_files'])):
                            source = media_item['all_files'][i]['path']
                            target = paths['target'][i]
                            self.copy_file(source, target)

        end = timeit.timeit()
        print("Coping media took {} seconds".format(int(end - start)))

    def copy_fonts(self):
        start = timeit.timeit()

        for item in self.font_items:
            if item['duplicate_of'] is None:
                os.makedirs(os.path.dirname(item['font_files']['target']), exist_ok=True)
                self.copy_file(item['path'], item['font_files']['target'])

        end = timeit.timeit()
        print("Coping fonts took {} seconds".format(int(end - start)))

    def copy_gizmos(self):
        start = timeit.timeit()

        for item in self.gizmo_items:
            if item['duplicate_of'] is None:
                os.makedirs(os.path.dirname(item['gizmo_files']['target']), exist_ok=True)
                self.copy_file(item['path'], item['gizmo_files']['target'])

        end = timeit.timeit()
        print("Coping gizmos took {} seconds".format(int(end - start)))

    def copy_ocio(self):
        start = timeit.timeit()

        ocio_files = self.ocio.get('files')
        if ocio_files is None:
            return
        for item in self.ocio['files']:
            os.makedirs(os.path.dirname(item['target']), exist_ok=True)
            self.copy_file(item['path'], item['target'])

        end = timeit.timeit()
        print("Coping ocio took {} seconds".format(int(end - start)))

    def gizmos_to_groups(self):

        def deselect_all():
            # deselect all nodes.
            for i in nuke.allNodes():
                i.knob('selected').setValue(False)

        for one in self.gizmo_items:
            gizmo = one['node']

            inputs = []
            for x in range(0, gizmo.maximumInputs()):
                if gizmo.input(x):
                    # print 'input: %s' % (gizmo.input(x).knob('name').value())
                    inputs.append(gizmo.input(x))
                else:
                    inputs.append(False)
            orig_name = gizmo.knob('name').value()
            orig_pos_x = gizmo.xpos()
            orig_pos_y = gizmo.ypos()
            deselect_all()
            # select knob, then run gizmo.makeGroup()
            gizmo.knob('selected').setValue(True)
            new_group = gizmo.makeGroup()
            deselect_all()
            # delete original
            nuke.delete(gizmo)
            new_group.knob('name').setValue(orig_name)
            new_group['xpos'].setValue(orig_pos_x)
            new_group['ypos'].setValue(orig_pos_y)
            # disconnect old inputs, reconnect inputs
            for x in range(0, new_group.maximumInputs()):
                new_group.setInput(x, None)
                if inputs[x]:
                    new_group.connectInput(x, inputs[x])

    def make_relative(self, my_path, my_root, up_allowed=True):

        my_root.replace('\\', '/').rstrip('/')
        my_path.replace('\\', '/').rstrip('/')
        rel = ''
        up_cnt = 0
        all_fix = ''
        root_fix = ''
        path_fix = ''
        if (len(my_root) <= len(my_path)) and (my_path[:len(my_root)] == my_root):
            # start matches
            rel = my_path[len(my_root):]
            if rel[0] == '/':
                rel = my_path[len(my_root) + 1:]
        else:
            if up_allowed:
                # let's see if we can match partially
                root_s = my_root.split('/')
                path_s = my_path.split('/')
                c = []
                c_fix = []
                up_cnt = 1
                if root_s[0].lower() == path_s[0].lower():
                    for cnt in range(len(my_path)):
                        if root_s[cnt] == path_s[cnt]:
                            pass
                        else:
                            for one in range(cnt, len(root_s) - 1):
                                c.append('..')
                                up_cnt += 1
                            for one in range(cnt, len(path_s)):
                                c.append(path_s[one])
                                c_fix.append(path_s[one])
                            break
                    rel = '/'.join(c)
                    # _fix adjusts the root to remove as many folders up to eliminate ../ as necessary
                    root_fix = '/'.join(root_s[:-1 * up_cnt])
                    # print('root_fix: ' + str(root_fix))
                    path_fix = '/'.join(c_fix)
                    # print('path_fix: ' + str(path_fix))
                    all_fix = root_fix + '/' + path_fix
                else:
                    pass
        return {'relative': rel, 'up_cnt': up_cnt, 'all_fix': all_fix, 'root_fix': root_fix, 'path_fix': path_fix}

    def relink(self, script, relative=True, above=0, project_custom=False, project=''):
        """
        Relink current nuke script to new paths
        """

        def get_node_and_path(item):

            if item['categories'] is None or item['categories'] == []:
                return None, None
            if item['category_files'] is None or item['category_files'] == []:
                return None, None
            first_category = item['categories'][0]
            cat_files = item['category_files'].get(first_category)
            if cat_files is None:
                return None, None
            target_nuke = cat_files.get('target_nuke')
            if target_nuke is None:
                return None, None
            return item['node_name'], target_nuke

        tile_colors = {
            'brown': 3477542145,  # print(int('%02x%02x%02x%02x' % (207,71,21,1),16))
            'lime_green': 3034977281,  # print(int('%02x%02x%02x%02x' % (180,230,20,1),16))
            'deep_green': 176695809,  # print(int('%02x%02x%02x%02x' % (10,136,42,1),16))
            'violet': 2400240129,  # print(int('%02x%02x%02x%02x' % (143,16,194,1),16))
            'fuchsia': 2400240129  # print(int('%02x%02x%02x%02x' % (168,39,178,1),16))
        }

        # set project root for relative paths
        script = script.replace('\\', '/')
        if relative:
            if project_custom:
                prj = project.replace('\\', '/').rstrip('/')
                project = prj
            else:
                if above == 0:
                    prj = '[file dirname [knob root.name]]'
                    project = os.path.dirname(script)
                else:
                    prj = '[join [lrange [split [file dirname [knob root.name]] "/"] 0 end-' + str(int(above)) + ' ] "/"]'
                    project = '/'.join(os.path.dirname(script).split('/')[:-1 * above])
            nuke.root()["project_directory"].setValue(prj)

        for item in self.media_items:
            if item['duplicate_of'] is None:
                node_name, target_nuke = get_node_and_path(item)
                color = tile_colors['lime_green']
            else:
                node_name, target_nuke = get_node_and_path(item['duplicate_of'])
                node_name = item['node_name']
                color = tile_colors['deep_green']
            if node_name is None or target_nuke is None:
                continue

            if relative:
                rel = self.make_relative(target_nuke, project)
                target_nuke = rel['relative']

            node = nuke.toNode(node_name)
            node['file'].setValue(target_nuke)
            node['tile_color'].setValue(color)

        # OCIO
        if self.ocio['color_management'] == 'OCIO' and self.ocio['ocio_config'] == 'custom':
            for one_file in self.ocio['files']:

                if one_file['path'] == self.ocio['custom_path']:
                    print(f"found it {one_file['path']}")
                    if not self.settings['ocio']['relative']:
                        print("ABSOLUTE")
                        nuke.root()['customOCIOConfigPath'].setValue(one_file['target'])
                        nuke.root()['OCIO_config'].setValue('custom')
                    else:
                        print("RELATIVE")
                        nuke_script = nuke.root().knob('name').evaluate().replace("\\", "/")
                        print(nuke_script)
                        repl_dir = self.make_relative(one_file['target'], nuke_script)
                        pprint.pprint(repl_dir)
                        if repl_dir['relative'] is not None and repl_dir['relative'] != '':
                            if repl_dir['up_cnt'] > 0:
                                new_ocio = '[join [lrange [split [file dirname [knob root.name]] "/"] 0 end-' + str(
                                    int(repl_dir['up_cnt'])-1) + ' ] "/"]/' + repl_dir['path_fix']
                                nuke.root()['customOCIOConfigPath'].setValue(new_ocio)
                                nuke.root()['OCIO_config'].setValue('custom')
                    break

        nuke.scriptSave(script)

    def make_nuke_scripts(self):

        class Default(dict):
            def __missing__(self, key):
                return key

        nuke_script_full = nuke.root().name().replace('\\', '/')
        nuke_script = nuke_script_full.split('/')[-1]
        self.anatomy['script_name'] = nuke_script[:-3]

        nuke_source = self.settings['nuke_scripts']['source']['path'].format_map(
            Default(self.anatomy)).replace("\\", "/")
        os.makedirs(os.path.dirname(nuke_source), exist_ok=True)
        shutil.copy2(nuke_script_full, nuke_source)

        # PACKAGE
        nuke_package = self.settings['nuke_scripts']['package']['path'].format_map(
            Default(self.anatomy)).replace("\\", "/")
        os.makedirs(os.path.dirname(nuke_package), exist_ok=True)

        nuke.scriptSaveAs(nuke_package, overwrite=1)
        relative = self.settings['nuke_scripts']['package']['relative']
        project_custom = self.settings['nuke_scripts']['package']['relative_custom_project']
        project_template = self.settings['nuke_scripts']['package']['relative_custom_project_template']
        project = project_template.format_map(Default(self.anatomy)).replace("\\", "/")
        above = self.settings['nuke_scripts']['package']['relative_above_script']
        self.relink(script=nuke_package, relative=relative, above=above, project_custom=project_custom, project=project)

        # TARGET
        nuke_target = self.settings['nuke_scripts']['target']['path'].format_map(
            Default(self.anatomy)).replace("\\", "/")
        os.makedirs(os.path.dirname(nuke_target), exist_ok=True)
        nuke.scriptSaveAs(nuke_target, overwrite=1)
        relative = self.settings['nuke_scripts']['package']['relative']
        project_custom = self.settings['nuke_scripts']['target']['relative_custom_project']
        project_template = self.settings['nuke_scripts']['target']['relative_custom_project_template']
        project = project_template.format_map(Default(self.anatomy)).replace("\\", "/")
        above = self.settings['nuke_scripts']['target']['relative_above_script']
        self.relink(script=nuke_target, relative=relative, above=above, project_custom=project_custom, project=project)

        nuke_target_relative = self.settings['nuke_scripts']['target']['relative']

        """
        nuke.scriptOpen(nuke_package)
        for item in self.media_items:
            node = nuke.toNode(item['node_name'])
            print(item['node_name'])
        """

    def prepare_script(self):

        self.read_comp_data()

        # find duplicities
        self.find_media_duplicities()
        self.find_font_duplicities()
        self.find_gizmo_duplicities()

        # filter categories
        self.media_items_to_categories()

        # generate target paths and relink paths
        self.media_items_to_paths()
        self.font_items_to_paths()
        self.gizmo_items_to_paths()
        self.ocio_to_paths()

        # generate report
        self.make_report()
        #pprint.pprint(self.report)

        #print("\n\nPLUGS:\n")
        #pprint.pprint(self.loaded_plugins)

        #pprint.pprint(self.gizmo_items)
        #pprint.pprint(self.media_items)

    def process_script(self):

        # prepare copy list
        self.copy_media()

        # copy fonts
        self.copy_fonts()

        # copy gizmos
        self.copy_gizmos()

        if self.settings['gizmos']['to_groups']:
            pass
            #self.gizmos_to_groups()

        # copy ocio
        self.copy_ocio()

        # Make Nuke scripts
        self.make_nuke_scripts()

        # save report (end) m


if __name__ == "__main__":
    # log
    log = logging.getLogger("mylog")
    log.setLevel(logging.DEBUG)
    log.info('Started at: ' + time.strftime("%Y-%m-%d, %H:%M"))

    # get user info
    # anatomies is list of anatomy dicts, that contain workfile path
    # job destination is a parent folder of the package job
    # settings is a dict containing user picked packing settings


    anatomies, job_destination, settings = action_dialog()
    if anatomies and len(anatomies) > 0:
        # pprint.pprint(anatomies)
        # print("\n\n\n")
        # process each nuke script
        for anatomy in anatomies:
            one_nuke = PackNukeScript(anatomy, job_destination, settings)
            one_nuke.prepare_script()
            one_nuke.process_script()

    #TODO
    # gui
    # save report
    # logfile


