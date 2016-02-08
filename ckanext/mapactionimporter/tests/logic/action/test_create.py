import nose.tools
import os

import ckan.tests.helpers as helpers
import ckanext.mapactionimporter.tests.helpers as custom_helpers


class TestCreateDatasetFromZip(custom_helpers.FunctionalTestBaseClass):

    def test_it_allows_uploading_a_zipfile(self):
        dataset = helpers.call_action(
            'create_dataset_from_mapaction_zip',
            upload=_UploadFile(custom_helpers.get_test_file()))

        nose.tools.assert_equal(
            dataset['title'],
            'Central African Republic:  Example Map- Reference (as of 3 Feb 2099)')

        # Expect the JPEG And PDF referenced in the XML Metadata

        dataset = helpers.call_action('package_show', id=dataset['id'])

        resources = dataset['resources']

        import pdb; pdb.set_trace()

        nose.tools.assert_true(len(resources) == 2)
        nose.tools.assert_equal(resources[0]['url_type'], 'upload')
        #nose.tools.assert_true(resources[0]['name'] in resources[0]['url'])


class _UploadFile(object):
    '''Mock the parts from cgi.FileStorage we use.'''
    def __init__(self, fp):
        self.file = fp
