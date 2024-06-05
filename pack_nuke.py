# import necessary
import nuke
import os
import glob
import re
import pprint


def get_default_category():
    default_category = {
        "default_category": {
            "path": {
                "root_template": "{job}/{folder[name]}/{category}",
                "root_template_relink": "{job}/{folder[name]}/{category}",
                "top_folder": "{job}/{folder[name]}/{category}",
                "top_folder_relink": "{job}/{folder[name]}/{category}"
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


def get_nuke_pack_project_settings():
    """
    This will return settings dict
    """
    # for testing only
    # TODO get project settings

    settings = {"toVendor1": {
        "job": {
            "job_name_default": "PackNuke_Dazzle2Vendor1_{yyyy}-{mm}-{dd}_v000",
            "job_name_check": "PackNuke_Dazzle2Vendor1_20\d\d-\d\d-\d\d_v\d\d\d",
            "job_root": "{project[name]}/out/packNuke/Dazzle2Vendor1"
        },
        "nuke_scripts": {
            "nuke_scripts_source": {
                "nuke_scripts_source_copy": True,
                "nuke_scripts_source_path": "{job[root]}/{job[name]}/{folder[name]}/{script_name}_source.nk"
            },
            "nuke_scripts_package": {
                "nuke_scripts_package_copy": True,
                "nuke_scripts_package_path": "{job[root]}/{job[name]}/{folder[name]}/{script_name}_check.nk",
                "nuke_scripts_package_path_relink": "/vendor1_relink_root/{folder[name]}/nuke/{script_name}_source.nk",
                "nuke_scripts_package_relative": True
            },
            "nuke_scripts_target": {
                "nuke_scripts_target_copy": True,
                "nuke_scripts_target_path": "{job[root]}/{job[name]}/{folder[name]}/{script_name}_check.nk",
                "nuke_scripts_target_path_relink": "/vendor1_relink_root/{folder[name]}/nuke/{script_name}_source.nk",
                "nuke_scripts_target_relative": True
            }
        },
        "hashes": {
            "hashes_generate": True
        },
        "categories": {
            "test_category": {
                "path": {
                    "root_template": "{job}/{folder[name]}/{category}",
                    "root_template_relink": "{job}/{folder[name]}/{category}",
                    "top_folder": "{job}/{folder[name]}/{category}",
                    "top_folder_relink": "{job}/{folder[name]}/{category}"
                },
                "filter_options": {
                    "skip_disconnected": False,
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
            "root_template": "{job}/{folder[name]}/fonts",
            "root_template_relink": "/vendor1_relink_root/{folder[name]}/fonts",
            "top_folder": "",
            "top_folder_relink": "",
            "skip_disconnected": True,
            "skip_disabled": True
        },
        "gizmos": {
            "enabled": True,
            "to_groups": True,
            "root_template": "{job}/{folder[name]}/gizmos",
            "root_template_relink": "/vendor1_relink_root/{folder[name]}/gizmos",
            "top_folder": "",
            "top_folder_relink": "",
            "skip_disconnected": True,
            "skip_disabled": True
        },
        "ocio": {
            "enabled": True,
            "root_template": "{job}/{folder[name]}/ocio",
            "root_template_relink": "/vendor1_relink_root/{folder[name]}/ocio",
            "top_folder": "",
            "top_folder_relink": "",
            "subfolders": True
        }
    }
    }
    return settings


def get_anatomy():
    # for testing only
    # TODO get anatomy

    anatomy = {
        "studio[name]": "Dazzle",
        "studio[code]": "dzl",
        "user": "john.doe",
        "project[name]": "DP1234_project",
        "project[code]": "dp1234_prj",
        "project": {
            "name": "DP1234_project",
            "code": "dp1234_prj",
        },
        "asset": "mw_119_12_0340",
        "folder[name]": "mw_119_12_0340",
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
        "dd": "30",
        "ddd": "Thu",
        "dddd": "Thursday",
        "m": "5",
        "mm": "05",
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

    # get project settings
    settings = get_nuke_pack_project_settings()

    # this is project anatomy
    anatomy = get_anatomy()

    # get first pack profile
    profile_name_first = list(settings)[0]

    profile_names = " ".join(list(settings))
    job_default_folder = settings[profile_name_first]["job"][
        "job_name_default"]
    job_default_check = settings[profile_name_first]["job"]["job_name_check"]
    job_default_path = settings[profile_name_first]["job"]["job_root"]

    # show dialog
    # TODO

    # fake user input
    # user_job_folder = job_default_folder.format_map(Default(anatomy)).replace("\\", "/")
    # user_job_path = job_default_path.format_map(Default(anatomy)).replace("\\", "/")
    user_job_folder = job_default_folder.format(**anatomy).replace("\\", "/")
    user_job_path = job_default_path.format(**anatomy).replace("\\", "/")
    user_job_profile = profile_name_first

    # validate user input
    if not re.match(job_default_check, user_job_folder):
        print(
            "Error! Make sure folder name matches convention:\n{}\n{}".format(
                job_default_check, user_job_folder))

    job_destination = user_job_path + "/" + user_job_folder  # no backslash, nuke hates it

    # now get a list of "workfile anatomies"
    # will fake it for now
    anatomy = get_anatomy()
    anatomy['job'] = user_job_folder  # add job name
    anatomies = [anatomy]  # fake it for one Nuke script

    return anatomies, job_destination, settings.get(user_job_profile)


class PackNukeScript:
    def __init__(self, anatomy, job_destination, settings):

        self.anatomy = anatomy
        self.job_destination = job_destination
        self.settings = settings

        self.media_items = []
        self.font_items = []
        self.gizmo_items = []
        self.loaded_plugins = []
        self.categories = {}
        self.media_copy_list = []

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

    def prepend_project_directory(self, path, project_dir=None,
                                  evaluate_project_directory=True):
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
                view_files.append(
                    knob_path.replace(r'%v', view).replace(r'%V', view))
        else:
            # if if stereo files not used, do not replace anything
            view_files = [knob_path]

        # overwrite knob_path value with new value per view
        for knob_path in view_files:

            # get TCL evaluated string
            knob_path_tcl = self.eval_tcl(knob_path)

            # get parent directory
            knob_path_parent_dir = os.path.dirname(knob_path_tcl)

            # try appending project root folder, if the dir does not exist
            if not os.path.exists(knob_path_parent_dir):
                knob_path_project_dir = self.prepend_project_directory(
                    knob_path_parent_dir)
                if os.path.isdir(knob_path_project_dir):
                    project_dir = True
                    knob_path_parent_dir = knob_path_project_dir
                    knob_path_tcl = self.prepend_project_directory(
                        knob_path_tcl)

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
                    wildcard_path = knob_path_tcl.replace(regex_file,
                                                          wildcards)
                    # get all files in directory
                    files = glob.glob(wildcard_path)
                    for each_file in files:
                        paths.append(each_file.replace('\\', '/'))

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
                    filename = filename_split[
                                   -len(filename_split)] + wildcards + \
                               filename_split[-1]
                    # full file path
                    wildcard_path = os.path.join(knob_path_parent_dir,
                                                 filename).replace('\\', '/')

                    # get all files that match wildcard pattern
                    files = glob.glob(wildcard_path)
                    for each_file in files:
                        paths.append(each_file.replace('\\', '/'))

                # if not a sequence
                else:
                    # append this file to paths, if it exists
                    if os.path.isfile(knob_path_tcl):
                        paths.append(knob_path_tcl)

                    # check if it is a relative (project directory) path
                    elif os.path.isfile(
                            self.prepend_project_directory(knob_path_tcl)):
                        paths.append(
                            self.prepend_project_directory(knob_path_tcl))
        # return result
        return paths, project_dir

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

            gizmo = type(node) == nuke.Gizmo
            if gizmo:
                return node.Class() if node.Class().endswith(
                    '.gizmo') else node.Class() + '.gizmo'
            else:
                return ''

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

        def store_gizmo_item(gizmo_name, gizmo_items, each_node, node_disabled,
                             node_disconnected):

            if gizmo_name != '':

                gizmo_path_found = False
                gizmo_path = ''
                for each_plugin_path in nuke.pluginPath():
                    gizmo_path = os.path.join(each_plugin_path,
                                              gizmo_name).replace('\\', '/')
                    if os.path.isfile(gizmo_path):
                        gizmo_path_found = False
                        break
                if gizmo_path_found:
                    if os.path.isfile(gizmo_path):
                        gizmo_item = {
                            'gizmo_name': gizmo_name,
                            'gizmo_path': gizmo_path,
                            'nodes': [each_node],
                            'node_disabled': node_disabled,
                            'node_disconnected': node_disconnected,
                            'size': os.path.getsize(gizmo_path)
                        }

                        i = 0
                        already_found = False
                        for g in gizmo_items:
                            if g['gizmo_name'] == gizmo_name:
                                if g['node_disabled'] == node_disabled:
                                    if g['node_disconnected'] == node_disconnected:
                                        already_found = True
                                        gizmo_items[i]['nodes'].append(
                                            each_node)
                            i += 1
                        if not already_found:
                            gizmo_items.append(gizmo_item)

            return gizmo_items

        def get_font_info(font_items):
            """
            fill missing info from getFonts
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
                        to_match = found_font['font_family'] + found_font[
                            'font_style']
                        found_font['path'] = None
                        for font in all_fonts:
                            check = font[0] + font[1]
                            if to_match == check:
                                found_font['path'] = font[2]
                                found_font['font_index'] = font[3]
                                break
            return font_items

        def get_media_item(node, knob, path, disabled, disconnected):
            # get real paths (file path list + project dir bool)
            real_knob_paths, project_dir = self.get_real_knob_paths(path)

            # make new list for new paths with their per-file size included
            all_files_with_sizes = []

            # get total file size
            total_size = 0
            if real_knob_paths is None:
                return None

            for each_file in real_knob_paths:
                size = os.path.getsize(each_file)
                total_size += size
                all_files_with_sizes.append([each_file, size])

            # check if the path exists
            exists = False
            if len(real_knob_paths) > 0:
                exists = True

            item = {
                'node': node,
                'knob': knob,
                'node_class': str(node.Class()),
                'node_name': str(node.fullName()),
                'exists': exists,
                'found_path': path,
                'all_files_with_sizes': all_files_with_sizes,
                'total_size': total_size,
                'project_dir': project_dir,
                'node_disabled': disabled,
                'node_disconnected': disconnected,
                'categories': [],
                'category_files': {},
                'tokens': {},
                'duplicate_of': None
            }
            return item

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
                gizmo_items = store_gizmo_item(gizmo_name, gizmo_items,
                                               each_node, node_disabled,
                                               node_disconnected)

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
                                'disabled': node_disabled,
                                'disconnected': node_disconnected,
                                'path': found_path.replace('\\', '/'),
                                'duplicate_of': None,
                                'font_files': {}
                            }
                            font_items.append(one_font)

                        else:
                            # file knob that is not a font
                            media_item = get_media_item(each_node, curr_knob,
                                                        found_path,
                                                        node_disabled,
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
                            'disabled': node_disabled,
                            'disconnected': node_disconnected,
                            'path': None,
                            'duplicate_of': None,
                            'font_files': {}
                        }
                        font_items.append(one_font)

            percent = int(
                round(float(i_node) / float(progress_total) * 100 / 2))
            # print('Done {}% of Nodes'.format(percent))
            i_node += 1

        self.media_items = media_items
        self.font_items = get_font_info(font_items)
        self.gizmo_items = gizmo_items
        self.loaded_plugins = get_loaded_plugins()

    def media_items_to_categories(self):

        def is_media_item_matching(media_item, paths, filter_options,
                                   filter_list):

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

            def match_node_class(filter, node_class):
                """
                Filter check is ignored, only matches the class name
                """
                if node_class is None:
                    return None

                node_list = filter['search'].strip().split(' ')
                if node_list is None or len(node_list) == 0:
                    return None

                if node_class in node_list:
                    if not filter['invert']:
                        # print("Match_class matched")
                        return node_class
                    else:
                        # print("Match_class not matched, 'cause of invert")
                        return None
                else:
                    if not filter['invert']:
                        # print("Match_class not matched")
                        return None
                    else:
                        # print("Match_class matched, 'cause of invert")
                        return node_class

            if filter_options['skip_disconnected'] and media_item[
                'node_disconnected']:
                # should skip disconnected
                print("Media Item {} skipped: disconnected".format(
                    media_item['node_name']))
                return False, None
            if filter_options['skip_disabled'] and media_item['node_disabled']:
                # should skip disabled
                print("Media Item {} skipped: disabled".format(
                    media_item['node_name']))
                return False, None
            if media_item['all_files_with_sizes'] and len(
                    media_item['all_files_with_sizes']) > 0:
                full_path = media_item['all_files_with_sizes'][0][0]
                _dir, file_name = os.path.split(full_path)
            else:
                print("Media Item {} skipped: no file found".format(
                    media_item['node_name']))
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
                    match = match_node_class(one_filter,
                                             media_item['node_class'])

                if match is not None:
                    tokens[one_filter['token_name']] = match
                    matches += 1
            print("Tokens {}, matches {}".format(tokens, matches))

            if (filter_options[
                    'combine_filters'].lower() == 'and' and matches == len(
                    filter_list)) or (
                    filter_options[
                        'combine_filters'].lower() == 'or' and matches > 0):
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
                filter_options = default_category['default_category'][
                    'filter_options']
            # get filters
            filter_list = category.get('filters')
            if not filter_list:
                filter_list = default_category['default_category']['filters']

            for media_item in self.media_items:
                print("media_items_to_categories: checking {} {}".format(
                    media_item['node_name'], category_name))
                matching, more_tokens = is_media_item_matching(media_item,
                                                               paths,
                                                               filter_options,
                                                               filter_list)
                if matching:
                    # add category name to media item
                    cats = media_item.get('categories')
                    if cats is not None:
                        media_item['categories'].append(category_name)
                    else:
                        media_item['categories'] = [category_name]

                    # print("Added match to categories: {}".format(media_item['categories']))

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
                    if media_item['all_files_with_sizes'] == check_item[
                        'all_files_with_sizes']:
                        check_item['duplicate_of'] = media_item

    def find_font_duplicities(self):

        for font_item in self.font_items:
            if font_item['duplicate_of'] is None:
                for check_item in self.font_items:
                    if check_item == font_item:
                        continue
                    if font_item['path'] == check_item['path']:
                        check_item['duplicate_of'] = font_item

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
            all_file_names = []
            for one_file in media_item['all_files_with_sizes']:
                all_file_names.append(one_file[0].split('/')[-1])

            if cats is not None:
                for one_category in cats:
                    all_tokens['category'] = one_category
                    all_tokens['node[name]'] = media_item['node_name']
                    all_tokens['node[class]'] = media_item['node_class']
                    cat_set = self.settings['categories'][one_category]
                    r_t = cat_set['path']['root_template'].format(
                        **all_tokens).replace("\\", "/")
                    r_t_r = cat_set['path']['root_template_relink'].format(
                        **all_tokens).replace("\\", "/")
                    t_f = cat_set['path']['top_folder'].format(
                        **all_tokens).replace("\\", "/")
                    t_f_r = cat_set['path']['top_folder_relink'].format(
                        **all_tokens).replace("\\", "/")

                    media_item['category_files'][one_category] = {
                        'template': r_t + '/' + t_f,
                        'template_relink': r_t_r + '/' + t_f_r,
                        'target': [r_t + '/' + t_f + '/' + f for f in
                                   all_file_names],
                        'relink': [r_t_r + '/' + t_f_r + '/' + f for f in
                                   all_file_names]
                    }

    def font_items_to_paths(self):
        """
        Fills font_item['font_files']
        template and template_relink are paths with tokens filled
        target and relink are list of paths for every file
        """

        _stngs = self.settings['fonts']
        for font_item in self.font_items:
            tokens = {'node': font_item['node_name'],
                      'class': font_item['node_class'],
                      'font': font_item['font_family']}
            all_tokens = {**self.anatomy, **tokens}
            all_file_names = []
            file_name = font_item['path'].split('/')[-1]

            r_t = _stngs['root_template'].format(**all_tokens).replace("\\",
                                                                       "/")
            r_t_r = _stngs['root_template_relink'].format(
                **all_tokens).replace("\\", "/")

            t_f = _stngs['top_folder'].format(**all_tokens).replace("\\", "/")
            if t_f != '':
                _template_full = r_t + '/' + t_f
            else:
                _template_full = r_t

            t_f_r = _stngs['top_folder_relink'].format(**all_tokens).replace(
                "\\", "/")
            if t_f_r != '':
                _template_full_relink = r_t_r + '/' + t_f_r
            else:
                _template_full_relink = r_t_r

            font_item['font_files'] = {
                'template': _template_full,
                'template_relink': _template_full_relink,
                'target': [_template_full + '/' + file_name],
                'relink': [_template_full_relink + '/' + file_name]
            }

    def prepare_media_copy_list(self):

        for media_item in self.media_items:
            if media_item['duplicate_of'] is None:
                for one_category, paths in media_item[
                    'category_files'].items():
                    for i in range(0, len(media_item['all_files_with_sizes'])):
                        self.media_copy_list.append(
                            [media_item['all_files_with_sizes'][i][0],
                             paths['target'][i]])

    def prepare_script(self):

        # script info
        nuke_script = nuke.root().name()
        nuke_script_size = os.path.getsize(nuke_script)

        self.read_comp_data()

        # find duplicities
        self.find_media_duplicities()
        self.find_font_duplicities()

        # filter categories
        self.media_items_to_categories()

        # generate target paths and relink paths
        self.media_items_to_paths()
        self.font_items_to_paths()

        # prepare copy list
        self.prepare_media_copy_list()

        # save report (start)

        print("\n\nmedia items:\n")
        for one in self.media_items:
            if one['duplicate_of'] is None:
                # pprint.pprint(one)
                print(one['found_path'])
                print(one['category_files'])
                print('\n\n')

        print("\n\nFONTS:\n")
        # pprint.pprint(self.font_items)
        for one in self.font_items:
            if one['duplicate_of'] is None:
                pprint.pprint(one)

        print("\n\nPLUGS:\n")
        pprint.pprint(self.loaded_plugins)

        print("\n\nGIZMOS\n")
        pprint.pprint(self.gizmo_items)

    def process_script(self):
        pass

        # copy media

        # copy fonts

        # copy gizmos

        # copy ocio

        # relink Nuke script

        # verify files

        # save report (end)


if __name__ == "__main__":

    # get user info
    # anatomies is list of anatomy dicts, that contain workfile path
    # job destination is a parent folder of the package job
    # settings is a dict containing user picked packing settings
    anatomies, job_destination, settings = action_dialog()
    if anatomies and len(anatomies) > 0:
        # process each nuke script
        for anatomy in anatomies:
            one_nuke = PackNukeScript(anatomy, job_destination, settings)
            one_nuke.prepare_script()
            one_nuke.process_script()



