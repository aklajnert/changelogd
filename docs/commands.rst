Commands
========

Changelogd consists of multiple independent subcommands to make the changelog 
management as easy as possible.

Init
----

This command initialized ``changelogd`` configuration including default templates. 
By default, it will create a new ``changelog.d`` directory in current work directory. 
You can select different directory with ``--path`` argument.

.. code-block:: bash

    $ changelogd init
    Created main configuration file: /workdir/changelog.d/config.yaml
    Copied templates to /workdir/changelog.d/templates

Entry
-----

Creates a new changelog entry. By default it asks for the entry type, issue id and the
changelog message. This can be changed by modifying the ``message_types`` in ``config.yaml``. 
Also, the ``entry`` subcommand will try to extract git username and e-mail and the system
username.

.. code-block:: bash

    $ changelogd entry
            [1]: feature
            [2]: bug
            [3]: doc
            [4]: deprecation
            [5]: other
    > Select message type [1]: 1
    > Issue ID (separate multiple values with comma): 100
    > Changelog message (required): A new feature implementation.
    Created changelog entry at /workdir/changelog.d/feature.f155ee47.entry.yaml

As a result, a following ``YAML`` file will be created:

.. code-block:: yaml

   git_email: github@aklajnert.pl
   git_user: Andrzej Klajnert
   issue_id:
   - '100'
   message: A new feature implementation.
   os_user: aklajnert
   type: feature

