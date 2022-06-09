#!/usr/bin/env python
"""
Painless-SQLAlchemy
----------------
Easy serialization and filtering for SQLAlchemy.

Links:
* [github](https://github.com/GetintheLoop/painless-sqlalchemy)
"""
import os
from setuptools import setup

setup(
    name='Painless-SQLAlchemy',
    version='1.0.3',
    url='https://github.com/GetintheLoop/painless-sqlalchemy',
    license='MIT',
    author='Lukas Siemon',
    author_email='painless@blackflux.com',
    maintainer='Lukas Siemon',
    maintainer_email='painless@blackflux.com',
    description='Simplified filtering and serialization for SQLAlchemy',
    long_description=__doc__,
    long_description_content_type="text/markdown",
    packages=[x[0] for x in os.walk("painless_sqlalchemy")],
    zip_safe=False,
    platforms='any',
    install_requires=[
        'SQLAlchemy>=1.2.0',
        'psycopg2-binary>=2.7'
    ],
    extras_require={
        'postgis': ["GeoAlchemy2>=0.4.2"]
    },
    keywords=['SQLAlchemy', 'Serialization', 'Query', 'Simple', 'Abstraction', 'PostGis', 'Columns'],
    classifiers=[]
)
