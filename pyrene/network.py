# Py3 compatibility
from __future__ import print_function
from __future__ import unicode_literals

import os
from ConfigParser import RawConfigParser
from .repos import BadRepo, DirectoryRepo, HttpRepo
from .constants import REPO, REPOTYPE


class UnknownRepoError(NameError):
    '''Repo is not defined at all'''


TYPE_TO_CLASS = {
    REPOTYPE.DIRECTORY: DirectoryRepo,
    REPOTYPE.HTTP: HttpRepo,
}


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

    def __init__(self, filename):
        self._repo_store_filename = filename
        self._config = None
        self.reload()

    def reload(self):
        self._config = RawConfigParser()
        if os.path.exists(self._repo_store_filename):
            self._config.read(self._repo_store_filename)

    def _save(self):
        with open(self._repo_store_filename, 'wt') as f:
            self._config.write(f)

    def get_repo(self, repo_name):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        if not self._config.has_section(repokey):
            raise UnknownRepoError(repo_name)

        attributes = self.get_attributes(repo_name)
        repo_type = attributes.get(REPO.TYPE)

        return TYPE_TO_CLASS.get(repo_type, BadRepo)(repo_name, attributes)

    def define(self, repo_name):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        self._config.add_section(repokey)
        self._save()

    def forget(self, repo_name):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        self._config.remove_section(repokey)
        self._save()

    def set(self, repo_name, key, value):
        repokey = self.REPO_SECTION_PREFIX + repo_name
        self._config.set(repokey, key, value)
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
            option: self._config.get(repokey, option)
            for option in self._config.options(repokey)
        }
        return attributes
