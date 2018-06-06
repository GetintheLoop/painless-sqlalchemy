## Test Requirements
* Python 3.6
* PostgreSQL 9.6
* Ubuntu 16.04

## Setup Using Docker (Recommended)

Install Docker then run

    $ . manage.sh

then inside container you can run the tests.

## Running the tests

Ensure your env is activated and run:

    $ python run_tests.py [options]
      
### Options

`--verbose`: Output debug information (warning: interferes with test progress output)

`--batch`: Run in batch mode. Faster but does not check for tests with side effects. Should be used to check for coverage!


## Setup Using Virtual Env

Documented for historical reasons. The preferred way is to use Docker. 

### Create Virtual Env
Install `virtualenv`

    $ sudo apt-get install python-pip
    $ sudo pip install virtualenv
    $ sudo apt-get install python-dev
    
##### CREATE ENVIRONMENT
    $ virtualenv -p /usr/bin/python3.6 env
    
    # activate the new environment
    $ source env/bin/activate
    
    # install requirements
    $ pip install -r requirements.txt
    
##### DEACTIVATE ENVIRONMENT
To deactivate environment for session, enter:

    $ deactivate

### Install and Setup PostgreSQL
[Instructions](https://github.com/simlu/xmonad/blob/master/programs/postgresql.md)

Important: Tests will (re)create database `painless_tmp`.
