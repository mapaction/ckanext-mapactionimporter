from defusedxml.ElementTree import parse

import os
import cgi

from slugify import slugify
import tempfile
import zipfile

import ckan.plugins.toolkit as toolkit


def create_dataset_from_zip(context, data_dict):
    upload = data_dict.get('upload')
    map_package = upload.file

    tempdir = tempfile.mkdtemp('-mapactionzip')

    metadata_paths = []
    file_paths = []
    with zipfile.ZipFile(map_package, 'r') as z:
        z.extractall(tempdir)
        for f in z.namelist():
            full_path = os.path.join(tempdir, f)
            if f.endswith('.xml'):
                metadata_paths.append(full_path)
            else:
                file_paths.append(full_path)

    assert len(metadata_paths) == 1
    metadata_file = metadata_paths[0]

    et = parse(metadata_file)

    dataset_dict = {}

    owner_org = data_dict.get('owner_org')
    if owner_org:
        dataset_dict['owner_org'] = owner_org

    title_lines = et.find('.//mapdata/title').text.splitlines()
    dataset_dict['title'] = ' '.join(title_lines)

    dataset_dict['name'] = slugify(et.find('.//mapdata/ref').text)
    dataset = toolkit.get_action('package_create')(context, dataset_dict)

    for resource_file in file_paths:
        resource = {
            'package_id': dataset['id'],
            'path': resource_file,
        }
        _create_and_upload_local_resource(context, resource)

    return dataset


def _create_and_upload_local_resource(context, resource):
    path = resource['path']
    del resource['path']
    try:
        with open(path, 'r') as the_file:
            _create_and_upload_resource(context, resource, the_file)
    except IOError:
        msg = {'datapackage': [(
            "Couldn't create some of the resources."
            " Please make sure that all resources' files are accessible."
        )]}
        raise toolkit.ValidationError(msg)


def _create_and_upload_resource(context, resource, the_file):
    resource['url'] = 'url'
    resource['url_type'] = 'upload'
    resource['upload'] = _UploadLocalFileStorage(the_file)
    toolkit.get_action('resource_create')(context, resource)


class _UploadLocalFileStorage(cgi.FieldStorage):
    def __init__(self, fp, *args, **kwargs):
        self.name = fp.name
        self.filename = fp.name
        self.file = fp
