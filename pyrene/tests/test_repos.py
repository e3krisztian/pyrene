# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import pyrene.repos as m


class Test_DirectoryRepo(unittest.TestCase):

    def test_attributes(self):
        repo = m.DirectoryRepo({'directory': 'dir@', 'type': 'directory'})
        self.assertEqual('directory', repo.type)
        self.assertEqual('dir@', repo.directory)


class Test_HttpRepo(unittest.TestCase):

    def test_attributes(self):
        repo = m.DirectoryRepo(
            {
                'download_url': 'https://priv.repos.org/simple',
                'type': 'http'
            }
        )
        self.assertEqual('http', repo.type)
        self.assertEqual('https://priv.repos.org/simple', repo.download_url)
