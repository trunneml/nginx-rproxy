#!/usr/bin/env python3
# pylint: disable=missing-docstring
import os

from setuptools import find_packages, setup


def read(fname):
    """
    Utility function to read the large files like the README file.

    Used for the long_description.  It's nice, because now:
    1) we have a top level README file and
    2) it's easier to type in the README file than to put a raw
    string in below ...
    """
    with open(os.path.join(os.path.dirname(__file__), fname)) as filepointer:
        return filepointer.read()

setup(
    name="nginxrproxy",
    version="0.2.0",
    author="Michael Trunner",
    author_email="michael@trunner.de",
    maintainer="Michael Trunner",
    maintainer_email="michael@trunner.de",
    description=("Let's encrypt wrapper for Nginx"),
    license="AGPL-3.0+",
    url="https://github.com/trunneml/nginx-rproxy",
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    long_description=read('README'),
    classifiers=[
        "Environment :: Web Environment",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Internet :: WWW/HTTP :: Site Management",
        "Topic :: Internet :: Proxy Server"
    ],
    include_package_data=True,
    install_requires=read("requirements.base.txt").splitlines(),
)
