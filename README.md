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
Student.filter(or_(
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

### Dot Notation

#### Simple

Dot notation is a simple and intuitive way to define relationship paths by
joining relationship names using dots. E.g. the teacher names of a student
can be referenced as `teachers.name`.

#### Extended

Multiple fields can be referenced by using brackets. E.g. the name and id of 
a students teachers can be referenced as `teachers(id,name)`.

To reference the default serialization of a Model a `*` can be used. E.g. teacher default serialization can be references from student as as `teachers.*`.

### Filter

`Model.filter(...)`

Returns SQLAlchemy query with necessary joins and passed filtering applied.

*Info*: Chainable using `query` parameter. However to reduce amount 
of automatic joins, using a single filter call is preferred.

#### Parameters

`attributes`: dict *or* SQLAlchemy filter using `ref` (optional)

`query`: SQLAlchemy query used as base, can be pre-filtered (optional)

`skip_nones`: Skip None-values when using dict (optional, default `false`)

#### Dictionary Filtering

This method is preferred to clause filtering when possible, since it's easier
to read and better optimized in certain cases compared to clause filtering.

The dictionary contains simple key-value lookups. Keys are expected in simple dot notation.
The values can be lists or simple values. 

##### None Values
None values are filtered from the `attributes` dictionary if `skip_nones` is used. 
Convenient when None values should be ignored. Parameter can not be used for
clause filtering.

##### Relationships and Lists

Filter values can be lists when `attribtues` is a dictionary. 
In this case the behaviour depends on the type of relationship / column that is filtered:
- For a `to-many` relationship every value in the list has to be matched
by at least one relationship target (`and`).
- For a `to-one` relationship or simple column only one element from the 
list has to be matched (`or`). 

When using list values, their entries are expected to be unique (due to
optimization).

#### Clause Filtering

Instead of a dictionary, an SQLAlchemy clause can be passed as `attribtues`.
Referenced column using the `ref` constructor will be automatically joined 
to the query.

##### Optimization

The clause is analysed and only joins that are necessary are being made.
For example, in most cases we can prevent redundant joints, however for a
to-many relationship and an `and` clause a separate join is required. 
Optimization information is stored on the query.

### Serialize

`Model.serialize(...)`

Returns JSON serializable representation of fetched data.

#### Parameters

`to_return`: list of fields to return, allows extended dot notation (optional)

`filter_by`: see identical parameter on `filter()` (optional)

`limit`: maximum amount of objects fetched (optional)

`offset`: offset value for objects fetched (optional)

`query`: see identical parameter on `filter()` (optional)

`skip_nones`: see identical parameter on `filter()` (optional)

`order_by`: result ordering, multiple via tuple, defaults to id ordering (optional)

`session`: Explict session to use for query (optional)

`expose_all`: Whether to Return not exposed fields (optional)

`params`: Query parameters (optional)

#### Default Serialization
When no `to_return` is passed, the default serialization for the model is used.
Can be customized per Model by overwriting `default_serialization` (defaults to `id`).

Default serialization can also be referenced using the `*` or appending it as
an entry to the dot notation.

Using explicit serialization opposed to the default serialization should
be preferred. Also be careful when defining default serialization containing `to-many` relationships or referencing
default serialization from other default serialization as the resulting queries
can quickly get very expensive.
 
However when testing and writing proof of concept the default serialization is very helpful.

#### Column Exposure
Not exposed columns are not returned from `serialize()` unless `expose_all` is
used. This is to reduce the risk of leaking secret information. For example
when storing a password hash it should be set to not exposed.

By default primary keys are not exposed and all other fields are exposed.
However exposure can be explicitly set by passing `info={"exposed": True/False}`
into the `Column` constructor.

#### Eager Loading
When using serialize only necessary column are loaded. This includes all
columns that are required to generate the result as well as all
columns required to resolve joins. This feature makes `serialize()` much more
efficient than manually loading and serializing models.

#### MapColumn
Custom serializations can be easily created using `MapColumn`. 
If we want to create a `contact_info` serialization on a student we can write:
```python
contact_info = MapColumn({
    'phone': 'phone',
    'home_phone': 'home_phone',
    'email': 'email'
})
```
Note that `to-one` relationships can also be referenced, but `to-many` relationships are [not supported](https://github.com/GetintheLoop/painless-sqlalchemy/issues/38). Filtering by `MapColumn` is also [not possible](https://github.com/GetintheLoop/painless-sqlalchemy/issues/37).

#### Limit and Offset
Limit and offset functionality is provided for `serialize()`.

This is not trivial functionality since many rows are returned from 
SQLAlchemy and it is not clear where one model ends and one model begins.
Currently window function and nested querying are used. Depending on
database version this can be inefficient for large tables.

### column_property
To serialize entries that don't come straight from database columns, we
can use column_properties. These are fully supported for `filter()` and `serialize()`.
However notice that filtering by computed fields can be very expensive.

### Internals and Optimization

#### Fetch as Required

When using serialize only necessary fields are queried. There are multiple steps here used to accomplish this. First determine required columns:
1) Expand columns, make them unique, filter not exposed, handle MapColumns
2) Add column required for relationship joins 

Then apply filtering separately:

- load only required relationships
- load only required columns
- load only required column_property

Note that primary columns are automatically loaded by SQLAlchemy.

#### Join as Required

When using `filter()` only necessary joins are made. So if we are filtering 
by `teacher.id` and `teacher.name` we only need to join `teacher` once.

While the above case is trivial, this gets very interesting when nested
boolean clauses are used. We can not simply remove all redundancy.

For example when a `to-many` relationship is used in an `and` cause, we can't
re-use the relationship since all conditions would then have to be met
on the same target, which is not desirable in most cases.
