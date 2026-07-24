from setuptools import find_packages, setup

setup(
    name="multi_script_editor",
    version="6.3.0",
    description="Python editor for multiple platforms",
    long_description="Python editor for multiple platforms and CG software applications",
    classifiers=[
        "Development Status :: Release 6.3.0",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3+",
    ],
    keywords="python ide script_editor",
    url="https://github.com/charliewales/pw_MultiScriptEditor",
    author="Carlos Rico",
    author_email="carlos.rico.3d@gmail.com",
    license="MIT",
    packages=find_packages(),
    install_requires=[],
    include_package_data=True,
    zip_safe=False,
)
