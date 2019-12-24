## {{ release_title or release_version }} ({{ release_date }})  
{% if release_description %}
{{ release_description }}  
{% endif %}{% for group in entry_groups %}
### {{ group.title }}  
{% for entry in group.entries %}{{ entry }}{% endfor %}{% endfor %}  
