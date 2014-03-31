# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os
from temp_dir import within_temp_dir
import tempfile
import shutil
import sys

import unittest
import mock
import paix as m


def rmtree(dir):
    if dir:
        try:
            shutil.rmtree(dir)
        except:
            sys.stderr.write('could not remove {}'.format(dir))


def write_file(path, content):
    with open(path, 'wb') as file:
        file.write(content)


def read_file(path):
    with open(path, 'rb') as file:
        return file.read()


class Test_Executor_copy(unittest.TestCase):

    def setUp(self):
        self.executor = m.Executor()

    @within_temp_dir
    def test_copy(self):
        with open('source', 'wb') as f:
            f.write(b'@!')

        self.executor.copy('source', 'destfile')

        with open('destfile', 'rb') as f:
            self.assertEqual(b'@!', f.read())

    @within_temp_dir
    def test_copy_creates_missing_directories(self):
        with open('source', 'wb') as f:
            f.write(b'@!')

        self.executor.copy('source', 'destdir/destfile')

        self.assertTrue(os.path.isdir('destdir'))
        with open('destdir/destfile', 'rb') as f:
            self.assertEqual(b'@!', f.read())

    def test_copy_expands_tilde(self):
        home = os.path.expanduser('~')
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(dir=home)
            temp_dir_with_tilde = os.path.join('~', os.path.basename(temp_dir))
            source = os.path.join(temp_dir_with_tilde, 'source')
            destination = os.path.join(temp_dir_with_tilde, 'destination')

            write_file(os.path.join(temp_dir, 'source'), b'~!')

            self.executor.copy(source, destination)

            self.assertEqual(b'~!', read_file(os.path.expanduser(destination)))
        finally:
            rmtree(temp_dir)


class Test_Paix(unittest.TestCase):

    def setUp(self):
        self.executor = mock.Mock()
        self.paix = m.Paix(executor=self.executor)

    def test_use(self):
        self.paix.onecmd('use somerepo')

        self.assertEqual(
            [
                mock.call.copy(
                    '~/.paix/repos/somerepo/pip.conf',
                    '~/.pip/pip.conf'
                )
            ],
            self.executor.mock_calls
        )

    @unittest.skip("not the way")
    def test_copy_single_package(self):
        self.paix.onecmd('copy roman==2.0.0 private:')

        self.assertEqual(
            [
                mock.call.execute('pip install -d . roman==2.0.0'.split()),
                mock.call.list_files(),
                mock.call.execute('twine upload roman-2.0.0.zip')
            ],
            self.executor.mock_calls
        )

    @unittest.skip('ONLY PLANNED, NO MEAT YET')
    def test_copy_to_local(self):
        pass

    @unittest.skip('ONLY PLANNED, NO MEAT YET')
    def test_copy_from_local(self):
        pass
