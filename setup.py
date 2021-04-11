#!/usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name = 'stdview',
    version = '0.0.1',
    packages = find_packages(),
    include_package_data = True,
    zip_safe = False,
    install_requires = [
        'flask',
        'python-magic',
        'Pygments',
    ],
    entry_points={
        'console_scripts': [
            'stdview = stdview.cli:main',
        ]
    }
)
