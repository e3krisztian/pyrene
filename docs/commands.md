Commands
========


copy
----

Copy packages with the same ease like local files with `cp` (or remote with `rsync`!).

```
Pyrene: copy SOURCE DESTINATION
```

Where `SOURCE` can be either `LOCAL-FILE` or `REPO:PACKAGE-SPEC`,
`DESTINATION` can be either a `REPO:` or a `LOCAL-DIRECTORY`

list
----

Lists known repositories.

show
----

Shows repository attributes

```
Pyrene: show repo
```

directory_repo
--------------

Defines a new `directory` repository or change an existing repo's the type to `directory`.

```
Pyrene: directory_repo repo
Pyrene[repo]: list
  repo
```

http_repo
---------

Defines a new `http` repository or change an existing repo's the type to `http`.

```
Pyrene: http_repo repo
Pyrene[repo]: list
  repo
```

set
---

Sets a repository attribute.

```
Pyrene: work_on repo
Pyrene[repo]: set attribute=value
Pyrene[repo]: show
  attribute: value
```

unset
-----

Removes a repository attribute

```
Pyrene: show repo
  attribute: value
Pyrene: work_on repo
Pyrene[repo]: unset attribute
Pyrene[repo]: show
```

forget
------

Makes a known repository unknown.

```
Pyrene: forget repo
Pyrene: list
```

setup_for_pypi_python_org
-------------------------

Configures repo to point to the default package index https://pypi.python.org.

```
Pyrene: setup_for_pip_local pypi
Pyrene: show pypi
  upload_url: https://pypi.python.org/
  type: http
  download_url: https://pypi.python.org/simple/
```

setup_for_pip_local
-------------------

Configures repo to be directory based and sets directory to `~/.pip/local`.
Also makes that directory if needed.

```
Pyrene: setup_for_pip_local local
Pyrene: show local
  directory: /home/user/.pip/local
  type: directory
```

use
---

How `pip` works can be greatly influenced by the `~/.pip/pip.conf` configuration file: it defines which repo is used to download from (`index-url` or `find-links`) and how (`no-use-wheels`, etc.)

When you say `use` I'll create a minimal `pip.conf` config file (*or overwrite silently the existing one!!!*) so that `pip` will use the given repo outside of `Pyrene` for downloads: 

```
Pyrene: use repo
```

serve
-----

For directory repos fire up a pypi-server on the repository.
For http repos show where it is already served.

work_on
-------

Sets the implicit/active repo.
This repo will serve as implicit repo parameter for most commands.

See e.g. [set](#set) or [unset](#unset)
