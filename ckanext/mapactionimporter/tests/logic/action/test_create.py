import nose.tools

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

        nose.tools.assert_true(len(resources) == 2)

        sorted_resources = sorted(resources, key=lambda k: k['format'])

        self._check_uploaded_resource(sorted_resources[0],
                                      'JPEG',
                                      'MA001_Aptivate_Example-300dpi.jpeg',
                                      'ma001aptivateexample-300dpi.jpeg')
        self._check_uploaded_resource(sorted_resources[1],
                                      'PDF',
                                      'MA001_Aptivate_Example-300dpi.pdf',
                                      'ma001aptivateexample-300dpi.pdf')

    def _check_uploaded_resource(self, resource, expected_format,
                                 expected_name,
                                 expected_basename):
        nose.tools.assert_equal(resource['url_type'], 'upload')
        nose.tools.assert_equal(resource['format'], expected_format)
        nose.tools.assert_equal(resource['name'], expected_name)

        basename = resource['url'].split('/')[-1]
        nose.tools.assert_equal(basename, expected_basename)


class _UploadFile(object):
    '''Mock the parts from cgi.FileStorage we use.'''
    def __init__(self, fp):
        self.file = fp
