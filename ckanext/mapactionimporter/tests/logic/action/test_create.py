import nose.tools

import ckan.tests.helpers as helpers
import ckan.tests.factories as factories
import ckanext.mapactionimporter.tests.helpers as custom_helpers
import ckan.plugins.toolkit as toolkit


class TestCreateDatasetFromZip(custom_helpers.FunctionalTestBaseClass):

    def test_it_allows_uploading_a_zipfile(self):
        dataset = helpers.call_action(
            'create_dataset_from_mapaction_zip',
            upload=custom_helpers._UploadFile(custom_helpers.get_test_zip()))

        nose.tools.assert_equal(
            dataset['title'],
            'Central African Republic:  Example Map- Reference (as of 3 Feb 2099)')

        nose.tools.assert_equal(
            dataset['name'],
            '189-ma001-aptivate-example')

        # Expect the JPEG And PDF referenced in the XML Metadata
        dataset = helpers.call_action('package_show', id=dataset['id'])
        resources = dataset['resources']
        extras = dataset['extras']

        nose.tools.assert_true(len(resources) == 2)
        nose.tools.assert_true(len(extras) > 0)

        sorted_resources = sorted(resources, key=lambda k: k['format'])

        self._check_uploaded_resource(sorted_resources[0],
                                      'JPEG',
                                      'MA001_Aptivate_Example-300dpi.jpeg',
                                      'ma001aptivateexample-300dpi.jpeg')
        self._check_uploaded_resource(sorted_resources[1],
                                      'PDF',
                                      'MA001_Aptivate_Example-300dpi.pdf',
                                      'ma001aptivateexample-300dpi.pdf')

    def test_dataset_private_when_organization_specified(self):
        user = factories.User()
        organization = factories.Organization(user=user)
        dataset = helpers.call_action(
            'create_dataset_from_mapaction_zip',
            context={'user': user['id']},
            upload=custom_helpers._UploadFile(custom_helpers.get_test_zip()),
            owner_org=organization['id'])
        nose.tools.assert_true(dataset['private'])

    def test_dataset_public_when_no_organization_specified(self):
        dataset = helpers.call_action(
            'create_dataset_from_mapaction_zip',
            upload=custom_helpers._UploadFile(custom_helpers.get_test_zip()))
        nose.tools.assert_false(dataset['private'])

    def test_dataset_notes_set_to_xml_summary(self):
        dataset = helpers.call_action(
            'create_dataset_from_mapaction_zip',
            upload=custom_helpers._UploadFile(custom_helpers.get_test_zip()))

        summary = ("Example reference map of the Central African Republic.  This "
                   "is an example map only and for testing use only")
        nose.tools.assert_equal(dataset['notes'], summary)

    def _check_uploaded_resource(self, resource, expected_format,
                                 expected_name,
                                 expected_basename):
        nose.tools.assert_equal(resource['url_type'], 'upload')
        nose.tools.assert_equal(resource['format'], expected_format)
        nose.tools.assert_equal(resource['name'], expected_name)

        basename = resource['url'].split('/')[-1]
        nose.tools.assert_equal(basename, expected_basename)

    def test_it_raises_if_no_zip_file(self):
        with nose.tools.assert_raises(toolkit.ValidationError) as cm:
            helpers.call_action(
                'create_dataset_from_mapaction_zip',
                upload=u''
            )

        nose.tools.assert_equals(cm.exception.error_summary,
                                 {'Upload':
                                  'You must select a file to be imported'})

    def test_it_raises_if_not_a_zip_file(self):
        with nose.tools.assert_raises(toolkit.ValidationError) as cm:
            helpers.call_action(
                'create_dataset_from_mapaction_zip',
                upload=_UploadFile(custom_helpers.get_not_zip()))

        nose.tools.assert_equals(cm.exception.error_summary,
                                 {'File':
                                  'File is not a zip file'})

    def test_it_raises_if_no_metadata(self):
        with nose.tools.assert_raises(toolkit.ValidationError) as cm:
            helpers.call_action(
                'create_dataset_from_mapaction_zip',
                upload=_UploadFile(custom_helpers.get_zip_no_metadata()))

        nose.tools.assert_equals(cm.exception.error_summary,
                                 {'File':
                                  'Could not find metadata XML in zip file'})


class _UploadFile(object):
    '''Mock the parts from cgi.FileStorage we use.'''
    def __init__(self, fp):
        self.file = fp
