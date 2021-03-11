from __future__ import print_function

import zipfile
from collections import defaultdict
import json
import os

import attr
from typing import Optional, List

import java.lang
from ghidra.framework import Application
from basic_type import BasicType


def get_jsondoc_basepath():
    return os.path.join(
        Application.getUserCacheDirectory().getAbsolutePath(),
        'GhidraAPI_javadoc',
        Application.getApplicationVersion(),
        'api',
    )

def extract_jsondoc():
    zip_location = os.path.join(Application.getInstallationDirectory().getAbsolutePath(), "docs/GhidraAPI_javadoc.zip")
    extract_dir = os.path.join(
        Application.getUserCacheDirectory().getAbsolutePath(),
        'GhidraAPI_javadoc',
        Application.getApplicationVersion())

    zip_file = zipfile.ZipFile(zip_location)
    zip_file.extractall(extract_dir)

def are_docs_available():
    return os.path.exists(get_jsondoc_basepath())


def get_jsondoc(class_name):
    path_without_ext = os.path.join(get_jsondoc_basepath(), class_name.replace('.', '/'))
    json_path = '{}.json'.format(path_without_ext)

    try:
        with open(json_path) as f:
            return json.load(f)
    except (IOError, KeyError):
        pass


def json_path_to_class_name(root, name, jsondoc_basepath):
    json_path = os.path.join(root, name)
    class_path = os.path.relpath(json_path, jsondoc_basepath)
    class_path_without_extension = os.path.splitext(class_path)[0]
    class_name = class_path_without_extension.replace(os.path.sep, '.')
    return str(class_name)


def get_jsondoc_classes():
    jsondoc_basepath = get_jsondoc_basepath()
    for root, _dirs, names in os.walk(jsondoc_basepath):
        for name in names:
            if name.endswith('.json'):
                yield json_path_to_class_name(root, name, jsondoc_basepath)


@attr.s
class ParamDoc(object):
    jsondoc = attr.ib()

    @property
    def name(self):
        return self.jsondoc['name']

    @property  # NOQA: A003
    def type(self):
        return BasicType.from_java(self.jsondoc['type_long'])

    @property
    def comment(self):
        return self.jsondoc['comment']


class MethodDoc(object):
    def __init__(self, jsondoc):
        self.jsondoc = jsondoc

    @property
    def comment(self):
        return self.jsondoc['comment']

    @property
    def return_type(self):
        return BasicType.from_java(self.jsondoc['return']['type_long'])

    @property
    def javadoc(self):
        return self.jsondoc['javadoc']

    @property
    def params(self):
        return map(ParamDoc, self.jsondoc['params'])


@attr.s
class OverloadSetDoc(object):
    overloads_jsondoc = attr.ib()

    @staticmethod
    def is_matching_overload(required_args, provided_args):
        # type: (List[BasicType], List[BasicType]) -> bool
        if len(required_args) != len(provided_args):
            return False

        return all(
            required.is_overload_match(provided)
            for required, provided
            in zip(required_args, provided_args)
        )

    def get_overload(self, param_types):
        # type: (List[BasicType]) -> Optional[MethodDoc]
        for overload in self.overloads_jsondoc:
            doc_param_types = [
                BasicType.from_java(param['type_long']) for param in overload['params']
            ]
            if self.is_matching_overload(doc_param_types, param_types):
                return MethodDoc(overload)
        return None


class ClassDoc(object):
    def __init__(self, class_name):
        self.class_name = class_name  # type: str
        self.jsondoc = get_jsondoc(class_name)

        if self.jsondoc is None:
            raise KeyError('No docs for {}'.format(class_name))

        self.methods = self._map_methods()

    def _map_methods(self):
        methods = defaultdict(list)
        for method in self.jsondoc['methods']:
            methods[method['name']].append(method)

        return methods

    @property
    def extends_doc(self):
        if hasattr(self, '_extends_doc'):
            return self._extends_doc

        self._extends_doc = ClassDoc(self.extends)
        return self._extends_doc

    @property
    def implements_doc(self):
        if hasattr(self, '_implemented_doc'):
            return self._implemented_doc

        self._implemented_doc = ClassDoc(self.extends)
        return self._implemented_doc

    @property
    def comment(self):
        return self.jsondoc['comment']

    @property
    def extends(self):
        return self.jsondoc.get('extends', None)

    @property
    def implements(self):
        return self.jsondoc.get('implements', None)

    @property
    def name(self):
        return self.jsondoc['name']

    def _get_overload_set(self, name):
        try:
            extend_overload_set = self.extends_doc._get_overload_set(name)
        except (java.lang.Throwable, Exception):
            extend_overload_set = []

        try:
            implements_overload_set = self.implements_doc._get_overload_set(name)
        except (java.lang.Throwable, Exception):
            implements_overload_set = []

        return self.methods.get(name, []) + extend_overload_set + implements_overload_set

    def get_overload_set(self, name):
        return OverloadSetDoc(self._get_overload_set(name))
