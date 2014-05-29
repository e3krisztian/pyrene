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
    dot_pyrene = os.path.expanduser('~/.pyrene')
    dot_pypirc = os.path.expanduser('~/.pypirc')

    tempdir = tempfile.mkdtemp(suffix='.pyrene')
    network = Network(dot_pyrene)
    try:
        if not os.path.exists(dot_pyrene):
            network.add_known_repos(dot_pypirc)

        cmd = PyreneCmd(network, Directory(tempdir), dot_pypirc)

        line = ' '.join(sys.argv[1:])

        if line:
            cmd.onecmd(line)
        else:
            cmd.cmdloop()
    finally:
        shutil.rmtree(tempdir)


if __name__ == '__main__':
    main()
