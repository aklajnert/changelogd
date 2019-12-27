* {% if issue_id is defined and issue_id %}[#{{ issue_id }}]({{ issues_url }}/{{ issue_id }}): {% endif %}{{ message }}{% if os_user and git_email %} ([@{{ os_user }}]({{ git_email }})){% endif %}  

