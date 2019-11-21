from __future__ import print_function

import os
from typing import Iterable, List, Tuple

from type_extractor import OverloadSet, Overload, Package, Class


def indent(text):
    splitted_text = text.splitlines(True)
    prefixed_lines = (('    ' + line if line.strip() else line) for line in splitted_text)

    return ''.join(prefixed_lines)


def format_overload_set(overload_set, bound=False):
    # type: (OverloadSet, bool) -> Iterable[str]

    def _get_format(is_ctor, has_docstring):
        ending = ' ...'
        if has_docstring:
            ending = (
                '\n'
                '    """\n'
                '{docstring}\n'
                '    """\n'
                '    ...'
            )

        if is_ctor:
            def_format = 'def {name}({optional_self}{args}):' + ending
        else:
            def_format = 'def {name}({optional_self}{args}) -> {return_type}:' + ending

        return def_format

    def get_optional_self(overload):
        # type: (Overload) -> str
        optional_self = ''
        if not (bound or overload.is_static and not overload_set.is_constructor):
            optional_self = 'self'
            if overload.argument_types:
                optional_self += ', '

        return optional_self

    def get_arguments(overload):
        # type: (Overload) -> str
        return ', '.join(
            '{arg_name}: {type}'.format(arg_name=arg_name, type=typ.proper_name)
            for arg_name, typ in zip(overload.argument_names, overload.argument_types)
        )

    for overload in overload_set.overloads:
        def_format = _get_format(overload_set.is_constructor, overload.docstring)
        overload_code = def_format.format(
            optional_self=get_optional_self(overload),
            name=overload_set.name,
            args=get_arguments(overload),
            return_type=overload.return_type.proper_name,
            docstring=indent(overload.docstring),
        )

        if overload.is_static and not overload_set.is_constructor and not bound:
            overload_code = '@staticmethod\n' + overload_code

        if len(overload_set.overloads) > 1:
            overload_code = '@overload\n' + overload_code

        yield overload_code


def format_imports(imports):
    for imp in imports:
        if isinstance(imp, str):
            yield 'import {}'.format(imp)
        elif isinstance(imp, tuple):
            module, member = imp
            yield 'from {} import {}'.format(module, member)


def format_pyi_class(cls, is_nested=False):
    # type: (Class, bool) -> str

    def _format_imports():
        if is_nested:
            return

        for formatted_import in format_imports(cls.requires):
            yield formatted_import

    def _format_methods():
        for overload_set in sorted(cls.methods):
            for fmt in format_overload_set(overload_set):
                yield fmt

    def _format_ctors():
        for overload_set in sorted(cls.constructors):
            for fmt in format_overload_set(overload_set):
                yield fmt

    def _format_properties():
        for prop in sorted(cls.properties):
            getter = (
                '    @property\n'
                '    def {name}(self) -> {getter_type}: ...{comment}'
            ).format(
                name=prop.name,
                getter_type=prop.getter_type.proper_name if prop.has_getter else 'None',
                comment='' if prop.has_getter else '  # No getter available.',
            )

            yield getter

            if prop.has_setter:
                setter = (
                    '    @{name}.setter\n'
                    '    def {name}(self, value: {setter_type}) -> None: ...'
                ).format(
                    name=prop.name,
                    setter_type=prop.setter_type.proper_name,
                )

                yield setter

    def _format_fields():
        for field in sorted(cls.fields):
            declaration = '    {name}: {type}'.format(
                name=field.name, type=field.my_type.proper_name,
            )
            if field.has_value:
                assignment = ' = {}'.format(field.value_repr)
                declaration += assignment
            yield declaration

    def _format_nested_classes():
        for nested_class in cls.nested_classes:
            nested_class_text = format_pyi_class(
                nested_class,
                is_nested=True,
            )
            indented_nested_class_text = indent(nested_class_text)
            yield indented_nested_class_text

    def _format_iterable():
        if cls.is_iterable:
            iter_obj = None
            for method in cls.methods:
                if method.name == 'next':
                    iter_obj = method.overloads[0].return_type.proper_name
                    break
            if iter_obj is not None:
                yield '    def __iter__(self) -> Iterator[{}]: ...'.format(iter_obj)
            else:
                yield '    def __iter__(self): ...'

    bases = ', '.join(base.proper_name for base in cls.bases)
    class_docs = ''
    if cls.docstring:
        class_docs = '    """\n{}\n    """\n\n'.format(indent(cls.docstring))

    return (
        '{imports}\n\n\n'
        '{class_header}\n'
        '{class_docs}'
        '{fields}\n\n'
        '{nested_classes}\n\n'
        '{ctors}\n\n'
        '{iterable}\n\n'
        '{methods}\n\n'
        '{properties}'
    ).format(
        imports='\n'.join(sorted(_format_imports())),
        class_header='class {name}({bases}):'.format(name=cls.name, bases=bases),
        ctors=indent('\n\n'.join(_format_ctors())),
        properties='\n\n'.join(_format_properties()),
        methods=indent('\n\n'.join(_format_methods())),
        fields='\n'.join(_format_fields()),
        nested_classes='\n\n'.join(_format_nested_classes()),
        iterable='\n\n'.join(_format_iterable()),
        class_docs=class_docs,
    )


def write_package_classes(root, package_path, package):
    # type: (str, str, Package) -> None
    for cls in package.classes:
        class_path = '{}.pyi'.format(os.path.join(root, package_path, cls.name))
        pyi_content = format_pyi_class(cls)
        with open(class_path, 'w') as f:
            f.write(pyi_content)


def update_imports(init_path, package):
    # type: (str, Package) -> None
    imports = set()

    if os.path.exists(init_path):
        with open(init_path, 'r') as f:
            imports.update(f.read().splitlines())

    imports.update(
        'from .{0} import {0} as {0}'.format(cls.name)
        for cls in package.classes
    )
    imports.update(
        'from . import {0} as {0}'.format(package.name.rpartition('.')[-1])
        for package in package.packages
    )

    with open(init_path, 'w') as f:
        f.write('\n'.join(sorted(imports)))


def get_package_path(package):
    # type: (Package) -> str
    return package.name.replace('.', '/')


def create_package_directories(root, packages):
    # type: (str, List[Package]) -> None
    for package in packages:
        package_path = get_package_path(package)
        path = os.path.join(root, package_path)
        if not os.path.exists(path):
            os.makedirs(path)


def get_all_packages(preparsed_packages):
    # type: (Tuple[Package, ...]) -> List[Package]
    """Get all packages, including nested ones"""
    stack = list(preparsed_packages)
    packages = []

    while stack:
        package = stack.pop()
        packages.append(package)
        stack.extend(package.packages)

    return packages


def create_type_hints(root, *packages):
    # type: (str, *Package) -> None
    all_packages = get_all_packages(packages)

    create_package_directories(root, all_packages)

    for package in all_packages:
        package_path = get_package_path(package)
        init_path = os.path.join(root, package_path, '__init__.pyi')
        update_imports(init_path, package)

        write_package_classes(root, package_path, package)
