[![Build Status](https://img.shields.io/travis/GetintheLoop/painless-sqlalchemy/master.svg)](https://travis-ci.org/GetintheLoop/painless-sqlalchemy)
[![Coverage Status](https://coveralls.io/repos/github/GetintheLoop/painless-sqlalchemy/badge.svg?branch=master)](https://coveralls.io/github/GetintheLoop/painless-sqlalchemy?branch=master)
[![Dependencies](https://pyup.io/repos/github/GetintheLoop/painless-sqlalchemy/shield.svg?t=1518818417448)](https://pyup.io)

# Painless-SQLAlchemy

`pip install painless-sqlalchemy`

### What is Painless-SQLAlchemy?

Painless-SQLAlchemy adds simplified serialization and filtering to SQLAlchemy.
     
### Supported Databases

Tests run Postgres 9.6.X. MySQL should work, but is not tested yet.

### Run Tests

Check out [SETUP.md](SETUP.md)

### Where can I get help?

Plese open a github issue.

---------------------

# Overview

Examples use Models described in [conftest.py](tests/conftest.py).

### Filtering

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

Ok, but what about really hard stuff. How about all Students that are taught by
a specific teacher or have a gmail address? Easy!

```python
Student.filter(_or(
    ref('teachers.id') == teacher_id,
    ref('email').ilike("%@gmail.com")
)).all()
```

### Serialization

Serializing Models is easy now. Let's get all teachers and their students:
```python
Teacher.serialize(['name', 'students.name'])
```

returns
```json
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

You can obviously combine serialize with filtering:
```python
Teacher.serialize(
    ['name', 'students.name'],
    {"id": teacher_id}
)
```

# Documentation
