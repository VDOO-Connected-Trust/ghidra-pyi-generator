# Generate .pyi's for Ghidra.
# @category: IDE Helpers
from __future__ import print_function
import type_formatter

import ghidra
from __main__ import askDirectory, askYesNo, getGhidraVersion

from generate_stub_package import generate_package

import class_loader
import type_extractor
import pythonscript_handler
import helper

my_globals = globals().copy()


def main():
    # type: () -> None
    if not helper.are_docs_available():
        helper.extract_jsondoc()
    try:
        pyi_root = askDirectory('.pyi root directory', 'Select').getPath()
        print(pyi_root)

    except ghidra.util.exception.CancelledException:
        print('Generation canceled: No output directory selected.')
        return

    class_loader.load_all_classes(prefix='ghidra.')

    pythonscript_handler.create_mock(pyi_root, my_globals)

    ghidra_package = type_extractor.Package.from_package(ghidra)
    type_formatter.create_type_hints(pyi_root, ghidra_package)

    generate_package(pyi_root, getGhidraVersion())

if __name__ == '__main__':
    main()
