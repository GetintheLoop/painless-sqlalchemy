import pycodestyle
from tests import list_project_files


class TestPep8(object):
    """ Test that we conform to PEP8. """

    def test_pep8(self):
        pep8style = pycodestyle.StyleGuide(quiet=False)
        result = pep8style.check_files(list_project_files())
        assert result.total_errors == 0, "Found pep8 problems"
