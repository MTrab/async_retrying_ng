"""Setup file for Next Gen. async_retrying module."""
# -*- coding: utf-8 -*-

import sys
import re
from pathlib import Path

from setuptools import setup

if sys.version_info < (3, 10, 0):
    sys.exit("The async_retrying_ng module requires Python 3.10.0 or later")

home = Path(__file__).parent
readme = home / "README.md"


def get_version():
    """Get version from module file."""
    regex = re.compile(r'__version__ = "(?P<version>.+)"', re.M)
    match = regex.search((home / "async_retrying_ng.py").read_text())
    return match.group("version")


setup(
    name="async_retrying_ng",
    version=get_version(),
    author="Malene Trab",
    author_email="malene@trab.dk",
    url="https://github.com/mtrab/async_retrying_ng",
    description="Next Gen. simple retrying for asyncio",
    long_description=readme.read_text(),
    install_requires=[
        "async_timeout",
    ],
    extras_require={
        ':python_version=="3.10"': ["asyncio"],
    },
    py_modules=["async_retrying"],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords=["asyncio", "retrying"],
)