Pyrene - Python Repository Network tool
=======================================

I am a tool to help your interactions with Python package repositories.
I can copy packages between repos for you without modifying any config files.

There are three types of repos I support, probably this covers all you might need:
- https://pypi.python.org - the global python public package repo
- ~/.pip/local - a directory with package files, for fast/offline development
- project specific PyPI server - defined by you or your company, for deployment

I provide a shell-like environment as primary interface - with completion for commands and parameters, but can be used as a command-line tool as well.

I support the following commands:

Command: `use repo`
-------------------

Creates/overwrites a `pip.conf` config file, for use by the outer environment: installing packages with `pip` can be greatly influenced by the `~/.pip/pip.conf` configuration file: it defines which repo is used to download from (`index-url` or `find-links`) and how (`no-use-wheels`, etc.)


Command: copy package[s] repo:
------------------------------

Copy packages like files with `cp`.


Command: define repo download-url [upload-url username password]
----------------------------------------------------------------


Command: set repo key=value
---------------------------


Command: forget repo
--------------------


Command: list
-------------


Command: show repo
------------------


Developers
==========

Packages are downloaded with [pip](http://www.pip-installer.org).

Packages are uploaded with code adopted from [twine](https://pypi.python.org/pypi/twine).

Guidelines:
- all code should be extremely simple and clear
- all features require unit tests
- zero messages from flake8

Contributions
- improving on the simplicity and clarity of the code
- or providing new badly missing features (preferably with tests)
are welcome.
