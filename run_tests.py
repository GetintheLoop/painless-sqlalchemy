import os
import sys
import pytest


def run_tests():
    args = [
        '--cov=painless_sqlalchemy',
        '--cov=tests',
        '--cov-report=html',
        '--cov-report=term-missing:skip-covered',
        '--cov-config=.coveragerc'
    ]
    if '--verbose' in sys.argv:
        args.append('-s')
    if '--batch' in sys.argv:
        os.environ['BATCH_RUN'] = "1"
    pytest.main(args)


if __name__ == '__main__':
    run_tests()
