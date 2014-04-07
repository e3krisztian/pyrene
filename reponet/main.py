# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

# TODO: split up this & its test file
# TODO: complete repo names
# FIXME: starting up with invalid config file causes exception
# TODO: prefix ini section names for repos with "repo:"
# TODO: implicit repos for local directories - both as source and destination!
# TODO: support some pip switches (-r requirements.txt, --pre, --no-use-wheel)
# TODO: support copying all package versions
# FIXME: 'use repo', where repo does not have attributes set causes exception

import tempfile
import os
import sys
import shutil
from .repomanager import RepoManager
from .util import Directory
from .shell import RepoNetCmd


def main():
    tempdir = tempfile.mkdtemp(suffix='.pypkgs')
    cmd = RepoNetCmd(
        RepoManager(os.path.expanduser('~/.python.reponet')),
        Directory(tempdir),
    )
    line = ' '.join(sys.argv[1:])
    try:
        if line:
            cmd.onecmd(line)
        else:
            cmd.cmdloop()
    finally:
        shutil.rmtree(tempdir)


if __name__ == '__main__':
    main()
