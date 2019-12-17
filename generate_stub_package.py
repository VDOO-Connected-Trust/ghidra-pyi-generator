import os


def generate_package(pyi_root, ghidra_version):

    setup_code = """
from setuptools import setup
import os

def find_stub_files():
    result = []
    package = 'ghidra'
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

    os.rename(os.path.join(pyi_root, 'ghidra'), os.path.join(pyi_root, 'ghidra-stubs'))
    with open(os.path.join(pyi_root, 'setup.py'), 'w') as setup_file:
        setup_file.write(setup_code)

    print('Run `pip install {}` to install ghidra-stubs package'.format(pyi_root))