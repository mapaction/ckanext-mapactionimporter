import os

import tempfile
import zipfile

from ckan.common import _

from defusedxml.ElementTree import parse
from slugify import slugify

EXCLUDE_TAGS = (
    'status',
    'title',
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
            z.extractall(tempdir)
            for f in z.namelist():
                full_path = os.path.join(tempdir, f)
                if f.endswith('.xml'):
                    metadata_paths.append(full_path)
                else:
                    file_paths.append(full_path)
    except zipfile.BadZipfile:
        raise MapPackageException(_('File is not a zip file'))


    # Expect a single metadata file
    assert len(metadata_paths) == 1
    metadata_file = metadata_paths[0]

    et = parse(metadata_file)

    # Extract key metadata
    dataset_dict = {}
    dataset_dict['title'] = join_lines(et.find('.//mapdata/title').text)

    map_id = et.find('.//mapdata/ref').text
    operation_id = et.find('.//mapdata/operationID').text
    dataset_dict['name'] = slugify('%s %s' % (operation_id, map_id))

    dataset_dict['notes'] = join_lines(et.find('.//mapdata/summary').text)
    dataset_dict['extras'] = [
        {'key': k, 'value': v} for (k, v) in
            map_metadata_to_ckan_extras(et).items()
    ]

    return (dataset_dict, file_paths)