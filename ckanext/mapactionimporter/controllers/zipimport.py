import ckan.model as model
import ckan.plugins.toolkit as toolkit


class ZipImportController(toolkit.BaseController):
    def new(self, data=None, errors=None, error_summary=None):
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user,
            'auth_user_obj': toolkit.c.userobj,
        }
        self._authorize_or_abort(context)

        errors = errors or {}
        error_summary = error_summary or {}

        default_data = {
            'owner_org': toolkit.request.params.get('group'),
        }
        data = data or default_data

        return toolkit.render(
            'mapactionimporter/import_zip.html',
            extra_vars={
                'data': data,
                'errors': errors,
                'error_summary': error_summary,
            }
        )

    def import_dataset(self):
        context = {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user,
        }
        self._authorize_or_abort(context)

        try:
            params = toolkit.request.params
            dataset = toolkit.get_action(
                'create_dataset_from_mapaction_zip')(
                    context,
                    params,
                )
            toolkit.redirect_to(controller='package',
                                action='edit',
                                id=dataset['name'])
        except toolkit.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.new(data=params,
                            errors=errors,
                            error_summary=error_summary)

    def _authorize_or_abort(self, context):
        try:
            toolkit.check_access('package_create', context)
        except toolkit.NotAuthorized:
            toolkit.abort(401,
                toolkit._('Unauthorized to create a dataset'))
