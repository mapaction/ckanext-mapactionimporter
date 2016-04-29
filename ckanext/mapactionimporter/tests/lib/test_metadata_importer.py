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


class TestPopulateDatasetDictFromXml(unittest.TestCase):
    template_xml = """<?xml version="1.0" encoding="utf-8"?>
<mapdoc>
  <mapdata>
    <operationID>{operationid}</operationID>
    <title>{title}</title>
    <ref>{ref}</ref>
    <summary>{summary}</summary>
    <theme>Orientation and Reference</theme>
  </mapdata>
</mapdoc>
    """

    def test_empty_summary_copied_to_notes(self):
        et = self._parse_xml(summary='')
        dataset_dict = mappackage.populate_dataset_dict_from_xml(et)

        self.assertEqual(dataset_dict['notes'], '')

    def test_missing_summary_copied_to_notes(self):
        et = self._parse_xml()

        mapdata = et.findall('.//mapdata')[0]
        summary = et.findall('.//summary')[0]
        mapdata.remove(summary)

        dataset_dict = mappackage.populate_dataset_dict_from_xml(et)

        self.assertEqual(dataset_dict['notes'], '')

    def _parse_xml(self, **kwargs):
        tags = (
            'operationid',
            'ref',
            'summary',
            'theme',
            'title',
        )

        values = {}

        for tag in tags:
            values[tag] = kwargs.get(tag, '')

        xml = self.template_xml.format(**values)

        return fromstring(xml)
