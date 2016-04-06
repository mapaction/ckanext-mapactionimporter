import os
import cgi
import uuid

from ckan.common import _
import ckan.logic as logic
import ckan.plugins.toolkit as toolkit

from ckanext.mapactionimporter.lib import mappackage


def create_dataset_from_zip(context, data_dict):
    upload = data_dict.get('upload')
    if not _upload_attribute_is_valid(upload):
        msg = {'upload': [_('You must select a file to be imported')]}
        raise toolkit.ValidationError(msg)

    private = data_dict.get('private', True)

    try:
        dataset_dict, file_paths = mappackage.to_dataset(upload.file)
    except (mappackage.MapPackageException) as e:
        msg = {'upload': [e.args[0]]}
        raise toolkit.ValidationError(msg)

    owner_org = data_dict.get('owner_org')
    if owner_org:
        dataset_dict['owner_org'] = owner_org
    else:
        private = False

    dataset_dict['private'] = private

    custom_dict = _get_custom_dict(dataset_dict)
    operation_id = custom_dict['operationID'].zfill(5)

    try:
        toolkit.get_action('group_show')(
            context,
            data_dict={'type': 'event', 'id': operation_id})
    except (logic.NotFound) as e:
        msg = {'upload': [_("Event with operationID '{0}' does not exist").format(
            operation_id)]}
        raise toolkit.ValidationError(msg)

    # TODO:
    # If we do this, we get an error "User foo not authorized to edit these groups
    # dataset_dict['groups'] = [{'name': operation_id]

    final_name = dataset_dict['name']
    dataset_dict['name'] = '{0}-{1}'.format(final_name, uuid.uuid4())
    dataset = toolkit.get_action('package_create')(context, dataset_dict)

    try:
        for resource_file in file_paths:
            resource = {
                'package_id': dataset['id'],
                'path': resource_file,
            }
            _create_and_upload_local_resource(context, resource)
    except:
        toolkit.get_action('package_delete')(context, {'id': dataset['id']})
        raise

    toolkit.get_action('member_create')(context, {
        'id': operation_id,
        'object': dataset['id'],
        'object_type': 'package',
        'capacity': 'member',  # TODO: What does capacity mean in this context?
    })

    dataset_dict = toolkit.get_action('package_show')(
        context, {'id': dataset['id']})
    dataset_dict['name'] = final_name
    dataset = toolkit.get_action('package_update')(context, dataset_dict)

    return dataset


def _get_custom_dict(dataset_dict):
    # CKAN expects custom keys to be unique
    return {c['key']: c['value'] for c in dataset_dict['extras']}


def _upload_attribute_is_valid(upload):
    return hasattr(upload, 'file') and hasattr(upload.file, 'read')


def _create_and_upload_local_resource(context, resource):
    path = resource['path']
    del resource['path']
    with open(path, 'r') as the_file:
        _create_and_upload_resource(context, resource, the_file)


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
