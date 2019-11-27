## {{ release-title }} ({{ release-date }})  

{{ release-description }}

{% for group in entry-groups %}
### {{ group.title %}  
{% for entry in group.entries %}{{ entry }}{% endfor %}
{% endfor %}  
