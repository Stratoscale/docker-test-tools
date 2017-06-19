# coding: utf-8
import os
import subprocess

from setuptools import setup, find_packages


def get_git_revision():
    """Return the git revision."""
    if os.path.exists('PKG-INFO'):
        with open('PKG-INFO') as package_info:
            for key, value in (line.split(':', 1) for line in package_info):
                if key.startswith('Version'):
                    return value.strip()

    return subprocess.check_output(['git', 'rev-parse', 'HEAD']).strip()

setup(
    name="docker-test-tools",
    version=get_git_revision(),
    description="Docker test tools",
    author_email="",
    url="",
    keywords=["Docker", "Test", "Tools"],
    install_requires=[
        "waiting==1.3.0",
        "docker-compose==1.13.0",
        "requests-unixsocket==0.1.5"
    ],
    packages=find_packages(),
    include_package_data=True,
    long_description="""Utilities for managing tests based on docker-compose"""
)
