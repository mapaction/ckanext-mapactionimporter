from defusedxml.ElementTree import parse

EXCLUDE_TAGS = (
    'status',
    'title',
)

def map_metadata_to_ckan_extras(et):
    map_metadata = {}
    for e in et.findall('./mapdata/*'):
        if e.tag in EXCLUDE_TAGS:
            continue
        map_metadata[e.tag] = e.text
    return map_metadata
