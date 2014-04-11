# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import abc
import shutil
from upload import upload
from .util import pip_install


KEY_TYPE = 'type'

KEY_DIRECTORY = 'directory'
KEY_SERVE_INTERFACE = 'interface'
KEY_SERVE_PORT = 'port'
KEY_SERVE_USERNAME = 'username'
KEY_SERVE_PASSWORD = 'password'

KEY_USERNAME = 'username'
KEY_PASSWORD = 'password'
KEY_DOWNLOAD_URL = 'download_url'
KEY_UPLOAD_URL = 'upload_url'


class Repo(object):
    __metaclass__ = abc.ABCMeta

    ATTRIBUTES = {KEY_TYPE}

    def __init__(self, attributes):
        super(Repo, self).__init__()
        self._attributes = attributes

    def __getattr__(self, key):
        try:
            return self._attributes[key]
        except KeyError:
            raise AttributeError(key)

    @abc.abstractmethod
    def get_as_pip_conf(self):
        pass

    @abc.abstractmethod
    def download_packages(self, package_spec, directory):
        pass

    @abc.abstractmethod
    def upload_packages(self, package_files):
        pass

    @abc.abstractmethod
    def serve(self):
        pass


PIPCONF_DIRECTORYREPO = '''\
[global]
no-index = true
find-links = {directory}
'''


class DirectoryRepo(Repo):

    ATTRIBUTES = {
        KEY_TYPE,
        KEY_DIRECTORY,
        KEY_SERVE_INTERFACE,
        KEY_SERVE_PORT,
        KEY_SERVE_USERNAME,
        KEY_SERVE_PASSWORD,
    }

    def get_as_pip_conf(self):
        return PIPCONF_DIRECTORYREPO.format(directory=self.directory)

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

    def serve(self):
        # TODO
        pass


PIPCONF_HTTPREPO = '''\
[global]
index-url = {download_url}
extra-index-url =
'''


class HttpRepo(Repo):

    ATTRIBUTES = {
        KEY_TYPE,
        KEY_UPLOAD_URL,
        KEY_DOWNLOAD_URL,
        KEY_USERNAME,
        KEY_PASSWORD,
    }

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

    def serve(self):
        print(
            'Externally served at url {}'
            .format(getattr(self, KEY_DOWNLOAD_URL, 'UNSPECIFIED???'))
        )
