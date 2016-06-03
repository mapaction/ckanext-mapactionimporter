import unittest

import ckanext.mapactionimporter.tests.helpers as custom_helpers

from defusedxml.ElementTree import parse, fromstring
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

    def test_versionNumber_excluded(self):
        self.assertNotIn('versionNumber', self.extras_dict)


class TestPopulateDatasetDictFromXml(unittest.TestCase):
    template_xml = """<?xml version="1.0" encoding="utf-8"?>
<mapdoc>
  <mapdata>
    <operationID>{operationid}</operationID>
    <title>{title}</title>
    <ref>{ref}</ref>
    <summary>{summary}</summary>
    <theme>Orientation and Reference</theme>
    <mapNumber>{mapnumber}</mapNumber>
    <versionNumber>{versionnumber}</versionNumber>
  </mapdata>
</mapdoc>
    """

    def test_empty_summary_copied_to_notes(self):
        et = self._parse_xml(summary='')
        dataset_dict = mappackage.populate_dataset_dict_from_xml(et)

        self.assertEqual(dataset_dict['notes'], '')

    def test_missing_summary_copied_to_notes(self):
        et = self._parse_xml()
        self._remove_from_etree(et, './/mapdata', 'summary')

        dataset_dict = mappackage.populate_dataset_dict_from_xml(et)

        self.assertEqual(dataset_dict['notes'], '')

    def test_summary_newlines_replaced_with_spaces(self):
        et = self._parse_xml(summary='one\ntwo\r\nthree\rfour\n\nfive\r\n\r\nsix\r\rseven')

        dataset_dict = mappackage.populate_dataset_dict_from_xml(et)

        self.assertEqual(dataset_dict['notes'], 'one two three four  five  six  seven')

    def test_missing_title_copied_to_title(self):
        et = self._parse_xml()
        self._remove_from_etree(et, './/mapdata', 'title')

        dataset_dict = mappackage.populate_dataset_dict_from_xml(et)

        self.assertEqual(dataset_dict['title'], '')

    def test_no_themes_when_missing(self):
        et = self._parse_xml()
        self._remove_from_etree(et, './/mapdata', 'theme')

        dataset_dict = mappackage.populate_dataset_dict_from_xml(et)

        self.assertTrue('product_themes' not in dataset_dict)

    def test_it_raises_when_mandatory_field_missing(self):
        mandatory_fields = ('operationID',
                            'mapNumber',
                            'versionNumber')

        for f in mandatory_fields:
            et = self._parse_xml()

            self._remove_from_etree(et, './/mapdata', f)

            with self.assertRaises(mappackage.MapPackageException):
                mappackage.populate_dataset_dict_from_xml(et)

    def test_it_raises_when_version_number_non_numeric(self):
        et = self._parse_xml(versionnumber='v1')

        with self.assertRaises(mappackage.MapPackageException) as e:
            mappackage.populate_dataset_dict_from_xml(et)

        self.assertEquals(e.exception.args[0],
                          "Version number 'v1' must be an integer")

    def test_name_includes_operation_id_map_number_and_version(self):
        et = self._parse_xml(operationid='00123', mapnumber='MA001',
                             versionnumber='02')
        dataset_dict = mappackage.populate_dataset_dict_from_xml(et)

        self.assertEqual(dataset_dict['name'], '00123-ma001-v2')

    def test_version_number_stored_in_ckan_version(self):
        et = self._parse_xml(versionnumber='2')
        dataset_dict = mappackage.populate_dataset_dict_from_xml(et)

        self.assertEqual(dataset_dict['version'], 2)

    def _remove_from_etree(self, et, parent_xpath, child_xpath):
        for parent in et.findall(parent_xpath):
            for child in parent.findall(child_xpath):
                parent.remove(child)

    def _parse_xml(self, **kwargs):
        defaults = {
            'mapnumber': 'default-map-no',
            'operationid': 'default-op-id',
            'ref': 'default-ref',
            'summary': 'default-summary',
            'theme': 'default-theme',
            'title': 'default-title',
            'versionnumber': '987',
        }

        values = {}

        for tag, default in defaults.iteritems():
            values[tag] = kwargs.get(tag, default)

        xml = self.template_xml.format(**values)

        return fromstring(xml)
