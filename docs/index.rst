.. Changelogd documentation master file, created by
   sphinx-quickstart on Sat Jan 11 13:46:11 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Changelogd
==========

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Changelogd allows teams to avoid merge conflicts for the changelog files. 
The ``changelogd`` content is stored within multiple YAML files - one per each 
changelog entry. Then, during application release, all input files are combined 
into one release file. The script uses Jinja2 templates to generate one consistent 
text file out of all input YAML files. The default output format is Markdown, but 
by modifying the templates it can be changed into any text format you like. 

Installation
------------

You can install ``changelogd`` via `pip`_ from `PyPI`_::

    $ pip install changelogd

Quickstart
----------

First, initialize ``changelogd`` configuration.

.. code-block:: bash

    $ changelogd init
    Created main configuration file: changelog.d\config.yaml
    Copied templates to changelog.d\templates

Then, create changelog entries:

.. code-block:: bash

    $ changelogd entry
            [1]: feature
            [2]: bug
            [3]: doc
            [4]: deprecation
            [5]: other
    > Select message type [1]: 2
    > Issue ID: 100
    > Changelog message: Changelog message
    Created changelog entry at changelog.d\bug.a3f13823.entry.yaml

Finally, generate changelog file.

.. code-block:: bash

    $ changelogd release version-number
    > Release description (hit ENTER to omit): This is the initial release.
    Saved new release data into changelog.d\releases\0.release-name.yaml
    Generated changelog file to changelog.md

Output file:

.. code-block:: md

    # Changelog  
    
    
    ## version-number (2020-01-11)  
    
    This is the initial release.  
    
    ### Bug fixes  
    * [#100](http://repo/issues/100): Changelog message ([@user](user@example.com))  

Contents
--------

.. toctree::
   :maxdepth: 2

   commands
   configuration
   templates
   history

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _`pip`: https://pypi.org/project/pip/
.. _`PyPI`: https://pypi.org/project
