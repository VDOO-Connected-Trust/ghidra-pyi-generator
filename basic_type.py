import re

import attr


@attr.s(eq=True)
class BasicType(object):
    name = attr.ib()  # type: str
    module = attr.ib()  # type: str
    is_array = attr.ib(default=False)  # type: bool
    is_iterator = attr.ib(default=False)  # type: bool

    REPLACEMENTS = {
        'boolean': 'bool',
        'java.lang.String': 'Text',
        'java.lang.Object': 'object',
        'java.math.BigInteger': 'long',
        'long': 'long',
        'B': 'int',  # byte
        'Z': 'bool',
        'C': 'int',  # char
        'S': 'int',  # short
        'I': 'int',
        'J': 'long',
        'F': 'float',
        'D': 'float',  # double
        'void': 'None',
        'short': 'int',
        'byte': 'int',
        'double': 'float',
        # Below this line are replacements from parsing Java code
        'char': 'int',  # char
        'java.lang.Boolean': 'bool',
        'java.lang.Integer': 'int',
        'java.lang.Long': 'long',
        'java.lang.Byte': 'int',
        'java.lang.Double': 'float',
        'java.lang.Short': 'int',
        'java.lang.Float': 'float',
    }

    @property
    def qualified_name(self):
        if self.is_builtin:
            return self.name

        return '{self.module}.{self.name}'.format(self=self)

    @property
    def proper_name(self):
        name = self.REPLACEMENTS.get(self.qualified_name, self.qualified_name)
        if self.is_array:
            return 'List[{}]'.format(name)
        elif self.is_iterator:
            return 'Iterator[{}]'.format(name)
        return name

    @property
    def requires(self):
        requires = set()

        if self.is_array:
            requires.add(('typing', 'List'))
        if self.is_iterator:
            requires.add(('typing', 'Iterator'))
        if self.proper_name == 'Text':
            requires.add(('typing', 'Text'))
        if self.proper_name == 'long':
            requires.add(('py3_compatibility', '*'))
        if '.' in self.proper_name and not self.is_builtin:
            requires.add(self.module)

        return requires

    @property
    def is_builtin(self):
        return self.module == str.__module__

    def is_overload_match(self, other):
        if not isinstance(other, BasicType):
            return False

        if self == other:
            return True

        if self.proper_name == other.proper_name:
            return True

        if self.is_iterator and other.qualified_name == 'java.util.Iterator':
            return True

        return False

    @staticmethod
    def from_type(t):
        # type: (type) -> BasicType
        is_array = t.__module__.startswith('[') or t.__name__.startswith('[')
        name = t.__name__.lstrip('[').rstrip(';').replace('$', '.')
        module = t.__module__.lstrip('[L')
        if module == 'java.util' and name == 'List':
            is_array = True
            name = 'object'
            module = str.__module__
        return BasicType(name=name, module=module, is_array=is_array)

    @staticmethod
    def from_java(definition):
        # type: (str) -> BasicType
        match = re.match(r'((?P<template>[\w.]+)<)?(?P<type>[\w.]+)(?P<array>\[\])?>?', definition)
        if match is None:
            raise ValueError('Invalid type definition: {}'.format(definition))

        type_name = match.group('type')

        is_array = False
        is_iterator = False
        if match.group('array'):
            is_array = True

        template = match.group('template')
        if template:
            if template == 'java.util.List':
                is_array = True
            elif template == 'java.util.Iterator':
                is_iterator = True
            elif template == 'java.util.ArrayList':
                is_array = True
            else:
                type_name = template

        module, _sep, name = type_name.rpartition('.')
        if not module:
            module = str.__module__
            name = type_name

        if name == 'T':
            name = 'object'

        basic_type = BasicType(name=str(name), module=str(module), is_array=is_array, is_iterator=is_iterator)
        if basic_type.proper_name == '.void':
            print(basic_type)
        return basic_type
