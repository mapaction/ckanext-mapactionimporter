import nose.tools

import ckan.tests.helpers as helpers
import ckan.tests.factories as factories
import ckanext.mapactionimporter.tests.helpers as custom_helpers
import ckan.plugins.toolkit as toolkit
import ckan.lib.uploader as uploader


class TestCreateDatasetFromZip(custom_helpers.FunctionalTestBaseClass):
    def setup(self):
        super(TestCreateDatasetFromZip, self).setup()
        self.user = factories.User()


class TestCreateDatasetForEvent(TestCreateDatasetFromZip):
    def setup(self):
        super(TestCreateDatasetForEvent, self).setup()
        self.group_189 = factories.Group(name='00189', user=self.user)

        helpers.call_action(
            'group_member_create',
            id=self.group_189['id'],
            username=self.user['name'],
            role='editor')

    def test_it_allows_uploading_a_zipfile(self):
        dataset = helpers.call_action(
            'create_dataset_from_mapaction_zip',
            upload=custom_helpers._UploadFile(custom_helpers.get_test_zip()))

        nose.tools.assert_equal(
            dataset['title'],
            'Central African Republic: Example Map- Reference (as of 3 Feb 2099)')

        nose.tools.assert_equal(
            dataset['name'],
            '189-ma001-01')

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
        organization = factories.Organization(user=self.user)
        dataset = helpers.call_action(
            'create_dataset_from_mapaction_zip',
            context={'user': self.user['id']},
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

    def test_dataset_license_defaults_to_not_specified(self):
        dataset = helpers.call_action(
            'create_dataset_from_mapaction_zip',
            upload=custom_helpers._UploadFile(custom_helpers.get_test_zip()))
        nose.tools.assert_equals(dataset['license_id'], 'notspecified')

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
                                 {'Upload':
                                  'File is not a zip file'})

    def test_it_raises_if_no_metadata(self):
        with nose.tools.assert_raises(toolkit.ValidationError) as cm:
            helpers.call_action(
                'create_dataset_from_mapaction_zip',
                upload=_UploadFile(custom_helpers.get_zip_no_metadata()))

        nose.tools.assert_equals(cm.exception.error_summary,
                                 {'Upload':
                                  'Could not find metadata XML in zip file'})

    def test_it_raises_if_empty_metadata(self):
        with nose.tools.assert_raises(toolkit.ValidationError) as cm:
            helpers.call_action(
                'create_dataset_from_mapaction_zip',
                upload=_UploadFile(custom_helpers.get_zip_empty_metadata()))

        nose.tools.assert_equals(cm.exception.error_summary,
                                 {'Upload':
                                  "Error parsing XML: 'no element found: line 1, column 0'"})

    def test_it_tidies_up_if_resource_creation_fails(self):
        old_max_resource_size = uploader._max_resource_size
        uploader._max_resource_size = 1

        with nose.tools.assert_raises(toolkit.ValidationError) as cm:
            helpers.call_action(
                'create_dataset_from_mapaction_zip',
                upload=_UploadFile(custom_helpers.get_test_zip()))

        nose.tools.assert_equals(cm.exception.error_summary,
                                 {'Upload':
                                  'File upload too large'})

        datasets = helpers.call_action(
            'package_list',
            context={'user': self.user['name']})

        # The dataset will be in the trash so won't appear here
        nose.tools.assert_equals(len(datasets), 0)

        uploader._max_resource_size = old_max_resource_size

        dataset = helpers.call_action(
            'create_dataset_from_mapaction_zip',
            upload=_UploadFile(custom_helpers.get_test_zip()))

        nose.tools.assert_equal(
            dataset['name'],
            '189-ma001-01')

    def test_it_raises_if_file_has_special_characters(self):
        with nose.tools.assert_raises(toolkit.ValidationError) as cm:
            helpers.call_action(
                'create_dataset_from_mapaction_zip',
                upload=_UploadFile(custom_helpers.get_special_characters_zip()))

        nose.tools.assert_equals(cm.exception.error_summary, {
            'Upload':
            "Error parsing XML: 'not well-formed (invalid token): line 22, column 47'",
        })

    def test_it_attaches_to_event_with_operation_id_from_metadata(self):
        dataset = helpers.call_action(
            'create_dataset_from_mapaction_zip',
            context={'user': self.user['name']},
            upload=custom_helpers._UploadFile(custom_helpers.get_test_zip()),
        )

        dataset = helpers.call_action(
            'package_show',
            context={'user': self.user['name']},
            id=dataset['id'])
        events = dataset['groups']

        nose.tools.assert_equals(len(events), 1)
        nose.tools.assert_equals(events[0]['name'], '00189')

    def test_new_version_associated_with_existing(self):
        version_1 = helpers.call_action(
            'create_dataset_from_mapaction_zip',
            upload=custom_helpers._UploadFile(custom_helpers.get_test_zip()))

        nose.tools.assert_equal(version_1['name'], '189-ma001-01')

        version_2 = helpers.call_action(
            'create_dataset_from_mapaction_zip',
            upload=custom_helpers._UploadFile(custom_helpers.get_update_zip()))

        nose.tools.assert_equal(version_2['name'], '189-ma001-02')

        [parent_1] = helpers.call_action(
            'package_relationships_list',
            id=version_1['id'],
            rel='child_of')

        [parent_2] = helpers.call_action(
            'package_relationships_list',
            id=version_2['id'],
            rel='child_of')

        nose.tools.assert_equal(parent_1['subject'], '189-ma001-01')
        nose.tools.assert_equal(parent_1['type'], 'child_of')
        nose.tools.assert_equal(parent_1['object'], '189-ma001')

        nose.tools.assert_equal(parent_2['subject'], '189-ma001-02')
        nose.tools.assert_equal(parent_2['type'], 'child_of')
        nose.tools.assert_equal(parent_2['object'], '189-ma001')


class TestCreateDatasetForNoEvent(TestCreateDatasetFromZip):
    def test_it_raises_if_event_does_not_exist(self):
        with nose.tools.assert_raises(toolkit.ValidationError) as cm:
            helpers.call_action(
                'create_dataset_from_mapaction_zip',
                upload=_UploadFile(custom_helpers.get_test_zip()))

        nose.tools.assert_equals(cm.exception.error_summary, {
            'Upload':
            "Event with operationID '00189' does not exist",
        })


class _UploadFile(object):
    '''Mock the parts from cgi.FileStorage we use.'''
    def __init__(self, fp):
        self.file = fp
