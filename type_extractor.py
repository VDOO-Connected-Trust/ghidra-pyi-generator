import keyword
from collections import defaultdict
from typing import List, Dict, Any, Optional, DefaultDict

import attr
import java.lang.reflect.Modifier

from basic_type import BasicType
from helper import ClassDoc, OverloadSetDoc, MethodDoc


def is_nested_class(parent, child):
    # type: (type, type) -> bool
    if parent.__module__ != child.__module__:
        return False

    if '$' not in child.__name__:
        return False

    child_parent_name = child.__name__.split('$')[0]
    if child_parent_name != parent.__name__:
        return False

    return True


def get_members(obj):
    # type: (Any) -> Dict[str,Any]
    members = {}
    for name in dir(obj):
        try:
            members[name] = getattr(obj, name)
        except AttributeError:
            # Some attrs are instance-attrs, and we can't get them via the class object.
            pass
        except TypeError:
            # Some attrs are write-only, so we can't get them.
            pass
        except java.lang.IllegalArgumentException:
            # Some values cannot be converted to Python types, so we are stuck.
            pass
        except java.lang.NoClassDefFoundError:
            pass

    # If something is in `__dict__` we want it directly from there.
    # Attribute resolution destroys reflection info when class fields are involved.
    members.update(obj.__dict__)

    return members


def make_valid_name(name):
    if keyword.iskeyword(name):
        return '{}_'.format(name)
    return name


def get_argument_names(argument_types, docs):
    # type: (List[BasicType], Optional[OverloadSetDoc]) -> List[str]
    if docs:
        overload_doc = docs.get_overload(argument_types)
        if overload_doc:
            return [make_valid_name(param.name) for param in overload_doc.params]

    return ['__a{}'.format(i) for i in range(len(argument_types))]


def get_return_type(return_type, docs):
    # type: (BasicType, Optional[MethodDoc]) -> BasicType

    if docs is None:
        return return_type

    return docs.return_type


@attr.s
class Overload(object):
    return_type = attr.ib()  # type: BasicType
    argument_types = attr.ib()  # type: List[BasicType]
    argument_names = attr.ib()  # type: List[str]
    is_static = attr.ib()  # type: bool
    docstring = attr.ib()  # type: Optional[str]

    @staticmethod
    def from_reflected_args(reflected_args, ctor_for=None, docs=None):
        # type: (Any, Any, Optional[OverloadSetDoc]) -> Overload
        if ctor_for is not None:
            return_type = ctor_for
        else:
            return_type = reflected_args.method.getReturnType()

        return_type = BasicType.from_type(return_type)
        argument_types = map(BasicType.from_type, reflected_args.method.getParameterTypes())

        argument_names = get_argument_names(argument_types, docs)

        docstring = ''
        if docs:
            overload_docs = docs.get_overload(argument_types)
            if overload_docs:
                docstring = overload_docs.javadoc
                argument_types = [param.type for param in overload_docs.params]
                return_type = get_return_type(return_type, overload_docs)

        return Overload(
            return_type=return_type,
            argument_types=argument_types,
            argument_names=argument_names,
            is_static=reflected_args.isStatic,
            docstring=docstring
        )

    @property
    def requires(self):
        return self.return_type.requires.union(*(t.requires for t in self.argument_types))


@attr.s
class OverloadSet(object):
    name = attr.ib()
    overloads = attr.ib()  # type: List[Overload]
    is_constructor = attr.ib(default=False)  # type: bool

    @staticmethod
    def from_reflected_function(reflected_function, docs=None):
        # type: (Any, Optional[OverloadSetDoc])->OverloadSet
        def _get_overloads():
            for reflected_args in reflected_function.argslist:
                if reflected_args is not None:
                    yield Overload.from_reflected_args(reflected_args, docs=docs)

        return OverloadSet(name=reflected_function.__name__, overloads=list(_get_overloads()))

    @staticmethod
    def from_reflected_constructor(reflected_constructor, cls, docs=None):
        def _get_overloads():
            for reflected_args in reflected_constructor.argslist:
                if reflected_args is not None:
                    yield Overload.from_reflected_args(reflected_args, ctor_for=cls, docs=docs)

        return OverloadSet(name='__init__', overloads=list(_get_overloads()), is_constructor=True)

    @property
    def requires(self):
        return set().union(*(overload.requires for overload in self.overloads))


@attr.s
class Property(object):
    name = attr.ib()
    getter_type = attr.ib()  # type: BasicType
    setter_type = attr.ib()  # type: BasicType

    @property
    def has_setter(self):
        return self.setter_type is not None

    @property
    def has_getter(self):
        return self.getter_type is not None

    @staticmethod
    def from_beanproperty(beanproperty, name):
        if beanproperty.setMethod:
            setter_type = beanproperty.setMethod.getParameterTypes()[0]
            setter_type = BasicType.from_type(setter_type)
        else:
            setter_type = None

        if beanproperty.getMethod:
            getter_type = beanproperty.getMethod.getReturnType()
            getter_type = BasicType.from_type(getter_type)
        else:
            getter_type = None

        return Property(name=name, setter_type=setter_type, getter_type=getter_type)


@attr.s
class Modifier(object):
    modifiers = attr.ib()  # type: int

    @property
    def is_static(self):
        return java.lang.reflect.Modifier.isStatic(self.modifiers)

    @property
    def is_final(self):
        return java.lang.reflect.Modifier.isFinal(self.modifiers)


def pretty_repr(value):
    if isinstance(value, long):  # NOQA: F821
        return hex(value)

    return repr(value)


@attr.s
class Field(object):
    name = attr.ib()  # type: str
    my_type = attr.ib()  # type: BasicType
    modifiers = attr.ib()  # type: Modifier
    value_repr = attr.ib()  # type: Optional[str]
    has_value = attr.ib()  # type: bool

    @staticmethod
    def from_reflectedfield(reflectedfield, name, cls):
        name = name
        my_type = reflectedfield.field.getType()
        modifiers = Modifier(reflectedfield.field.getModifiers())

        value_repr = None
        has_value = False

        if modifiers.is_static and modifiers.is_final:
            try:
                value = getattr(cls, name)
                value_repr = pretty_repr(value)
                has_value = True
            except java.lang.IllegalArgumentException:
                pass

        return Field(
            name=name,
            my_type=BasicType.from_type(my_type),
            modifiers=modifiers,
            value_repr=value_repr,
            has_value=has_value,
        )


@attr.s
class NamedObject(object):
    name = attr.ib()
    obj = attr.ib()


def group_by_typename(items):
    # type: (Dict[str,Any]) -> Dict[str, List[NamedObject]]
    groups = defaultdict(list)  # type: DefaultDict[str, List[NamedObject]]

    for name, obj in items.iteritems():
        type_name = type(obj).__name__
        groups[type_name].append(NamedObject(name=name, obj=obj))

    return groups


@attr.s
class Class(object):
    name = attr.ib()
    methods = attr.ib()  # type: List[OverloadSet]
    constructors = attr.ib()  # type: List[OverloadSet]
    properties = attr.ib()  # type: List[Property]
    fields = attr.ib()  # type: List[Field]
    nested_classes = attr.ib()  # type: List[Class]
    is_iterable = attr.ib()  # type: bool
    bases = attr.ib()  # type: List[BasicType]
    docstring = attr.ib(default=None)  # type: Optional[str]

    @staticmethod
    def from_class(cls, docs=None):
        # type: (type, Optional[ClassDoc]) -> Class
        # TODO: Handle the following typenames:
        #       beanevent, beaneventproperty, method_descriptor
        member_groups = group_by_typename(get_members(cls))  # type: Dict[str, List[NamedObject]]

        # Nested classes have funky names and we need to handle them.
        name = cls.__name__.rpartition('$')[-1]

        # The `__iter__` method is not in `__dict__`,
        # and is not a reflectedfunction, so we don't have any
        # type information on it.
        is_iterable = hasattr(cls, '__iter__')

        docstring = None
        if docs:
            docstring = docs.comment

        methods = []
        for nobj in member_groups['reflectedfunction']:
            method_docs = docs.get_overload_set(nobj.name) if docs else None
            method = OverloadSet.from_reflected_function(
                reflected_function=nobj.obj, docs=method_docs,
            )
            methods.append(method)

        constructors = []
        for nobj in member_groups['reflectedconstructor']:
            ctor_docs = docs.get_overload_set('<init>') if docs else None
            ctor = OverloadSet.from_reflected_constructor(
                reflected_constructor=nobj.obj, cls=cls, docs=ctor_docs,
            )
            constructors.append(ctor)

        return Class(
            name=name,
            methods=methods,
            properties=[
                Property.from_beanproperty(beanproperty=nobj.obj, name=nobj.name)
                for nobj in member_groups['beanproperty']
            ],
            constructors=constructors,
            fields=[
                Field.from_reflectedfield(reflectedfield=nobj.obj, name=nobj.name, cls=cls)
                for nobj in member_groups['reflectedfield']
            ],
            # There is no jsondoc for nested classes,
            # so we cannot grab it without adding HTML parsing.
            # TODO: Use HTML parsing to populate nested class documentation.
            nested_classes=[
                Class.from_class(nobj.obj)
                for nobj in member_groups['Class']
                if is_nested_class(cls, nobj.obj)
            ],
            is_iterable=is_iterable,
            bases=map(BasicType.from_type, cls.__bases__),
            docstring=docstring
        )

    @property
    def requires(self):
        requirements = (
            set()
            .union(*(member.requires for member in self.methods))
            .union(*(nested_class.requires for nested_class in self.nested_classes))
            .union(*(base.requires for base in self.bases))
        )
        if self.is_iterable:
            requirements.add(('typing', 'Iterator'))

        return requirements


@attr.s
class Package(object):
    name = attr.ib()  # type: str
    classes = attr.ib()  # type: List[Class]
    packages = attr.ib()  # type: List[Package]

    @staticmethod
    def from_package(package):
        packages = []
        classes = []
        for name, attr_ in get_members(package).iteritems():
            if name == '__name__':
                continue

            typename = BasicType.from_type(type(attr_)).proper_name

            if typename == 'javapackage':
                packages.append(Package.from_package(attr_))

            elif typename == 'java.lang.Class':
                try:
                    docs = ClassDoc('{}.{}'.format(package.__name__, name))
                except KeyError:
                    docs = None
                classes.append(Class.from_class(attr_, docs=docs))

        return Package(name=package.__name__, classes=classes, packages=packages)

    @property
    def requires(self):
        return set().union(*(cls.requires for cls in self.classes))
