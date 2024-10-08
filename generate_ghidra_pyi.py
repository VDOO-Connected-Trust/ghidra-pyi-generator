# Generate .pyi's for Ghidra.
# @category: IDE Helpers
from __future__ import print_function
import type_formatter

import ghidra
# Make this script work with the stubs in an IDE
try:
    from ghidra.ghidra_builtins import *
except:
    pass
from __main__ import askDirectory, askYesNo, getGhidraVersion

from generate_stub_package import generate_package

import class_loader
import type_extractor
import pythonscript_handler
import helper
import os

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

    compatibility_path = os.path.join(pyi_root, 'py3_compatibility.pyi')
    with open(compatibility_path, 'w') as f:
        f.write('import sys\nif sys.version_info.major >= 3:\n    long = int\n')

    ghidra_package = type_extractor.Package.from_package(ghidra)
    type_formatter.create_type_hints(pyi_root, ghidra_package)

    package_version = "DEV"
    if isRunningHeadless():
        # We are running in an headless environment and this might be an automated CI build
        # so we try getting an extra argument that is supposed to be the git commit tag so the package version is a combination
        # of the ghidra version and the version of the stub generating code
        try:
            package_version = askString("Package version", "Please specify package version")
        except:
            pass
    generate_package(pyi_root, getGhidraVersion(), stub_version=package_version)

if __name__ == '__main__':
    main()
