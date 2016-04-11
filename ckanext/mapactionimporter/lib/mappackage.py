import os

import logging
import shutil
import tempfile
import zipfile

from ckan.common import _

from defusedxml.ElementTree import parse, ParseError
from slugify import slugify

log = logging.getLogger(__name__)

# Valid CKAN tags must only contain alphanumeric characters or symbols: -_.
PRODUCT_THEMES = (
    "Affected Population",
    "Agriculture",
    "Appeals",
    "Camp Coordination or Management",
    "Early Recovery",
    "Education",
    "Emergency Shelter",
    "Emergency Telecommunications",
    "Environmental Aspects",
    "Health",
    "Logistics",
    "Nutrition",
    "P-codes",
    "Population Baseline",
    "Orientation and Reference",
    "Search and Rescue or Evacuation Planning",
    "Search and Rescue Sectors",
    "Security and Safety and Protection",
    "Situation and Damage",
    "Water Sanitation and Hygiene",
    "Who-What-Where",
)


EXCLUDE_TAGS = (
    'status',
    'title',
    'operationID',
    'theme',
)


class MapPackageException(Exception):
    pass


def map_metadata_to_ckan_extras(et):
    map_metadata = {}
    for e in et.findall('./mapdata/*'):
        if e.tag in EXCLUDE_TAGS:
            continue
        map_metadata[e.tag] = e.text
    return map_metadata


def join_lines(text):
    """ Return input text without newlines """
    return ' '.join(text.splitlines())


def to_dataset(map_package):
    # Extract the map package
    tempdir = tempfile.mkdtemp('-mapactionzip')

    metadata_paths = []
    file_paths = []
    try:
        with zipfile.ZipFile(map_package, 'r') as z:
            for i in z.infolist():
                filename = i.filename.encode('cp437')
                full_path = os.path.join(tempdir, filename)

                with open(full_path, 'wb') as outputfile:
                    shutil.copyfileobj(z.open(i.filename), outputfile)

                if filename.endswith('.xml'):
                    metadata_paths.append(full_path)
                else:
                    file_paths.append(full_path)
    except zipfile.BadZipfile:
        raise MapPackageException(_('File is not a zip file'))

    # Expect a single metadata file
    if len(metadata_paths) == 0:
        raise MapPackageException(_('Could not find metadata XML in zip file'))
    metadata_file = metadata_paths[0]

    try:
        et = parse(metadata_file)
    except ParseError as e:
        raise MapPackageException(_("Error parsing XML: '{0}'".format(
            e.msg.args[0])))

    dataset_dict = populate_dataset_dict_from_xml(et)
    operation_id = et.find('.//mapdata/operationID').text

    return (dataset_dict, file_paths, operation_id)


def populate_dataset_dict_from_xml(et):
    # Extract key metadata
    dataset_dict = {}
    dataset_dict['title'] = join_lines(et.find('.//mapdata/title').text)

    map_id = et.find('.//mapdata/ref').text
    operation_id = et.find('.//mapdata/operationID').text
    dataset_dict['name'] = slugify('%s %s' % (operation_id, map_id))

    theme = et.find('.//mapdata/theme').text
    if theme in PRODUCT_THEMES:
        dataset_dict['product_themes'] = [theme]
    else:
        log.error('Product theme "%s" not defined in PRODUCT_THEMES' % theme)

    dataset_dict['notes'] = join_lines(et.find('.//mapdata/summary').text)
    dataset_dict['extras'] = [
        {'key': k, 'value': v} for (k, v) in
        map_metadata_to_ckan_extras(et).items()
    ]

    return dataset_dict
