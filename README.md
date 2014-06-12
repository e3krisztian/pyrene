<figure>
  <img src="docs/pyrene.png"/>
  <figcaption>Pyrene</figcaption>
</figure>

a _Py_ thon _Re_ pository _Ne_ twork tool
=========================================

I am a tool to help your interactions with Python package repositories.

For example I can copy packages between repos, or configure `pip` to use
a private repository instead of the default http://pypi.python.org.

I provide a shell-like environment as primary interface - with help and completion for commands and attributes, but I can be used as a command-line tool as well.

There are two types of repos I know about:

- http repos, e.g.
    - https://pypi.python.org - the global python public package repo
    - project specific PyPI server - defined by you or your company, for deployment
- directory repos, that is
    - a directory with package files, for fast/offline development
    - `~/.pip/local` - one such directory


Installation
============

From PyPI:

```
mkvirtualenv app-pyrene
pip install pyrene
```

`master` branch directly from GitHub:

```
mkvirtualenv app-pyrene
pip install git+https://github.com/krisztianfekete/pyrene.git
```

In order to have `pyrene` without activating its `virtualenv` do the following
(assuming `~/bin` is on your `PATH`):

```
ln -s ~/.virtualenvs/app-pyrene/bin/pyrene ~/bin
```

Usage
=====

State consists of:
- set of repositories
- an active repository (initially None) that is used for the repo parameter when it is not given for most commands (also called implicit repo)

I listen to commands, that

- operate on repos ([copy][cmd-copy], [serve][cmd-serve], [use][cmd-use])
- show details about the state ([list][cmd-list], [show][cmd-show])
- change state
  - set the active/implicit repo ([work_on][cmd-work_on])
  - define or undefine repositories ([directory_repo][cmd-directory_repo], [http_repo][cmd-http_repo], [forget][cmd-forget])
  - change repository parameters ([set][cmd-set], [unset][cmd-unset], [setup_for_pip_local][cmd-setup_for_pip_local], [setup_for_pypi_python_org][cmd-setup_for_pypi_python_org])


Development
===========

`Pyrene` is a work in progress, with sharp edges, miswordings...

So

contributions
-------------

- reporting issues
- improving documentation
- improving on the simplicity and clarity of the code/interface
- adding relevant tests
- providing new badly missing features (preferably with tests)
- showing alternatives

are welcome.

Guidelines:
-----------

- all code should be extremely simple and clear, including tests
- all features require unit tests
- zero messages from [flake8]
- usability, simplicity wins over feature completeness
- the smallest the change, the better

The current code might violate these, but it is then considered a bug.
Fixing any of these violations - even if it looks trivial is welcome!

External packages/tools:
------------------------

- packages are downloaded with [pip]
- packages are uploaded to http/https repos with [twine]
- local packages are served with [pypiserver]

[cmd-http_repo]: docs/commands.md#http_repo
[cmd-directory_repo]: docs/commands.md#directory_repo
[cmd-forget]: docs/commands.md#forget
[cmd-work_on]: docs/commands.md#work_on
[cmd-set]: docs/commands.md#set
[cmd-unset]: docs/commands.md#unset
[cmd-setup_for_pip_local]: docs/commands.md#setup_for_pip_local
[cmd-setup_for_pypi_python_org]: docs/commands.md#setup_for_pypi_python_org
[cmd-list]: docs/commands.md#list
[cmd-show]: docs/commands.md#show
[cmd-copy]: docs/commands.md#copy
[cmd-serve]: docs/commands.md#serve
[cmd-use]: docs/commands.md#use

[github repo]: https://github.com/krisztianfekete/pyrene
[flake8]: https://pypi.python.org/pypi/flake8
[pip]: http://www.pip-installer.org
[twine]: https://pypi.python.org/pypi/twine
[pypiserver]: https://pypi.python.org/pypi/pypiserver
