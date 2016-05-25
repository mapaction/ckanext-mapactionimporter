'''Test helper functions and classes.'''
import os

import ckan.tests.helpers as helpers
import ckan.plugins as plugins

from ckanext.mapactionimporter.plugin import create_product_themes


def get_test_xml():
    return get_test_file('MA001_Aptivate_Example.xml')


def get_test_zip():
    return get_test_file('MA001_Aptivate_Example.zip')


def get_update_zip():
    return get_test_file('MA001_Aptivate_Example_Update.zip')


def get_not_zip():
    return get_test_file('MA001_Aptivate_Example.txt')


def get_zip_no_metadata():
    return get_test_file('MA001_Missing_Metadata.zip')


def get_zip_empty_metadata():
    return get_test_file('MA001_Empty_Metadata.zip')


def get_special_characters_zip():
    return get_test_file('MA001_Special_Characters.zip')


def get_test_file(filename):
    return file(os.path.join(os.path.split(__file__)[0],
        './test-data/', filename))


class _UploadFile(object):
    '''Mock the parts from cgi.FileStorage we use.'''
    def __init__(self, fp):
        self.file = fp


class FunctionalTestBaseClass(helpers.FunctionalTestBase):
    @classmethod
    def setup_class(cls):
        super(FunctionalTestBaseClass, cls).setup_class()
        plugins.load('mapactionimporter')

    def setup(self):
        super(FunctionalTestBaseClass, self).setup()
        create_product_themes()

    @classmethod
    def teardown_class(cls):
        plugins.unload('mapactionimporter')
        super(FunctionalTestBaseClass, cls).teardown_class()
