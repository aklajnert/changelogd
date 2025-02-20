#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The setup script."""
from setuptools import find_packages
from setuptools import setup

from changelogd import __version__

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    readme += "\n" + history_file.read()

requirements = [
    "Click>=8.1.7",
    "Jinja2>=3.1.3",
    "toml>=0.10.2",
    "ruamel.yaml>=0.18.6",
]

test_requirements = ["pytest>=5", "pyfakefs==5.4", "pytest-subprocess"]

dev_requirements = [
    "bump2version==1.0.1",
    "wheel==0.43.0",
    "flake8==7.0.0",
    "nox==2024.3.2",
    "mypy==1.9.0",
]

docs_requirements = [
    "setuptools",
    "sphinx",
]

setup(
    author="Andrzej Klajnert",
    author_email="python@aklajnert.pl",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    description="Changelogs without conflicts.",
    entry_points={
        "console_scripts": [
            "changelogd=changelogd.cli:main",
        ],
    },
    install_requires=requirements,
    extras_require={
        "test": test_requirements,
        "dev": dev_requirements,
        "docs": docs_requirements,
    },
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords="changelogd",
    name="changelogd",
    packages=find_packages(include=["changelogd", "changelogd.*"]),
    test_suite="tests",
    url="https://github.com/aklajnert/changelogd",
    version=__version__,
    zip_safe=False,
)
