History  
=======

0.1.9 (2025-01-12)  
------------------

Features  
~~~~~~~~
* `#71 <https://github.com/aklajnert/changelogd/pull/71>`_: Allow to render empty sections.

Bug fixes  
~~~~~~~~~
* `#65 <https://github.com/aklajnert/changelogd/pull/65>`_: Fixed release command when already existing release version is passed.

0.1.8 (2023-02-24)  
------------------

Features  
~~~~~~~~
* `#37 <https://github.com/aklajnert/changelogd/pull/37>`_: Allow to set default values for entries.
* `#36 <https://github.com/aklajnert/changelogd/pull/36>`_: Allow to add entry to the existing release.

0.1.7 (2022-10-10)  
------------------

Minor improvements  
~~~~~~~~~~~~~~~~~~
* `#26 <https://github.com/aklajnert/changelogd/pull/26>`_: Trim whitespace from multi-value fields.

Other changes  
~~~~~~~~~~~~~
* `#25 <https://github.com/aklajnert/changelogd/pull/25>`_: Switch to GitHub Actions.

0.1.6 (2022-09-06)  
------------------

Features  
~~~~~~~~
* `#21 <https://github.com/aklajnert/changelogd/pull/21>`_: Add support for computed values.

Minor improvements  
~~~~~~~~~~~~~~~~~~
* `#7 <https://github.com/aklajnert/changelogd/pull/7>`_: Add a readme file that will be put into the changelogd config directory.

Other changes  
~~~~~~~~~~~~~
* `#19 <https://github.com/aklajnert/changelogd/pull/19>`_: Remove invalid pytest option.
* `#18 <https://github.com/aklajnert/changelogd/pull/18>`_: Add support for python 3.9 and 3.10, fix tests.

0.1.5 (2020-01-30)  
------------------

Minor improvements  
~~~~~~~~~~~~~~~~~~
* `#6 <https://github.com/aklajnert/changelogd/pull/6>`_: Add __main__.py file to allow invoking via `python -m changelogd`.

0.1.4 (2020-01-24)  
------------------

Minor improvements  
~~~~~~~~~~~~~~~~~~
* `#5 <https://github.com/aklajnert/changelogd/pull/5>`_: Save timestamp with entry YAML, so the order won't be affected by simple file modification.
* `#4 <https://github.com/aklajnert/changelogd/pull/4>`_: Display entry title with `Select message type` question.

0.1.3 (2020-01-20)  
------------------

Features  
~~~~~~~~
* `#2 <https://github.com/aklajnert/changelogd/pull/2>`_: Allow to control which user data will be saved in entries.
* `#3 <https://github.com/aklajnert/changelogd/pull/3>`_: Automatically add new entries and releases to git.

Other changes  
~~~~~~~~~~~~~
* `#1 <https://github.com/aklajnert/changelogd/pull/1>`_: Switch from ``tox`` to ``nox`` for running tests and tasks.

0.1.2 (2020-01-17)  
------------------

Bug fixes  
~~~~~~~~~
* Fixed missing templates from the ``MANIFEST.in``

0.1.1 (2020-01-16)  
------------------

Initial release  
