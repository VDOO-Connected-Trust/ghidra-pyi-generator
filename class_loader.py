"""Load all classes from classes.list

To generate the `classes.list`,
open `api/overview-tree.html` from the Ghidra docs in a web-browser
and copy it's contents to a text file.
"""

import helper
import importlib
import re
import os
import java.lang


def get_class_name(line):
    match = re.search(r'[\w.]+', line)
    if match:
        return match.group(0)


def load_class(name):
    module_name, _sep, class_name = name.rpartition('.')
    module = importlib.import_module(module_name)
    getattr(module, class_name)


def parse_class_list(list_path=None):
    if list_path is None:
        list_path = os.path.join(os.path.dirname(__file__), 'classes.list')

    with open(list_path) as f:
        classes = f.readlines()

    for class_entry in classes:
        yield get_class_name(class_entry)


def load_all_classes(prefix='ghidra', list_path=None):
    parsed_classes = set(parse_class_list(list_path=list_path))
    jsondoc_classes = set(helper.get_jsondoc_classes())
    class_names = parsed_classes | jsondoc_classes

    for class_name in class_names:
        if class_name.startswith(prefix):
            try:
                load_class(class_name)
            except (java.lang.Throwable, Exception):
                print('Failed loading {}'.format(class_name))
