#!/usr/bin/env python
"""
Painless-SQLAlchemy
----------------
Easy serialization and filtering for SQLAlchemy.
Links
`````
* `github <https://github.com/GetintheLoop/painless-sqlalchemy>`_
"""
from setuptools import setup

setup(
    name='Painless-SQLAlchemy',
    version='0.6.0',
    url='https://github.com/GetintheLoop/painless-sqlalchemy',
    license='MIT',
    author='Lukas Siemon',
    author_email='painless@blackflux.com',
    maintainer='Lukas Siemon',
    maintainer_email='painless@blackflux.com',
    description='Simplified filtering and serialization for SQLAlchemy',
    long_description=__doc__,
    packages=[
        'painless_sqlalchemy',
        'painless_sqlalchemy.core',
        'painless_sqlalchemy.elements',
        'painless_sqlalchemy.util',
        'painless_sqlalchemy.util.testing',
    ],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'SQLAlchemy>=1.2.0',
        'psycopg2-binary>=2.7'
    ],
    keywords=['SQLAlchemy', 'Serialization', 'Query', 'Simple', 'Abstraction'],
    classifiers=[]
)
