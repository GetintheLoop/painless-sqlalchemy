[![Build Status](https://img.shields.io/travis/GetintheLoop/painless-sqlalchemy/master.svg)](https://travis-ci.org/GetintheLoop/painless-sqlalchemy)
[![Coverage Status](https://coveralls.io/repos/github/GetintheLoop/painless-sqlalchemy/badge.svg?branch=master)](https://coveralls.io/github/GetintheLoop/painless-sqlalchemy?branch=master)
[![Dependencies](https://pyup.io/repos/github/GetintheLoop/painless-sqlalchemy/shield.svg?t=1518818417448)](https://pyup.io)

# Painless-SQLAlchemy

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

### Filter

- parameters
- resolution for and / or clauses (information stored on query)

#### Dictionary Filtering

- list filtering on to many vs to one relationship / column
- None values

#### Clause Filtering

- ref

### Serialize

- parameters
- exposure of columns
- only loading what is required (eager loading)
- MapColumn
- default serialization
- ordering / limit offset (how is this accomplished)
