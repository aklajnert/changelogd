#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""The setup script."""
from setuptools import find_packages
from setuptools import setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

requirements = [
    "Click>=7.0",
    "Jinja2>=2.10",
    "toml>=0.9.4",
    "ruamel.yaml>=0.16.0",
]

test_requirements = ["pytest>=5", "pyfakefs==3.7", "pytest-subprocess"]

dev_requirements = [
    "bump2version==0.5.11",
    "wheel==0.33.6",
    "flake8==3.7.9",
    "tox==3.14.1",
    "mypy==0.740",
]

setup(
    author="Andrzej Klajnert",
    author_email="python@aklajnert.pl",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Changelogs without conflicts.",
    entry_points={"console_scripts": ["changelogd=changelogd.cli:main",],},
    install_requires=requirements,
    extras_require={"test": test_requirements, "dev": dev_requirements},
    license="MIT license",
    long_description=readme,
    include_package_data=True,
    keywords="changelogd",
    name="changelogd",
    packages=find_packages(include=["changelogd", "changelogd.*"]),
    test_suite="tests",
    url="https://github.com/aklajnert/changelogd",
    version="0.1.0",
    zip_safe=False,
)
