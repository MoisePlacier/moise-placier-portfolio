{% set profile = namespace(is_profile=false) %}
{% for section in cv.rendercv_sections %}
{% if section.title == "Profil" and entry in section.entries %}
{% set profile.is_profile = true %}
{% endif %}
{% endfor %}
{% if not profile.is_profile %}
{{entry}}
{% endif %}
