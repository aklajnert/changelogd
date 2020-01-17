* {% if pr_ids is defined and pr_ids -%}
{% for pr_id in pr_ids -%}
`#{{ pr_id }} <{{ pr_url }}/{{ pr_id }}>`_{% if not loop.last %}, {% endif %}
{%- endfor %}: {% endif -%}
{{ message }}

