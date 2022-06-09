Start docker

> . manage.sh

Run tests

> python run_tests.py

Install twine

> pip install twine

Compile with

> python setup.py sdist

Publish with

> python /user/.local/lib/python3.9/site-packages/twine/__main__.py upload dist/*