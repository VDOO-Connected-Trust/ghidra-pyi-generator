import site
import shutil
import os.path

os.system("mkdir -p %s" % (site.getsitepackages()[0], ))
shutil.copytree(os.path.join(__file__, "..", "vendor"), site.getsitepackages()[0])