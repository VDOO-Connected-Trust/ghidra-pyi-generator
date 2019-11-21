# Generate .pyi's for Ghidra.
# @category: IDE Helpers
from __future__ import print_function
import type_formatter

import ghidra
from __main__ import askDirectory, askYesNo

import class_loader
import type_extractor
import pythonscript_handler
import helper

my_globals = globals().copy()


def main():
    # type: () -> None
    if not helper.are_docs_available():
        continue_without_docs = askYesNo(
            'Missing API Documentation',
            'Ghidra API documentation is missing.\n'
            'Documentation is required to generate docstrings,\n'
            'argument names, and to find some of the classes.\n'
            '\n'
            'Would you like to continue without the API documentation?',
        )

        if not continue_without_docs:
            print('Generation canceled: Missing API documentation.')
            print('To make the API documentation available, ', end='')
            print('click "Ghidra API Help" in the "Help" menu.')
            print('Once the extraction is complete, re-run this script to generate the .pyi files.')
            return

        print('Continuing without API documentation. Expect partial results.')

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


if __name__ == '__main__':
    main()
