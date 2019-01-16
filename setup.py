#!/usr/bin/env python3
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="batchren",
    version="0.5.2",
    author="Andrew Au",
    author_email="andrew.ch.au@outlook.com",
    description="A command line batch renamer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/matvign/batchrenamer",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
    install_requires=['natsort'],
    python_requires='~=3.5',
    scripts=['bin/batchren']
)
