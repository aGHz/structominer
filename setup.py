#!/usr/bin/env python

from setuptools import setup

VERSION = '0.2.0'
DESC = open('README.rst').read()
DESC = "\n".join(DESC.split("\n")[5:])  # Remove the header and tag line

setup(
    name = 'structominer',
    packages = ['structominer'],
    version = VERSION,
    description = 'Data scraping for a more civilized age',
    long_description = DESC,
    author = 'Adrian Ghizaru',
    author_email = 'adrian.ghizaru@gmail.com',
    url = 'https://github.com/aGHz/structominer',
    license = 'MIT',

    install_requires = [
        'lxml',
    ],

    zip_safe = False,
    include_package_data = True,
    package_data = {'': ['LICENSE', 'README.rst']},

    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Internet',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Text Processing :: Filters',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Text Processing :: Markup :: XML',
    ],
    keywords = ['data', 'scraping', 'web', 'scraper'],

    download_url = 'https://github.com/aGHz/structominer/archive/{v}.tar.gz'.format(v=VERSION)
)
