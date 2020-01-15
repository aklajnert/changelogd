* {% if issue_id is defined and issue_id -%}
{% for iid in issue_id -%}
`#{{ iid }} <{{ issues_url }}/{{ iid }}>_{% if not loop.last %}, {% endif %}
{%- endfor %}: {% endif -%}
{{ message }}
{%- if os_user and git_email %} ([@{{ os_user }}](mailto:{{ git_email }})){% endif %}  

