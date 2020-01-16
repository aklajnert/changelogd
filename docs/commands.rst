Commands
========

Changelogd consists of multiple independent subcommands to make the changelog 
management as easy as possible.

init
----

This command initialized ``changelogd`` configuration including default templates. 
By default, it will create a new ``changelog.d`` directory in the current work directory. 
You can select different directory with ``--path`` argument. If you want to use RST format,
use ``--rst`` argument to the ``changelogd init``.

.. code-block:: bash

   $ changelogd init
   Created main configuration file: /workdir/changelog.d/config.yaml
   Copied templates to /workdir/changelog.d/templates

entry
-----

Creates a new changelog entry. By default, it asks for the entry type, issue id, and the
changelog message. This can be changed by modifying the ``message_types`` in ``config.yaml``. 
Also, the ``entry`` subcommand will try to extract git username and e-mail and the system
username. The entry file name will contain a md5 checksum of the file content, to avoid
conflicts. The filename can be changed, as long as it follows the following pattern: 
``<message-type>.<any-string>.entry.yaml``.

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

   git_email: user@example.com
   git_user: Some User
   issue_id:
   - '100'
   message: A new feature implementation.
   os_user: user
   type: feature

draft
-----

Load all input files and resolve templates to generate a changelog. The changelog
will be printed to the stdout stream. 

.. code-block:: bash
   
   $ changelogd draft
   > Release description (hit ENTER to omit): Just draft
   # Changelog
   
   
   ## draft (2020-01-13)
   
   Just draft
   
   ### Features
   * [#100](http://repo/issues/100): A new feature implementation. ([@user](user@example.com))
    
release
-------

Generate a new release file, remove all entries and generate a changelog file. You need to
specify the new release name.

.. warning:: This command will fail if there are no entry files.

.. code-block:: bash

   $ changelogd release 0.1.0
   > Release description (hit ENTER to omit): Demo release
   Saved new release data into /workdir/changelog.d/releases/0.0.1.0.yaml
   Generated changelog file to /workdir/changelog.md

The generated ``YAML`` file will have all entries combined. The release file name will
always start with a number, which will indicate the order of releases within the generated
changelog file. The default content of the ``0.0.1.0.yaml`` file:  

.. code-block:: yaml

   entries:
     feature:
     - git_email: user@example.com
       git_user: Some User
       issue_id:
       - '100'
       message: A new feature implementation.
       os_user: user
   previous_release: null
   release_date: '2020-01-13'
   release_description: Demo release
   release_version: 0.1.0

partial
-------

Generate changelog without clearing entries, release name is taken from config file. 
This will overwrite the changelog file.
Use ``--check`` argument to return exit code = 1 if the output file is different than the 
previously generated one (can be useful in CI/CD).

.. code-block:: bash

   $ changelogd partial
   Generated changelog file to /workdir/changelog.md


