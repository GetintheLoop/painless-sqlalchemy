import re
import fnmatch
from os import path, walk

ROOT_DIR = path.dirname(path.abspath(path.join(__file__, "..")))


def list_project_files(exclude=None):
    """ List python project files """
    if exclude is None:
        exclude = ["env"]

    # compile asterisks to regular expressions
    exclude_regex = []
    for excluded in [path.join(ROOT_DIR, excluded) for excluded in exclude]:
        escaped = re.escape(excluded)
        escaped = escaped.replace("\*\*", ".*")
        escaped = escaped.replace("\*", "[^\/]*")
        exclude_regex.append(re.compile(escaped))

    result = []
    for root, subFolders, files in walk(ROOT_DIR):
        for file_ in fnmatch.filter(files, "*.py"):
            abs_path = path.join(root, file_)
            include = True
            for excluded in exclude_regex:
                if excluded.match(abs_path):
                    include = False
                    break
            if include:
                result.append(abs_path)

    return result
