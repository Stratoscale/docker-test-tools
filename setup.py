# coding: utf-8
from setuptools import setup, find_packages

setup(
    name="docker-test-tools",
    git_version=True,
    description="Docker test tools",
    author_email="",
    url="",
    keywords=["Docker", "Test", "Tools"],
    install_requires=[
        "waiting==1.3.0",
        "docker-compose==1.11.2",
        "requests-unixsocket==0.1.5"
    ],
    packages=find_packages(),
    include_package_data=True,
    long_description="""Utilities for managing tests based on docker-compose"""
)
