import os
import re
import multiprocessing
from multiprocessing.pool import ThreadPool
import time
from pylint import epylint
from tests import list_project_files, ROOT_DIR


class TestPylint(object):
    """ Test that we conform to Pylint. """

    suppress_for_test_files = [
        "E1101",  # no-member (Model creation)
        "W0221",  # arguments-differ (class setup inheritance)
        "W0212"  # protected-access  (e.g. private methods)
    ]

    def test_pylint(self):
        pool = ThreadPool(multiprocessing.cpu_count())
        processes = [pool.apply_async(
            lambda f: epylint.py_run(
                '%s --rcfile=%s' % (f, os.path.join(ROOT_DIR, ".pylintrc")),
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
                for log in stdout.split("\n"):
                    if re.match(r"^\*{13} Module [a-zA-Z0-9._]+$", log):
                        continue
                    if re.match(r"^\s[-]+$", log):
                        continue
                    if re.match(
                        r"^\sYour code has been rated at \d+\.\d+/10 "
                        r"\(previous run: \d+\.\d+/10, [+\-]\d+\.\d+\)$",
                        log
                    ):
                        continue
                    if re.match(r"^\s*$", log):
                        continue
                    logs.append(log.strip())
            if not re.match(
                r"^Using config file [/A-Za-z0-9\-_]+?\.pylintrc\n$",
                stderr
            ):
                logs.append(stderr)
        pool.close()

        result = []
        if len(logs) > 0:
            for log in logs:
                m = re.match(
                    r"^([/a-zA-Z0-9_.\-]+):(\d+): (error|warning) "
                    r"\(([A-Z]\d{4}), ([a-z\-]+), ",
                    log
                )
                if m:
                    groups = m.groups()
                    prefix = os.path.commonprefix([ROOT_DIR, groups[0]])
                    relpath = os.path.relpath(groups[0], prefix)
                    if (
                        relpath.startswith("tests/") and
                        groups[3] in self.suppress_for_test_files
                    ):
                        continue
                result.append(log)

        if len(result) > 0:
            for log in result:
                print(log)
            print("PyLint Problems: %s" % len(result))
        assert len(result) == 0
