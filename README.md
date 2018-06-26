[![Build Status](https://img.shields.io/travis/GetintheLoop/painless-sqlalchemy/master.svg)](https://travis-ci.org/GetintheLoop/painless-sqlalchemy)
[![Coverage Status](https://coveralls.io/repos/github/GetintheLoop/painless-sqlalchemy/badge.svg?branch=master)](https://coveralls.io/github/GetintheLoop/painless-sqlalchemy?branch=master)
[![Dependencies](https://pyup.io/repos/github/GetintheLoop/painless-sqlalchemy/shield.svg?t=1518818417448)](https://pyup.io)

# Painless-SQLAlchemy

Released on [pypi](https://pypi.python.org/pypi/Painless-SQLAlchemy). Install with

`pip install painless-sqlalchemy`

### What is Painless-SQLAlchemy?

Painless-SQLAlchemy adds simplified querying and serialization to SQLAlchemy.
     
### Supported Databases

Tests run Postgres 9.6.X. 

Project could be adapted to work with MySQL.

### Run Tests

Check out [SETUP.md](SETUP.md)

### Where can I get help?

Plese open a github issue.

---------------------

# Overview

Examples use Models described in [conftest.py](tests/conftest.py).

## Filter()

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

## Serialize()

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

# Much More

Various other improvements and abstractions over SQLAlchemy are provided. 
E.g. CIText and PostGIS custom column types are provided for convenience. 

---------------------

# Documentation

## Model Definitions

All your Models need to inherit from `Model.py`. Examples are given in [conftest.py](tests/conftest.py)

## Dot Notation

#### Simple

Dot notation is a simple and intuitive way to define relationship paths by
joining relationship names using dots. E.g. the teacher names of a student
can be referenced as `teachers.name`.

#### Extended

Multiple fields can be referenced by using brackets. E.g. the name and id of 
a students teachers can be referenced as `teachers(id,name)`.

To reference the default serialization of a Model a `*` can be used. 
E.g. teacher default serialization can be references from student as as `teachers.*`.

## Filter()

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

Filtering by lists is optimized, hence list entries must be unique.

#### Clause Filtering

Instead of a dictionary, an SQLAlchemy clause can be passed as `attribtues`.
Referenced column using the `ref` constructor will be automatically joined 
to the query.

##### Optimization

The clause is analysed and only joins that are necessary are being made.
In most cases we can prevent redundant joints. Optimization information is stored on the query. 

## Serialize()

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
When using serialize only necessary column are loaded. This feature makes 
`serialize()` much more efficient than manually loading and serializing models.

## Advanced Columns

We can define custom mapping for data the does not directly correspond to a 
database column entry.

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

#### column_property
To serialize entries that don't come straight from database columns, we
can use column_properties. These are fully supported for `filter()` and `serialize()`.
However notice that filtering by computed fields can be very expensive.

## Custom Column Types

#### CIText

Column type for [CIText](https://www.postgresql.org/docs/current/static/citext.html). Requires database extension `citext` to be created.

```python
email = Column(CIText(64, True))
```

Constructor takes two parameters, the maximum length of the citext and
a boolean flag `enforce_lower`. 

If the boolean flag is set to true, all input is forced to lower case in application layer (data already in the database is not changed). If the flag is set to false, the field behaves like an ordinary CIText and saves case as provided.

#### HexColor

Column type for Hex Color of format "#RRGGBB".

```python
color = Column(HexColorType)
```

Will raise ValueError if invalid input is provided. Data consistency is not enforced in the database layer.

Uses Integer database representation to store provided value.

#### Time

Column type for 24-hour time of format "HH:MM". Valid range is "00:00" to "23:59".

```python
opening = Column(TimeType)
```

Will raise ValueError if invalid input is provided. Data consistency is enforced, 
however database granularity finer than minute is not considered when loading.

Uses [Time without timezone](https://www.postgresql.org/docs/9.1/static/datatype-datetime.html) database representation to store provided value.

#### Time Zone

Column type for time zone. Valid values are all values found [here](http://en.wikipedia.org/wiki/List_of_tz_database_time_zones) that are also valid postgres timezones.

```python
timezone = Column(TimeZoneType)
```

Will raise ValueError if invalid input is provided. Data consistency is not enforced.
Unknown timezone will be loaded as "None".

Uses [TEXT](https://www.postgresql.org/docs/9.1/static/datatype-character.html) to store time zone in database.

#### PostGIS Types

Require database extension `postgis` and package [GeoAlchemy2](https://github.com/geoalchemy/geoalchemy2). Floats are rounded to 9 digits in application layer logic to prevent rounding error induced bugs.

Assumes coordinates to be on earth. Consistency is partially enforced through the database. However [SRID](https://postgis.net/docs/ST_SetSRID.html) are expected to be correct.

Utility Functions:
- `haversine(lat1, lon1, lat2, lon2)` computes the distance on earth between gps coordinates `[lat1, lon1]` and `[lat2, lon2]`
- `point_inside_polygon(x, y, poly)` returns true iff point defined by `x,y` is inside non-overlapping polygon `poly`

##### Location

Gps coordinate as tuple `(latitude, longitude)`. 

```python
location = Column(LocationType)
```

Stored as [Point](https://postgis.net/docs/ST_Point.html) geometry in the database.

Raises error in application layer logic if input is invalid.

##### Area

Gps area as list `[(lat1, lon1), (lat2, lon2), ..., (latX, lonX), (lat1, lon1)]`

```python
location = Column(AreaType(True))
```

Stores as [Polygon](https://postgis.net/docs/ST_Polygon.html) geometry in the database.

Takes boolean `clockwise` argument. If set to `True` this will enforced polygons to be clock-wise in application layer logic. If set to `False` it will enforce counter clockwise and if set to `None` polygons are stored as given.

Raises error in application layer logic if input is invalid. Open Polygons, Polygons with identical, consecutive points and Polygons with too few unique points are considered invalid.

## Advanced Functions

## Expand()

`Model.expand(...)`

Expand string representation of fields. E.g.
```python
Student.expand('teachers.classroom(id,school_id),id')
```
would return `['teachers.classroom.id', 'teachers.classroom.school_id', 'id']`.

A path ending in `*` gets expanded to the default serialization.

## Has()

`Model.has(...)`

Check if a specific field exists for a model. E.g.
```python
Student.has('teachers.classroom.id')
```
would return `True`. Does not allow input that still needs to be expanded.

---------------------

# Utility Functionality

## Many to Many Relationships

A function to conveniently generate many to many relationship tables is exposed in `TableUtil.many_to_many`.

## Testing Data Models

Generic functionality to write database tests is exposed through `util.testing.*`. For an example
please consider the tests written for this project.

---------------------

# Internals and Optimization

## Load as Required

When using serialize only necessary fields are queried. There are multiple steps here used to accomplish this. First determine required columns:

- Expand columns, make them unique, filter not exposed, handle MapColumns
- Gather columns required for relationship joins 

Then apply filtering separately:

- load only required relationships
- load only required columns
- load only required column_property

Note that primary columns are automatically loaded by SQLAlchemy.

## Join as Required

When using `filter()` only necessary joins are made. So if we are filtering 
by `school.id` and `school.name`, we only need to join `school` once.

While the above case is trivial, this gets very interesting when nested
boolean clauses are used. We can not simply remove all redundancy.

For example when a `to-many` relationship is used in an `and` cause, we can't
re-use the relationship since all conditions would then have to be met
on the same target, which is not desirable in most cases.

## Limit and Offset

Limit and offset functionality is not trivial since many rows are returned from 
SQLAlchemy and it is not clear where one model ends and one model begins.

Currently window function and nested querying are used. Depending on
database version this can be inefficient for large tables.