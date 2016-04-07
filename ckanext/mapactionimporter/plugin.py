import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.mapactionimporter.logic.action.create

## Must be alphanumeric characters or symbols: -_.
PRODUCT_THEMES = (
    "Affected Population",
    "Agriculture",
    "Appeals",
    "Camp Coordination or Management",
    "Early Recovery",
    "Education",
    "Emergency Shelter",
    "Emergency Telecommunications",
    "Environmental Aspects",
    "Health",
    "Logistics",
    "Nutrition",
    "P-codes",
    "Population Baseline",
    "Reference and Orientation",
    "Search and Rescue or Evacuation Planning",
    "Search and Rescue Sectors",
    "Security and Safety and Protection",
    "Situation and Damage",
    "Water Sanitation and Hygiene",
    "Who-What-Where",
)

def register_translator():
    # https://github.com/ckan/ckanext-archiver/blob/master/ckanext/archiver/bin/common.py
    # If not set (in cli access), patch the a translator with a mock, so the
    # _() functions in logic layer don't cause failure.
    from paste.registry import Registry
    from pylons import translator
    from ckan.lib.cli import MockTranslator
    if 'registery' not in globals():
        global registry
        registry = Registry()
        registry.prepare()

    if 'translator_obj' not in globals():
        global translator_obj
        translator_obj = MockTranslator()
        registry.register(translator, translator_obj)

def create_product_themes():
    register_translator()

    user = toolkit.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'product_themes'}
        vocab = toolkit.get_action('vocabulary_show')(context, data)
        tags = toolkit.get_action('tag_list')(context, {'vocabulary_id': vocab['id']})
        for tag in PRODUCT_THEMES:
            if tag in tags:
                tags.remove(tag)
            else:
                data = {'name': tag, 'vocabulary_id': vocab['id'], 'display_name': "Foo"}
                toolkit.get_action('tag_create')(context, data)
        for tag in tags:
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            toolkit.get_action('tag_delete')(context, data)
    except toolkit.ObjectNotFound:
        data = {'name': 'product_themes'}
        vocab = toolkit.get_action('vocabulary_create')(context, data)
        for tag in PRODUCT_THEMES:
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            toolkit.get_action('tag_create')(context, data)


def product_themes(query=None):
    try:
        tag_list = toolkit.get_action('tag_list')
        product_themes = tag_list(data_dict={'vocabulary_id': 'product_themes', 'all_fields': True, 'query': query})
        return product_themes
    except toolkit.ObjectNotFound:
        return []


class MapactionimporterPlugin(plugins.SingletonPlugin, toolkit.DefaultDatasetForm):
    plugins.implements(plugins.IDatasetForm)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.IFacets, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)

    # IFacets
    def dataset_facets(self, facets_dict, package_type):
        facets_dict['vocab_product_themes'] = plugins.toolkit._('Theme')
        return facets_dict


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
            controller='ckanext.mapactionimporter.controllers.zipimport:ZipImportController',
            action='import_dataset',
            conditions=dict(method=['POST']),
        )

        return map_

    def get_actions(self):
        return {
            'create_dataset_from_mapaction_zip':
            ckanext.mapactionimporter.logic.action.create.create_dataset_from_zip,
        }

    def get_helpers(self):
        return {'product_themes': product_themes}

    def _modify_package_schema(self, schema):
        schema.update({
            'product_themes': [
                toolkit.get_validator('ignore_missing'),
                toolkit.get_converter('convert_to_tags')('product_themes')
            ]
        })
        return schema


    def show_package_schema(self):
        schema = super(MapactionimporterPlugin, self).show_package_schema()
        schema['tags']['__extras'].append(toolkit.get_converter('free_tags_only'))
        schema.update({
            'product_themes': [
                toolkit.get_converter('convert_from_tags')('product_themes'),
                toolkit.get_validator('ignore_missing')]
            })
        return schema

    def create_package_schema(self):
        schema = super(MapactionimporterPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(MapactionimporterPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []
