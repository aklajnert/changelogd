==========
changelogd
==========


.. image:: https://img.shields.io/pypi/v/changelogd.svg
        :target: https://pypi.python.org/pypi/changelogd

.. image:: https://dev.azure.com/aklajnert/changelogd/_apis/build/status/aklajnert.changelogd?branchName=master


Changelogs without conflicts.


* Free software: MIT license
* Documentation: https://changelogd.readthedocs.io.


Installation
------------

You can install ``changelogd`` via `pip`_ from `PyPI`_::

    $ pip install changelogd

Quickstart
----------

First, initialize ``changelogd`` configuration.

.. code-block:: bash

    > changelogd init
    2019-12-30 19:45:10 - Created main configuration file: changelog.d\config.yaml
    2019-12-30 19:45:10 - Copied templates to changelog.d\templates

Then, create changelog entries:

.. code-block:: bash

    > changelogd entry
            [1]: feature
            [2]: bug
            [3]: doc
            [4]: deprecation
            [5]: other
    Select message type [1]: 2
    Issue ID: 100
    Changelog message: Changelog message
    2019-12-30 19:45:37,825 - Created changelog entry at changelog.d\bug.a3f13823.entry.yaml

Finally, generate changelog file.

.. code-block:: bash

    > changelogd release <release-name>
    Release description (hit ENTER to omit): This is the initial release.
    2019-12-30 19:50:10 - Saved new release data into changelog.d\releases\0.release-name.yaml
    2019-12-30 19:50:10 - Generated changelog file to changelog.md


License
-------

Distributed under the terms of the `MIT`_ license, "pytest-subprocess" is free and open source software

Issues
------

If you encounter any problems, please `file an issue`_ along with a detailed description.



.. _`MIT`: http://opensource.org/licenses/MIT
.. _`file an issue`: https://github.com/aklajnert/changelogd/issues
.. _`pip`: https://pypi.org/project/pip/
.. _`PyPI`: https://pypi.org/project
