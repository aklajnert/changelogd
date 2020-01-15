* {% if pr_ids is defined and pr_ids -%}
{% for pr_id in pr_ids -%}
[#{{ pr_id }}]({{ pr_url }}/{{ pr_id }}){% if not loop.last %}, {% endif %}
{%- endfor %}: {% endif -%}
{{ message }}
{%- if os_user and git_email %} ([@{{ os_user }}](mailto:{{ git_email }})){% endif %}  

