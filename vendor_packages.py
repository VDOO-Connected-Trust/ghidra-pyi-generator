import site
import shutil
import os.path

os.system("mkdir -p %s" % (os.path.dirname(site.getsitepackages()[0]), ))
shutil.copytree(os.path.join(os.path.dirname(__file__), "vendor"), site.getsitepackages()[0])