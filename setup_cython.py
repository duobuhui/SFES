from distutils.core import setup
from Cython.Build import cythonize

import platform

if platform.system() == "Windows":
    name = "SFES-Windows"
elif platform.system() == "Linux":
    name = "SFES-Linux"
elif platform.system() == "Darwin":
    print(platform.machine())
    if "arm" in platform.machine():
        name = "SFES-macOS-Apple_Silicon"
    elif "64" in platform.machine():
        name = "SFES-macOS-Intel"
    else:
        name = "SFES-macOS"
else:
    name = "SFES"

setup(
    name=name,
    ext_modules=cythonize(
        [
            "api.py",
            "main.py",
            "utility.py",
            "i18n.py",
            "login.py",
            "geetest.py",
            "globals.py",
            "utils.py",
        ]
    ),
)
