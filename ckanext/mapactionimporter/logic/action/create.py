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
        dataset_dict, file_paths, operation_id = mappackage.to_dataset(
            upload.file)
    except (mappackage.MapPackageException) as e:
        msg = {'upload': [e.args[0]]}
        raise toolkit.ValidationError(msg)

    owner_org = data_dict.get('owner_org')
    if owner_org:
        dataset_dict['owner_org'] = owner_org
    else:
        private = False

    dataset_dict['private'] = private

    operation_id = operation_id.zfill(5)

    try:
        toolkit.get_action('group_show')(
            _get_context(context),
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
    dataset = toolkit.get_action('package_create')(
        _get_context(context), dataset_dict)

    try:
        for resource_file in file_paths:
            resource = {
                'package_id': dataset['id'],
                'path': resource_file,
            }
            _create_and_upload_local_resource(_get_context(context), resource)
    except:
        toolkit.get_action('package_delete')(_get_context(context),
                                             {'id': dataset['id']})
        raise

    toolkit.get_action('member_create')(_get_context(context), {
        'id': operation_id,
        'object': dataset['id'],
        'object_type': 'package',
        'capacity': 'member',  # TODO: What does capacity mean in this context?
    })

    dataset_dict = toolkit.get_action('package_show')(
        context, {'id': dataset['id']})
    dataset_dict['name'] = final_name

    try:
        dataset = toolkit.get_action('package_update')(
            _get_context(context), dataset_dict)
    except toolkit.ValidationError as e:
        if _('That URL is already in use.') in e.error_dict.get('name', []):
            e.error_dict['name'] = [_('"%s" already exists.' % final_name)]
        raise e

    # TODO: Is there a neater way so we don't have to reverse engineer the
    # parent name?
    parent_name = '-'.join(final_name.split('-')[0:-1])
    parent = _get_or_create_parent_dataset(context,
                                           {'name': parent_name,
                                            'owner_org': owner_org})

    toolkit.get_action('package_relationship_create')(
        _get_context(context), {
            'subject': dataset['id'],
            'object': parent['id'],
            'type': 'child_of',
        }
    )

    return dataset


def _get_context(context):
    return {
        'model': context['model'],
        'session': context['session'],
        'user': context['user'],
        'ignore_auth': context.get('ignore_auth', False)
    }


def _get_or_create_parent_dataset(context, data_dict):
    try:
        dataset = toolkit.get_action('package_show')(
            _get_context(context), {'id': data_dict['name']})
    except (logic.NotFound):
        dataset = toolkit.get_action('package_create')(
            _get_context(context), data_dict)

    return dataset


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
