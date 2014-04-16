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


def main():
    tempdir = tempfile.mkdtemp(suffix='.pyrene')
    cmd = PyreneCmd(
        Network(os.path.expanduser('~/.pyrene')),
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
