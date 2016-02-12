import os
import cgi
import random

from ckan.common import _
import ckan.plugins.toolkit as toolkit

from ckanext.mapactionimporter.lib import mappackage


def create_dataset_from_zip(context, data_dict):
    upload = data_dict.get('upload')
    if not _upload_attribute_is_valid(upload):
        msg = {'file': [_('You must select a file to be imported')]}
        raise toolkit.ValidationError(msg)

    private = data_dict.get('private', True)

    try:
        dataset_dict, file_paths = mappackage.to_dataset(upload.file)
    except (mappackage.MapPackageException) as e:
        msg = {'file': [e.args[0]]}
        raise toolkit.ValidationError(msg)

    owner_org = data_dict.get('owner_org')
    if owner_org:
        dataset_dict['owner_org'] = owner_org
    else:
        private = False

    dataset_dict['private'] = private

    dataset = toolkit.get_action('package_create')(context, dataset_dict)

    for resource_file in file_paths:
        resource = {
            'package_id': dataset['id'],
            'path': resource_file,
        }
        _create_and_upload_local_resource(context, resource)

    return dataset


def _upload_attribute_is_valid(upload):
    return hasattr(upload, 'file') and hasattr(upload.file, 'read')


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
    resource['name'] = os.path.basename(the_file.name)
    toolkit.get_action('resource_create')(context, resource)


class _UploadLocalFileStorage(cgi.FieldStorage):
    def __init__(self, fp, *args, **kwargs):
        self.name = fp.name
        self.filename = fp.name
        self.file = fp
