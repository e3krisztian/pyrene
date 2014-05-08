# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os
try:
    from ConfigParser import RawConfigParser
except ImportError:
    def RawConfigParser():
        import configparser
        return configparser.ConfigParser(interpolation=None)

from .repos import BadRepo, DirectoryRepo, HttpRepo
from .constants import REPO, REPOTYPE


class UnknownRepoError(NameError):
    '''Repo is not defined at all'''


class Network(object):

    REPO_TYPES = {
        REPOTYPE.DIRECTORY,
        REPOTYPE.HTTP,
    }

    REPO_ATTRIBUTES = set(
        DirectoryRepo.ATTRIBUTES
    ).union(
        set(HttpRepo.ATTRIBUTES)
    )

    REPO_SECTION_PREFIX = 'repo:'

    TYPE_TO_CLASS = {
        REPOTYPE.DIRECTORY: DirectoryRepo,
        REPOTYPE.HTTP: HttpRepo,
    }

    # name of active/default/ repo
    active_repo = None

    def __init__(self, filename):
        self._repo_store_filename = filename
        self._config = None
        self.active_repo = None
        self.reload()

    def reload(self):
        self._config = RawConfigParser()
        if os.path.exists(self._repo_store_filename):
            self._config.read(self._repo_store_filename)

    def _save(self):
        with open(self._repo_store_filename, 'wt') as f:
            self._config.write(f)

    def get_repo(self, repo_name):
        repo_name = repo_name or self.active_repo
        repokey = self.REPO_SECTION_PREFIX + repo_name
        if not self._config.has_section(repokey):
            raise UnknownRepoError(repo_name)

        attributes = self.get_attributes(repo_name)
        repo_type = attributes.get(REPO.TYPE)

        repo_class = self.TYPE_TO_CLASS.get(repo_type, BadRepo)
        return repo_class(repo_name, attributes)

    def define(self, repo_name):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        self._config.add_section(repokey)
        self._save()

    def forget(self, repo_name):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        self._config.remove_section(repokey)
        self._save()

    def set(self, repo_name, attribute, value):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        self._config.set(repokey, attribute, value)
        self._save()

    def unset(self, repo_name, attribute):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        self._config.remove_option(repokey, attribute)
        self._save()

    @property
    def repo_names(self):
        return [
            section[len(self.REPO_SECTION_PREFIX):]
            for section in self._config.sections()
            if section.startswith(self.REPO_SECTION_PREFIX)
        ]

    def get_attributes(self, repo_name):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        if not self._config.has_section(repokey):
            raise UnknownRepoError(repo_name)

        attributes = {
            attribute: self._config.get(repokey, attribute)
            for attribute in self._config.options(repokey)
        }
        return attributes
