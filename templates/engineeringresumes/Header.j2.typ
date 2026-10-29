{% set profile = namespace(text="") %}
{% for section in cv.rendercv_sections %}
{% if section.title == "Profil" %}
{% set profile.text = section.entries | join(" ") %}
{% endif %}
{% endfor %}

#grid(
  columns: (1fr, 1.25fr),
  column-gutter: 0.8cm,
  align: top + left,
  [
{% if cv.name %}
= {{ cv.name }}
{% endif %}
{% if cv.headline %}
#text(size: 9.5pt, weight: "bold")[{{ cv.headline | replace("industrialisation", "#box[industrialisation]") | replace("agroalimentaires", "#box[agroalimentaires]") }}]
{% endif %}
#v(0.18cm)
#text(size: 8.5pt)[
#stack(
  spacing: 0.11cm,
{% for connection in cv._connections[:3] %}
  [{% if loop.index0 == 0 %}#strong[Adresse :] #h(0.06cm){% elif loop.index0 == 1 %}#strong[Mail :] #h(0.06cm){% elif loop.index0 == 2 %}#strong[Tél :] #h(0.06cm){% endif %}{{ connection }}],
{% endfor %}
  [#link("{{ cv.website }}", icon: false, if-underline: false, if-color: false)[#strong[Site Web Portfolio]] #h(0.10cm) | #h(0.10cm) #link("https://linkedin.com/in/{{ cv.social_networks[0].username }}", icon: false, if-underline: false, if-color: false)[#fa-icon("linkedin", size: 1.15em)]],
)
]
  ],
  [
#text(size: 10pt, weight: "bold")[PROFIL]
#v(0.05cm)
#line(length: 100%, stroke: 0.5pt)
#v(0.10cm)
#text(size: 9pt)[{{ profile.text }}]
  ],
)
#v(0.18cm)
