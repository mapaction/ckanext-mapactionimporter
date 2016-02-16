import nose.tools

import ckan.tests.factories as factories
import ckan.tests.helpers as helpers
import ckan.plugins.toolkit as toolkit
import ckanext.mapactionimporter.tests.helpers as custom_helpers

assert_equals = nose.tools.assert_equals
assert_true = nose.tools.assert_true
assert_regexp_matches = nose.tools.assert_regexp_matches


class TestDataPackageController(custom_helpers.FunctionalTestBaseClass):

    def test_import_zipfile(self):
        user = factories.User()
        organization = factories.Organization(user=user)

        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('import_mapactionzip')

        params = {
            'owner_org': organization['id'],
        }

        response = self.app.post(
            url,
            params,
            extra_environ=env,
            upload_files=[(
                'upload',
                custom_helpers.get_test_zip().name,
            )],
        )

        # Should redirect to dataset's page
        assert_equals(response.status_int, 302)

        slug = '189-ma001-aptivate-example'
        assert_regexp_matches(
            response.headers['Location'],
            '/dataset/edit/%s' % slug)

        # Should create the dataset
        dataset = helpers.call_action('package_show', id=slug)
        assert_equals(dataset['name'], slug)
        assert_equals(dataset['private'], True)

    @helpers.change_config('ckan.auth.create_unowned_dataset', False)
    def test_cannot_display_form_without_access(self):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('import_mapactionzip')
        response = self.app.get(url, extra_environ=env, status=[401])
        assert_true('Unauthorized to create a dataset' in response.body)

    @helpers.change_config('ckan.auth.create_unowned_dataset', False)
    def test_cannot_create_dataset_without_access(self):
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('import_mapactionzip')
        response = self.app.post(url, extra_environ=env, status=[401])
        assert_true('Unauthorized to create a dataset' in response.body)
