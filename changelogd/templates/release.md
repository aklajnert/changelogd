## {{ release-title }}  

{% for group in entry-groups %}
### {{ group.title %}  
{% for entry in group.entries %}{{ entry }}{% endfor %}
{% endfor %}  
