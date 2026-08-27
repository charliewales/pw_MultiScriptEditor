from pathlib import Path
from runpy import run_path
from tempfile import TemporaryDirectory

from setuptools import find_packages, setup


ROOT = Path(__file__).parent
VERSION = run_path(str(ROOT / "multi_script_editor" / "_version.py"))["__version__"]
EGG_INFO_BASE = TemporaryDirectory(prefix="multi_script_editor-")

setup(
    name="multi_script_editor",
    version=VERSION,
    description="Python editor for multiple platforms",
    long_description=(ROOT / "readme.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3",
    ],
    keywords="python ide script_editor",
    url="https://github.com/charliewales/pw_MultiScriptEditor",
    author="Carlos Rico",
    author_email="carlos.rico.3d@gmail.com",
    license="MIT",
    license_files=("license.md",),
    packages=find_packages(exclude=("tests", "tests.*")),
    python_requires=">=3.7",
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "mse=multi_script_editor:show",
        ],
    },
    options={
        "egg_info": {
            "egg_base": EGG_INFO_BASE.name,
        },
    },
    zip_safe=False,
)
