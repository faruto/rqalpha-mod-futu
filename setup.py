#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Futu, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from os.path import dirname, join
from pip.req import parse_requirements

from setuptools import (
    find_packages,
    setup,
)

with open(join(dirname(__file__), 'rqalpha_mod_futu/VERSION.txt'), 'rb') as f:
    version = f.read().decode('ascii').strip()

setup(
    name='rqalpha-mod-futu',
    version=version,
    description='A mod for RQAlpha to connect with futuquant to implement US/HK stock quant trading',
    keywords='RQAlpha Back-testing futuquant Futu HK/US Stock Quant Trading API Mod',
    author='Futu, Inc.',
    author_email='ftdev@futunn.com',
    url='https://github.com/FutunnOpen/rqalpha-mod-futu',
    license='Apache License 2.0',
    packages=find_packages(exclude=[]),
    package_data={'': ['*.*']},
    zip_safe=False,
    install_requires=[str(ir.req) for ir in parse_requirements("requirements.txt", session=False)],
    classifiers=[
        'Programming Language :: Python',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Unix',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
