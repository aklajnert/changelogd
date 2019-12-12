## {{ release_title }} ({{ release_date }})  

{{ release_description }}

{% for group in entry_groups %}
### {{ group.title }}  
{% for entry in group.entries %}{{ entry }}{% endfor %}
{% endfor %}  
