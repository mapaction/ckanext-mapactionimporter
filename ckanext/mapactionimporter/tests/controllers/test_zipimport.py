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
        slug = 'ma001-aptivate-example'
        user = factories.User()
        env = {'REMOTE_USER': user['name'].encode('ascii')}
        url = toolkit.url_for('import_mapactionzip')
        response = self.app.post(
            url,
            extra_environ=env,
            upload_files=[(
                'upload',
                custom_helpers.get_test_file().name,
            )],
        )

        # Should redirect to dataset's page
        assert_equals(response.status_int, 302)
        assert_regexp_matches(
            response.headers['Location'],
            '/dataset/%s' % slug)

        # Should create the dataset
        dataset = helpers.call_action('package_show', id=slug)
        assert_equals(dataset['name'], slug)
