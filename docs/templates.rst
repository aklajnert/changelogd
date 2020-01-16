Templates
=========

The ``templates`` directory should be placed in the same directory where the ``config.yaml``
file. The ``changelogd init`` command will prepare the templates for you. By default, you 
can generate templates in ``Markdown`` format or change to ``ReStructuredText`` (with  
``changelogd init --rst``). 

You can have your templates (and the output changelog) in any other text format you like, 
just make sure that the template file names start with ``main``, ``release`` and ``entry``.

Templates are using `Jinja2 <https://jinja.palletsprojects.com/en/2.10.x/>`_ for rendering
the data. All templates have access to the fields defined in ``context`` within ``config.yaml``.

main
----

This is the top-level template of the output changelog file. You can add some header and 
footer here. The list of releases is passed into the template via ``releases`` variable, 
which should be printed in a loop:  

.. code-block:: jinja

   {% for release in releases %}{{ release }}{% endfor %}

release
-------

This template is responsible for displaying single release instances. It has access to
all variables within the data from ``YAML`` release representations.  The release should
iterate over entry groups, and display their content. Entry groups is stored as a list 
in ``entry_groups`` variable. Each group contain ``title`` which is the ``title`` from
``message_types`` defined in ``config.yaml``, and ``entries`` that is a single entry 
representation.

.. code-block:: jinja

   {% for group in entry_groups %}
       ### {{ group.title }}  
       {% for entry in group.entries %}
           {{ entry }}
       {% endfor %}
   {% endfor %}

entry
-----

Defines how the particular entry will be shown. It has access to all variables defined
in entry's ``YAML`` representation.

