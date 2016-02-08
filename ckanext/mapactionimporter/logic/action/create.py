from defusedxml.ElementTree import parse

import os
from slugify import slugify
import tempfile
import zipfile

import ckan.plugins.toolkit as toolkit


def create_dataset_from_zip(context, data_dict):
    upload = data_dict.get('upload')
    map_package = upload.file

    with zipfile.ZipFile(map_package, 'r') as z:
        metadata_path = [f for f in z.namelist()
                         if f.endswith('.xml')][0]

        tempdir = tempfile.mkdtemp('-mapactionzip')
        z.extractall(tempdir)

    metadata_file = os.path.join(tempdir, metadata_path)

    et = parse(metadata_file)

    dataset_dict = {}
    title_lines = et.find('.//mapdata/title').text.splitlines()
    dataset_dict['title'] = ' '.join(title_lines)

    dataset_dict['name'] = slugify(et.find('.//mapdata/ref').text)
    dataset = toolkit.get_action('package_create')(context, dataset_dict)

    return dataset
