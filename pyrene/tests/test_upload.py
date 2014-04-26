from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals

import unittest
import pyrene.upload as m


class Test_get_whl_py_version(unittest.TestCase):

    def test_pip(self):
        self.assertEquals(
            'py2.py3',
            m.get_whl_py_version('pip-1.5.4-py2.py3-none-any.whl')
        )
