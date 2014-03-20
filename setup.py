#!/usr/bin/env python

from setuptools import setup

VERSION = '0.1.0'
DESC = open('README.rst').read()

setup(
    name = 'structominer',
    packages = ['structominer'],
    version = VERSION,
    description = 'The high-class document scraper',
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
    keywords = ['web', 'document', 'scrape', 'scraping', 'scraper'],

    download_url = 'https://github.com/aGHz/structominer/tarball/{v}'.format(v=VERSION)
)
