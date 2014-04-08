# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import abc
import os
import shutil
from upload import upload
from .util import pip_install


class Repo(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, attributes):
        super(Repo, self).__init__()
        self._attributes = attributes

    def __getattr__(self, key):
        return self._attributes[key]

    @abc.abstractmethod
    def get_as_pip_conf(self):
        pass

    @abc.abstractmethod
    def download_packages(self, package_spec, directory):
        pass

    @abc.abstractmethod
    def upload_packages(self, package_files):
        pass


PIPCONF_FILEREPO = '''\
[global]
no-index = true
find-links = {directory}
'''


class FileRepo(Repo):

    def get_as_pip_conf(self):
        return PIPCONF_FILEREPO.format(directory=self.directory)

    def download_packages(self, package_spec, directory):
        pip_install(
            '--find-links', self.directory,
            '--no-index',
            '--download', directory.path,
            package_spec,
        )

    def upload_packages(self, package_files):
        destination = self.directory
        for source in package_files:
            shutil.copy2(source, destination)


class PipLocalRepo(FileRepo):

    @property
    def directory(self):
        return os.path.expanduser('~/.pip/local')


PIPCONF_HTTPREPO = '''\
[global]
index-url = {download_url}
extra-index-url =
'''


class HttpRepo(Repo):

    def get_as_pip_conf(self):
        return PIPCONF_HTTPREPO.format(download_url=self.download_url)

    def download_packages(self, package_spec, directory):
        pip_install(
            '--index-url', self.download_url,
            '--download', directory.path,
            package_spec,
        )

    def upload_packages(self, package_files):
        for source in package_files:
            upload(
                source,
                signature=None,
                repository=self.upload_url,
                username=self.username,
                password=self.password,
                comment='Uploaded with Pyrene',
            )


class PyPIRepo(HttpRepo):

    @property
    def download_url(self):
        return 'https://pypi.python.org/simple'

    @property
    def upload_url(self):
        return 'https://pypi.python.org/'
