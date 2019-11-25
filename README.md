# Ghidra `.pyi` Generator

The Ghidra `.pyi` Generator generates `.pyi` [type stubs][pep-0484]
for the entire Ghidra API.
Those stub files can later be used in PyCharm to enhance the development experience.

You can either use the stubs released [here][latest-release], or follow the instructions below to generate them yourself.

To use the stubs in PyCharm, follow the instructions in [Install, uninstall, and upgrade interpreter paths][interpreter-paths].

### Using The Stubs

Once installed, all you need to do is import the Ghidra modules as usual, and PyCharm will do the rest.

```python
import ghidra
```

To get support for the Ghidra builtins, you need to import them as well. The type hints for those exist in
the generated `ghidra_builtins.pyi` stub. Since it is not a real Python module, importing it at runtime will fail.
But the `.pyi` gives PyCharm all the information it needs to help you.

```python
try:
    from ghidra_builtins import *
except:
    pass
```

Once done, just code & enjoy.

![Pycharm Demo][pycharm-demo]


## Dependencies

### Ghidra Docs

To properly extract all types from Ghidra, make sure to extract the API documentation.

1. Open the Ghidra CodeBrowser
2. Go to `Help -> Ghidra API Help`
3. Wait for Ghidra to extract the docs

### Python Packages

The script depends on both the `attr` and `typing` packages.

```bash
# Create a virtualenv for Ghidra packages.
# It is important to use Python2.7 for this venv!
# If you want, you can skip this step and use your default Python installation.
mkvirtualenv ghidra
 
# Create Jython's site-pacakges directory.
jython_site_packages="~/.local/lib/jython2.7/site-packages"
mkdir -p $jython_site_packages
 
# Create a PTH file to point Jython to Python's site-packages directories.
# Again, this has to be Python2.7.
python -c "import site; print(site.getusersitepackages()); print(site.getsitepackages()[-1])" > $jython_site_packages/python.pth
 
# Use pip to install packages for Ghidra
pip install attrs typing
```

## Creating the `.pyi` files

1. Add this directory to the `Script Directories` in the Ghidra Script Manager
2. Refresh the script list
3. Run `generate_ghidra_pyi.py` (will be located under `IDE Helpers`)
4. When a directory-selection dialog appears, choose the directory you'd like to save the `.pyi` files in.


[interpreter-paths]: https://www.jetbrains.com/help/pycharm/installing-uninstalling-and-reloading-interpreter-paths.html
[latest-release]: https://github.com/VDOO-Connected-Trust/ghidra-pyi-generator/releases/latest
[pep-0484]: https://www.python.org/dev/peps/pep-0484/
[pycharm-demo]: ./media/pycharm_demo.gif