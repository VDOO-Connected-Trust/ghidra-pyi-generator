# Ghidra `.pyi` Generator

The Ghidra `.pyi` Generator generates `.pyi` [type stubs][pep-0484]
for the entire Ghidra API.
Those stub files can later be used in PyCharm to enhance the development experience.

You can either use the stubs released [here][latest-release], or follow the instructions below to generate them yourself.


## Using The Stubs

### Installation 

The release contains  [PEP 561 stub package][pep-561-stub], which can simply be installed with `pip install ghidra-stubs*.whl`
into the environment in which the real `ghidra` module is available. Any conformant tool will then use the stub package
for type analysis purposes.  

If you want to manually add the stub files to PyCharm, follow the instructions in [Install, uninstall, and upgrade interpreter paths][interpreter-paths].

### Usage

Once installed, all you need to do is import the Ghidra modules as usual, and PyCharm will do the rest.

```python
import ghidra
```

To get support for the Ghidra builtins, you need to import them as well. The type hints for those exist in
the generated `ghidra_builtins.pyi` stub. Since it is not a real Python module, importing it at runtime will fail.
But the `.pyi` gives PyCharm all the information it needs to help you.

```python
try:
    from ghidra.ghidra_builtins import *
except:
    pass
```

If you are using [ghidra_bridge](https://github.com/justfoxing/ghidra_bridge) from a Python 3 environment where no real `ghidra` module
exists you can use a snippet like the following:

```python
import typing
if typing.TYPE_CHECKING:
    import ghidra
    from ghidra.ghidra_builtins import *
else:
    b = ghidra_bridge.GhidraBridge(namespace=globals())

# actual code follows here
```

`typing.TYPE_CHECKING` is a special value that is always `False` at runtime but `True` during any kind of type checking or completion.

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
They are now vendored under the `vendor` directory as Python2.7 support is gradually
being dropped from the ecosystem, making it hard to install and fetch packages.

```bash
 
# Create Jython's site-pacakges directory.
jython_site_packages=~/.local/lib/jython2.7/site-packages
mkdir -p $jython_site_packages
 
# Create a PTH file to point Jython to our vendored site-packages

# Outside a virtualenv, use
echo "$(realpath ./vendor)" > $jython_site_packages/python.pth

```

## Creating the `.pyi` files


### GUI
1. Add this directory to the `Script Directories` in the Ghidra Script Manager
2. Refresh the script list
3. Run `generate_ghidra_pyi.py` (will be located under `IDE Helpers`)
4. When a directory-selection dialog appears, choose the directory you'd like to save the `.pyi` files in.

### CLI

```bash
$GHIDRA_ROOT/support/analyzeHeadless /tmp tmp -scriptPath $(pwd) -preScript generate_ghidra_pyi.py ./
```


## Python Package

`generate_ghidra_pyi.py` generates a `setup.py` inside the directory that was selected.

This allows using `pip install` to install a  [PEP 561 stub package][pep-561-stub] that is recognized by PyCharm and other tools as containing type information for the ghidra module.



[interpreter-paths]: https://www.jetbrains.com/help/pycharm/installing-uninstalling-and-reloading-interpreter-paths.html
[latest-release]: https://github.com/VDOO-Connected-Trust/ghidra-pyi-generator/releases/latest
[pep-0484]: https://www.python.org/dev/peps/pep-0484/
[pycharm-demo]: ./media/pycharm_demo.gif
[pep-561-stub]: https://www.python.org/dev/peps/pep-0561/#stub-only-packages
