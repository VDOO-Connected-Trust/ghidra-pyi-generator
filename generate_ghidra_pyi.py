# Generate .pyi's for Ghidra.
# @category: IDE Helpers
from __future__ import print_function
import type_formatter

import ghidra
from __main__ import askDirectory, askYesNo, getGhidraVersion

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

    setup_code = """
from setuptools import setup
import os

packages = ['ghidra-stubs']

package_data = {'': ['*']}



def find_stub_files():
    result = []
    for root, dirs, files in os.walk('ghidra-stubs'):
        for file in files:
            if file.endswith('.pyi'):
                if os.path.sep in root:
                    sub_root = root.split(os.path.sep, 1)[-1]
                    file = os.path.join(sub_root, file)
                result.append(file)
    return result

setup_kwargs = {
'name': 'ghidra-stubs',
    'version': '%s',
    'author': 'Tamir Bahar',
    'packages': packages,
    'package_data': {'ghidra-stubs': find_stub_files()},
}


setup(**setup_kwargs)
""" % (getGhidraVersion())

    import os
    os.rename(os.path.join(pyi_root, 'ghidra'), os.path.join(pyi_root, 'ghidra-stubs'))
    with open(os.path.join(pyi_root, 'setup.py'), 'w') as setup_file:
        setup_file.write(setup_code)

    print("Run `pip install %s` to install ghidra-stubs package" % pyi_root)

if __name__ == '__main__':
    main()
