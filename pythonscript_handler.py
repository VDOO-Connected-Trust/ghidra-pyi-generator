from __future__ import print_function

import os

try:
    import ghidra.python.PythonScript as PythonScript
except ImportError:
    # 11.2 renamed everything to Jython
    import ghidra.jython.JythonScript as PythonScript

import helper
import type_extractor
import type_formatter
from type_extractor import OverloadSet
from basic_type import BasicType
from type_formatter import format_imports


PYTHONSCRIPT_PROPERTIES = {
    'currentProgram': ghidra.program.database.ProgramDB,
    'currentAddress': ghidra.program.model.address.Address,
    'currentLocation': ghidra.program.util.ProgramLocation,
    'currentSelection': ghidra.program.util.ProgramSelection,
    'currentHighlight': ghidra.program.util.ProgramSelection,
    'monitor': ghidra.util.task.TaskMonitor,
}


def format_method_arguments(argument_types):
    return ', '.join(
        '__a{i}: {type}'.format(i=i, type=typ.proper_name) for i, typ in enumerate(argument_types)
    )


def format_overload_set(overload_set):
    def_format = 'def {name}({args}) -> {return_type}: ...'
    for overload in overload_set.overloads:
        overload_code = def_format.format(
            name=overload_set.name,
            args=format_method_arguments(overload.argument_types),
            return_type=overload.return_type.proper_name,
        )

        if len(overload_set.overloads) > 1:
            overload_code = '@overload\n' + overload_code
        yield overload_code


def is_ghidra_value(value):
    return type(value).__module__.partition('.')[0] == 'ghidra'


def is_ghidra_method(value):
    return (
        type(value).__name__ == 'instancemethod'
        and getattr(value, 'im_class', None) == PythonScript
    )


def is_instance_property(name):
    try:
        getattr(PythonScript, name)
    except AttributeError as e:
        if e.args[0].startswith('instance attr:'):
            return True
    return False


def get_type_signature(name, value):
    if name in PYTHONSCRIPT_PROPERTIES:
        t = BasicType.from_type(PYTHONSCRIPT_PROPERTIES[name])  # type: BasicType
        return '{}: {}'.format(name, t.proper_name), t.requires

    if is_ghidra_value(value):
        t = BasicType.from_type(type(value))  # type: BasicType
        return '{}: {}'.format(name, t.proper_name), t.requires

    if is_ghidra_method(value):
        overload_set = OverloadSet.from_reflected_function(value.im_func)
        return '\n'.join(format_overload_set(overload_set)), overload_set.requires

    return None


def get_formatted_overload_set(overload_set):
    return '\n\n'.join(type_formatter.format_overload_set(overload_set, bound=True))


def generate_ghidra_builtins(my_globals):
    builtins = (ghidra.program.flatapi.FlatProgramAPI, ghidra.app.script.GhidraScript)
    classes = [type_extractor.Class.from_class(cls) for cls in builtins]
    imports = set().union(*(cls.requires for cls in classes))

    def _format_overloads():
        for cls, builtin in zip(classes, builtins):
            class_name = '{}.{}'.format(builtin.__module__, builtin.__name__)
            try:
                docs = helper.ClassDoc(class_name)
            except KeyError:
                docs = None
            cls = type_extractor.Class.from_class(builtin, docs=docs)
            imports.update(cls.requires)
            for overload_set in cls.methods:
                if overload_set.name in my_globals:
                    yield (overload_set.name, get_formatted_overload_set(overload_set))

    methods = dict(_format_overloads())

    for name, value in my_globals.iteritems():
        if name in methods:
            continue

        signature = get_type_signature(name, value)
        if signature:
            code, requires = signature
            imports.update(requires)

            methods[name] = code

    return '\n'.join([
        '\n'.join(format_imports(sorted(imports))),
        '\n\n',
        '\n\n'.join(sorted(methods.values())),
    ])


def create_mock(pyi_root, my_globals):
    builtins = generate_ghidra_builtins(my_globals)
    with open(os.path.join(pyi_root, 'ghidra_builtins.pyi'), 'w') as f:
        f.write(builtins)
