[![Build Status](https://img.shields.io/travis/GetintheLoop/painless-sqlalchemy/master.svg)](https://travis-ci.org/GetintheLoop/painless-sqlalchemy)
[![Coverage Status](https://coveralls.io/repos/github/GetintheLoop/painless-sqlalchemy/badge.svg?branch=master)](https://coveralls.io/github/GetintheLoop/painless-sqlalchemy?branch=master)
[![Dependencies](https://pyup.io/repos/github/GetintheLoop/painless-sqlalchemy/shield.svg?t=1518818417448)](https://pyup.io)

# Painless-SQLAlchemy

Released on [pypi](https://pypi.python.org/pypi/Painless-SQLAlchemy). Install with

`pip install painless-sqlalchemy`

### What is Painless-SQLAlchemy?

Painless-SQLAlchemy adds simplified querying and serialization to SQLAlchemy.
     
### Supported Databases

Tests run Postgres 9.6.X. MySQL should work, but is not tested yet.

### Run Tests

Check out [SETUP.md](SETUP.md)

### Where can I get help?

Plese open a github issue.

---------------------

# Overview

Examples use Models described in [conftest.py](tests/conftest.py).

### Filter

*Looking for all Teachers teaching a specific Student?*
```python
Teacher.filter({'students.id': student_id}).all()
```

*How about all Students frequenting a specific Classroom...*
```python
Student.filter({'teachers.classroom.id': classroom_id}).all()
```

*...who's first name is also Alex or John?*
```python
Student.filter({
    'teachers.classroom.id': classroom_id,
    'first_name': ["Alex", "John"]
}).all()
```

*Ok, but what about all Students taught by
a specific teacher or with a gmail address?*

```python
Student.filter(_or(
    ref('teachers.id') == teacher_id,
    ref('email').ilike("%@gmail.com")
)).all()
```

### Serialize

*Let's get all teachers and their students:*
```python
Teacher.serialize(['name', 'students.name'])
```

*returns*
```
[
  {
    "name": "Nichole Copeland",
    "students": [
      {"name": "Margaret Anderson"},
      {"name": "Laura Smith"},
      ...
    ]
  },
  ...
]
```

*And we can combine that with filtering:*
```python
Teacher.serialize(
    ['name', 'students.name'],
    {"id": teacher_id}
)
```

# Documentation

### Model Definitions

All your Models need to inherit from `Model.py`. Examples are given in [conftest.py](tests/conftest.py)

### Filter

`Model.filter(...)`

Returns SQLAlchemy query that has necessary joins / filters applied.

#### Parameters

`attributes`: dict *or* SQLAlchemy filter using ref

`query`: Optional (pre-filtered) query used as base

`skip_nones`: Skip None-values dict entries iff true

- resolution for and / or clauses (information stored on query)

#### Dictionary Filtering

#### Relationships and Lists
- list filtering on to many vs to one relationship / column
- optimization compared to clause filtering
- None values

#### Clause Filtering

- ref, how to use it and what it does

### Serialize

`Model.serialize(...)`

Returns JSON serializable representation of fetched data.

#### Parameters

`to_return`: list of fields to return

`filter_by`: dict of SQLAlchemy clause to filter by

`limit`: maximum amount of objects fetched

`offset`: offset value for the result

`query`: Optional (pre-filtered) query used as base

`skip_nones`: Skip filter_by entries that have a "None" value

`order_by`: enforce result ordering, multiple via tuple

`session`: Explict session to use for query

`expose_all`: Whether to Return not exposed fields

`params`: Query parameters

#### Column Exposure
- exposure of columns
- only loading what is required (eager loading)

#### MapColumn
- MapColumn

#### Default Serialization
- default serialization
- pro / con for defining all fields / relationships

#### Limit and Offset
- ordering / limit offset (how is this accomplished)

### Internals and Optimization

- optimized to only fetch what is necessary
- optimized to only make necessary joins (when possible to do this automatically)