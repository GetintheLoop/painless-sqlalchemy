## Test Requirements
* Docker

## Start Docker Container

    $ . manage.sh

## Running the tests

    $ python run_tests.py [options]
      
### Options

`--verbose`: Output debug information (warning: interferes with test progress output)

`--batch`: Run in batch mode. Faster but does not check for tests with side effects. Should be used to check for coverage!
