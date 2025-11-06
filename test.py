import seaborn
import os

# Get the file path of the jupyterlab module
try:
    # For packages, __file__ points to the __init__.py file in the package directory
    jupyterlab_path = seaborn.__file__
    # Get the directory containing the module
    jupyterlab_dir = os.path.dirname(jupyterlab_path)
    print(f"The seaborn module is located in: {jupyterlab_dir}")
except AttributeError:
    print("The seaborn module does not have a __file__ attribute (it may be a built-in or namespace package).")