from copy import deepcopy
from unittest import TestCase
from pathlib import Path
from bin.input_parser import validate_schema
from io import StringIO
import yaml
import json

simple_json = '{"foo": {"bar": "value"}}'

simple_yaml = '''
    foo:
      bar: value
'''

sample_input = """
    reveal:
      reference:
        genome: "mm10.fasta"
      tracks:
        - name: "Sample BAM 1"
          path: /path1/sample1.bam
      capture:
        regions: /path3/regions.bed
        slops: [50, 500]
        igvOptions:
          - option: "SKIP_VERSION"
            value: "null,2.12.2"
          - option: "SHOW_SEQUENCE_TRANSLATION"
            value: "true"
"""


class Test(TestCase):

    def setUp(self):
        base_path = Path(__file__).parent
        self.schema_path = (base_path / "../assets/schema_input.json").resolve()

    def test__validate_schema_valid_input(self):
        yaml_stream = StringIO(deepcopy(sample_input))
        with open(self.schema_path, 'r') as schema_file:
            json_input = yaml.safe_load(yaml_stream)
            json_schema = json.load(schema_file)

        result, _ = validate_schema(json_input, json_schema)
        self.assertTrue(result)

    def test__validate_schema_invalid_input_bed_regions(self):
        string_data = deepcopy(sample_input).replace("regions: /path3/regions.bed", "regions: wrong_extension.ext")
        yaml_stream = StringIO(string_data)

        with open(self.schema_path, 'r') as schema_file:
            json_input = yaml.safe_load(yaml_stream)
            json_schema = json.load(schema_file)

        result, message = validate_schema(json_input, json_schema)
        self.assertFalse(result)
        self.assertEqual(message, "BED-3 file for capture regions must be provided, "
                                  "cannot contain spaces and must have extension '.bed'")

    def test__validate_schema_invalid_missing_tracks(self):
        yaml_stream = StringIO(deepcopy(sample_input))

        with open(self.schema_path, 'r') as schema_file:
            json_input = yaml.safe_load(yaml_stream)
            json_schema = json.load(schema_file)

        json_input['reveal']['tracks'].pop()
        result, message = validate_schema(json_input, json_schema)
        self.assertFalse(result)
        self.assertTrue("tracks" in message)
        self.assertTrue("[] is too short" in message)


