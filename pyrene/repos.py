# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import abc
import shutil
from .upload import upload
from .util import pip_install, PyPI, red, green
from .constants import REPO


class Repo(object):
    __metaclass__ = abc.ABCMeta

    ATTRIBUTES = (REPO.TYPE,)
    attributes = dict

    def __init__(self, name, attributes):
        super(Repo, self).__init__()
        self.name = name
        self.attributes = dict(attributes)

    def __getattr__(self, key):
        try:
            return self.attributes[key]
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

    def print_attributes(self):
        for attribute in self.ATTRIBUTES:
            if attribute in self.attributes:
                msg = green(
                    '   {}: {}'
                    .format(attribute, self.attributes[attribute])
                )
            else:
                msg = ' - {}'.format(attribute)

            print(msg)

        junk = sorted(set(self.attributes.keys()) - set(self.ATTRIBUTES))
        if junk:
            print()
            print('Junk attributes:')
            for attribute in junk:
                msg = red(
                    ' ? {}: {}'.format(attribute, self.attributes[attribute])
                )

                print(msg)


PIPCONF_NULLREPO = '''\
[global]
# no package can be installed from a BadRepo
no-index = true
'''


class BadRepo(Repo):

    ATTRIBUTES = {}

    def get_as_pip_conf(self):
        return PIPCONF_NULLREPO

    @property
    def printable_name(self):
        return red('{} (a misconfigured repo!)'.format(self.name))

    def download_packages(self, package_spec, directory):
        print(
            '{}: pretended to provide package "{}"'
            .format(self.printable_name, package_spec)
        )

    def upload_packages(self, package_files):
        if package_files:
            print(
                '{}: pretended to upload package files'
                .format(self.printable_name)
            )
            for file in package_files:
                print('  {}'.format(file))
        else:
            print('{}: nothing to upload'.format(self.printable_name))

    def serve(self):
        print('{}: is not served'.format(self.printable_name))


PIPCONF_DIRECTORYREPO = '''\
[global]
no-index = true
find-links = {directory}
'''


class DirectoryRepo(Repo):

    ATTRIBUTES = (
        REPO.TYPE,
        REPO.DIRECTORY,
        REPO.VOLATILE,
        REPO.SERVE_INTERFACE,
        REPO.SERVE_PORT,
        REPO.SERVE_USERNAME,
        REPO.SERVE_PASSWORD,
    )

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

    def serve(self, pypi_server=PyPI):
        server = pypi_server()
        server.directory = self.directory
        server.interface = getattr(self, REPO.SERVE_INTERFACE, '0.0.0.0')
        server.port = getattr(self, REPO.SERVE_PORT, '8080')
        true = {'y', 'yes', 't', 'true'}
        server.volatile = getattr(self, REPO.VOLATILE, 'no').lower() in true

        try:
            username = getattr(self, REPO.SERVE_USERNAME)
            password = getattr(self, REPO.SERVE_PASSWORD)
        except AttributeError:
            pass
        else:
            server.add_user(username, password)

        server.serve()


PIPCONF_HTTPREPO = '''\
[global]
index-url = {download_url}
extra-index-url =
'''


class HttpRepo(Repo):

    ATTRIBUTES = (
        REPO.TYPE,
        REPO.UPLOAD_URL,
        REPO.DOWNLOAD_URL,
        REPO.USERNAME,
        REPO.PASSWORD,
    )

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
        print('Externally served at url {}'.format(self.download_url))
