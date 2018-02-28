import re
import os
import subprocess
from tests import ROOT_DIR


class TestVersionConsistent(object):
    """ Test setup.py version doesn't fall behind git tag. """

    def test_version_consistent(self):
        v1 = subprocess.check_output(
            'git describe --tags --abbrev=0'.split()).strip().decode("utf-8")
        with open(os.path.join(ROOT_DIR, "setup.py")) as f:
            v2 = re.search("version='([0-9.]+)',", f.read()).groups()[0]
        assert list(map(int, v1.split("."))) <= list(map(int, v2.split(".")))
