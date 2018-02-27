import multiprocessing
import re
from multiprocessing.pool import ThreadPool
import time
from pylint import epylint
from tests import list_project_files


class TestPylint(object):
    """ Test that we conform to Pylint. """

    def test_pylint(self):
        pool = ThreadPool(multiprocessing.cpu_count())
        processes = [pool.apply_async(
            lambda f: epylint.py_run(
                '%s' % f,
                return_std=True
            ),
            [file_]
        ) for file_ in list_project_files()]

        while not all(p.ready() for p in processes):
            time.sleep(0.2)

        logs = []
        for process in processes:
            stdout, stderr = map(lambda e: e.getvalue(), process.get())
            if "Your code has been rated at 10.00/10" not in stdout:
                logs.append(stdout)
            if not re.match(
                r"^Using config file [/A-Za-z0-9\-_]+?\.pylintrc\n$",
                stderr
            ):
                logs.append(stderr)
        pool.close()

        if len(logs) > 0:
            for log in logs:
                print(log)
            print("Files with PyLint Problems: %s" % len(logs))
        assert len(logs) == 0
