# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import tempfile
import os
import sys
import shutil
from .network import Network
from .util import Directory
from .shell import PyreneCmd


def add_known_repos(cmd):
    cmd.do_import_pypirc('')
    repo_names = cmd.network.repo_names
    if 'pypi' not in repo_names:
        cmd.do_http_repo('pypi')
        cmd.do_setup_for_pypi_python_org('')
    if 'local' not in repo_names:
        cmd.do_directory_repo('local')
        cmd.do_setup_for_pip_local('')


def main():
    dot_pyrene = os.path.expanduser('~/.pyrene')
    dot_pypirc = os.path.expanduser('~/.pypirc')

    tempdir = tempfile.mkdtemp(suffix='.pyrene')
    try:
        cmd = PyreneCmd(
            Network(dot_pyrene),
            Directory(tempdir),
            dot_pypirc,
        )

        if not os.path.exists(dot_pyrene):
            add_known_repos(cmd)

        line = ' '.join(sys.argv[1:])

        if line:
            cmd.onecmd(line)
        else:
            cmd.cmdloop()
    finally:
        shutil.rmtree(tempdir)


if __name__ == '__main__':
    main()
