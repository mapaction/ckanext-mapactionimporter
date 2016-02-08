import ckan.plugins.toolkit as toolkit


class ZipImportController(toolkit.BaseController):
    def new(self, data=None, errors=None, error_summary=None):
        errors = errors or {}
        error_summary = error_summary or {}
        data = data or {}

        return toolkit.render(
            'mapactionimporter/import_zip.html',
            extra_vars={
                'data': data,
                'errors': errors,
                'error_summary': error_summary,
            }
        )
