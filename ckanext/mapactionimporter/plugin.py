import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.mapactionimporter.logic.action.create


class MapactionimporterPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'mapactionimporter')

    def before_map(self, map_):
        map_.connect(
            'import_mapactionzip',
            '/import_mapactionzip',
            controller='ckanext.mapactionimporter.controllers.zipimport:ZipImportController',
            action='new',
            conditions=dict(method=['GET']),
        )
        map_.connect(
            'import_mapactionzip',
            '/import_mapactionzip',
            controller='ckanext.datapackager.controllers.zipimport:ZipImportController',
            action='import_dataset',
            conditions=dict(method=['POST']),
        )

        return map_

    def get_actions(self):
        return {
            'create_dataset_from_mapaction_zip':
            ckanext.mapactionimporter.logic.action.create.create_dataset_from_zip,
        }
