import os
import shutil


def generate_package(pyi_root, ghidra_version):

    setup_code = """
from setuptools import setup
import os

def find_stub_files():
    result = []
    package = 'ghidra-stubs'
    for root, dirs, files in os.walk(package):
        for file in files:
            if file.endswith('.pyi'):
                file = os.path.relpath(os.path.join(root,file), start=package)
                result.append(file)
    return result

setup(name= 'ghidra-stubs',
version='{}',
author='Tamir Bahar',
packages=['ghidra-stubs'],
package_data={{'ghidra-stubs': find_stub_files()}})
    """.format(ghidra_version)

    stub_folder = os.path.join(pyi_root, 'ghidra-stubs')
    os.rename(os.path.join(pyi_root, 'ghidra'), stub_folder)
    shutil.copy2(os.path.join(pyi_root, 'ghidra_builtins.pyi'), stub_folder)
    with open(os.path.join(pyi_root, 'setup.py'), 'w') as setup_file:
        setup_file.write(setup_code)

    print('Run `pip install {}` to install ghidra-stubs package'.format(pyi_root))