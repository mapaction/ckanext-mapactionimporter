import nose.tools
import os

import ckan.tests.helpers as helpers
import ckanext.mapactionimporter.tests.helpers as custom_helpers


class TestCreateDatasetFromZip(custom_helpers.FunctionalTestBaseClass):

    def test_it_allows_uploading_a_zipfile(self):
        test_file = file(os.path.join(
            os.path.split(__file__)[0],
            '../../test-data/MA001_Aptivate_Example.zip'))

        dataset = helpers.call_action('create_dataset_from_mapaction_zip',
                                      upload=_UploadFile(test_file))
        nose.tools.assert_equal(
            dataset['title'],
            'Central African Republic:  Example Map- Reference (as of 3 Feb 2099)')


class _UploadFile(object):
    '''Mock the parts from cgi.FileStorage we use.'''
    def __init__(self, fp):
        self.file = fp
