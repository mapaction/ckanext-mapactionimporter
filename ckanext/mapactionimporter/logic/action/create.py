from defusedxml.ElementTree import parse

import os
import cgi

from slugify import slugify
import tempfile
import zipfile

from ckan.common import _
import ckan.plugins.toolkit as toolkit

from ckanext.mapactionimporter.lib import metadataimporter


class MapPackageException(Exception):
    pass


def join_lines(text):
    """ Return input text without newlines """
    return ' '.join(text.splitlines())


def create_dataset_from_zip(context, data_dict):
    upload = data_dict.get('upload')
    if not _upload_attribute_is_valid(upload):
        msg = {'file': [_('You must select a file to be imported')]}
        raise toolkit.ValidationError(msg)

    private = data_dict.get('private', True)

    try:
        map_package = _load_and_validate_map_package(upload)
    except (MapPackageException) as e:
        msg = {'file': [e.args[0]]}
        raise toolkit.ValidationError(msg)

    dataset_dict = map_package_to_dataset_dict(map_package)

    file_paths = dataset_dict.get('file_paths', [])
    if file_paths:
        del dataset_dict['file_paths']

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


def _load_and_validate_map_package(upload):
    map_package = {}

    tempdir = tempfile.mkdtemp('-mapactionzip')

    metadata_paths = []
    file_paths = []
    try:
        with zipfile.ZipFile(upload.file, 'r') as z:
            z.extractall(tempdir)
            for f in z.namelist():
                full_path = os.path.join(tempdir, f)
                if f.endswith('.xml'):
                    metadata_paths.append(full_path)
                else:
                    file_paths.append(full_path)
    except zipfile.BadZipfile:
        raise MapPackageException(_('File is not a zip file'))

    if len(metadata_paths) == 0:
        raise MapPackageException(_('Could not find metadata XML in zip file'))

    map_package['metadata_file'] =  metadata_paths[0]
    map_package['file_paths'] = file_paths

    return map_package


def map_package_to_dataset_dict(map_package):
    dataset_dict = {}

    et = parse(map_package['metadata_file'])

    dataset_dict['title'] = join_lines(et.find('.//mapdata/title').text)
    map_id = et.find('.//mapdata/ref').text
    operation_id = et.find('.//mapdata/operationID').text
    dataset_dict['name'] = slugify('%s %s' % (operation_id, map_id))
    dataset_dict['notes'] = join_lines(et.find('.//mapdata/summary').text)
    dataset_dict['extras'] = [
        {'key': k, 'value': v} for (k, v) in
        metadataimporter.map_metadata_to_ckan_extras(et).items()
    ]

    dataset_dict['file_paths'] = map_package['file_paths']

    return dataset_dict


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
