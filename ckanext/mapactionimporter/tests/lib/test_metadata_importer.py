import unittest

import ckanext.mapactionimporter.tests.helpers as custom_helpers

from defusedxml.ElementTree import parse
from ckanext.mapactionimporter.lib import mappackage


class TestMapMetadataToCkanExtras(unittest.TestCase):

    def setUp(self):
        et = parse(custom_helpers.get_test_xml())
        self.extras_dict = mappackage.map_metadata_to_ckan_extras(et)
        self.assertTrue(len(self.extras_dict) > 0)

    def test_status_excluded(self):
        self.assertNotIn('status', self.extras_dict)

    def test_title_excluded(self):
        self.assertNotIn('title', self.extras_dict)

    def test_operationID_excluded(self):
        self.assertNotIn('operationID', self.extras_dict)
