import json
import tempfile
from copy import deepcopy
from io import StringIO
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock

import yaml

from bin.input_parser import InputParser
from bin.input_parser import validate_schema

simple_json = '{"foo": {"bar": "value"}}'

simple_yaml = '''
    foo:
      bar: value
'''

sample_input = """
    reveal:
      tracks:
        - name: "Sample BAM 1"
          path: /path1/sample1.bam
      capture:
        regions:
            - path: /path3/regions.bed
              prefix: "TEST_"
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

    def test__validate_schema__valid_input(self):
        yaml_stream = StringIO(deepcopy(sample_input))
        with open(self.schema_path, 'r') as schema_file:
            json_input = yaml.safe_load(yaml_stream)
            json_schema = json.load(schema_file)

        result, _ = validate_schema(json_input, json_schema)
        self.assertTrue(result)

    def test__validate_schema__invalid_input_bed_regions(self):
        string_data = deepcopy(sample_input).replace("/path3/regions.bed", "wrong_extension.ext")
        yaml_stream = StringIO(string_data)

        with open(self.schema_path, 'r') as schema_file:
            json_input = yaml.safe_load(yaml_stream)
            json_schema = json.load(schema_file)

        result, message = validate_schema(json_input, json_schema)
        self.assertFalse(result)
        self.assertEqual(message, "BED-3 file for capture regions must be provided, "
                                  "cannot contain spaces and must have extension '.bed'")

    def test__validate_schema__invalid_missing_tracks(self):
        yaml_stream = StringIO(deepcopy(sample_input))

        with open(self.schema_path, 'r') as schema_file:
            json_input = yaml.safe_load(yaml_stream)
            json_schema = json.load(schema_file)

        json_input['reveal']['tracks'].pop()
        result, message = validate_schema(json_input, json_schema)
        self.assertFalse(result)
        self.assertTrue("tracks" in message)
        self.assertTrue("[] is too short" in message)

    def test__check_schema(self):
        yaml_stream = StringIO(deepcopy(sample_input))

        with tempfile.NamedTemporaryFile('w', suffix='.yml') as temp_file:
            temp_file.write(sample_input)
            temp_file.flush()
            parser = InputParser(temp_file.name, "s3://ref/path")
            validated_json = parser._check_schema()

        sample_input_json = yaml.safe_load(yaml_stream)
        self.assertEqual(validated_json, sample_input_json)

    def test__load_data(self):
        with tempfile.NamedTemporaryFile('w', suffix='.yml') as temp_file:
            temp_file.write(sample_input)
            temp_file.flush()
            parser = InputParser(temp_file.name, "/sample/reference/path.fa")
            parser._load_data()
        print(parser)

    def test__check_reference__invalid_extension(self):
        parser = Mock(spec=InputParser,
                      reference="mm10.fasta",
                      VALID_REFERENCE=InputParser.VALID_REFERENCE)
        with self.assertRaises(AssertionError) as contex:
            InputParser._check_reference(parser)
        self.assertEqual('The input file has an unrecognized extension: mm10.fasta. '
                         'It should be one of: .fq.gz, .fastq.gz, .fa, .fa.gz', str(contex.exception))

    def test__check_reference__s3path(self):
        parser = Mock(spec=InputParser,
                      reference="s3://ngi-igenomes/igenomes/test_genome.fa",
                      VALID_REFERENCE=InputParser.VALID_REFERENCE)
        InputParser._check_reference(parser)

    def test__check_tracks__invalid_extension(self):
        parser = Mock(spec=InputParser,
                      tracks=[{"name": "Track 1", "path": "/path/track1.fa"}],
                      VALID_TRACKS=InputParser.VALID_TRACKS)
        with self.assertRaises(AssertionError) as contex:
            InputParser._check_tracks(parser)
        self.assertEqual(str(contex.exception), 'The input file has an unrecognized extension: /path/track1.fa. '
                                                'It should be one of: .bed, .vcf, .bam')
