#!/usr/bin/env python


"""Provide a command line tool to validate and transform tabular samplesheets."""

import argparse
import csv
import logging
import sys
from collections import Counter
from pathlib import Path
import yaml
import json
from jsonschema import validate


logger = logging.getLogger()


def validate_schema(json_input, json_schema):
    try:
        validate(instance=json_input, schema=json_schema)
        return True, ""
    except Exception as error:
        message = error.schema['errorMessage'] if 'errorMessage' in error.schema else str(error.path) + " " + error.message
        return False, message


def validate_format(filename, valid_formats):
    """Assert that a given filename has one of the expected extensions."""
    if not any(filename.endswith(extension) for extension in valid_formats):
        raise AssertionError(
            f"The input file has an unrecognized extension: {filename}\n"
            f"It should be one of: {', '.join(valid_formats)}"
        )


class InputParser:
    """
    Define a service that can validate and transform the input yaml containing tracks, regions, and options.

    """
    INPUT_SCHEMA = "../assets/schema_input.json"

    VALID_FASTA_FORMATS = (
        ".fq.gz",
        ".fastq.gz",
    )

    def __init__(self, reference=None, tracks=[], capture_regions="", igv_options=[],
                 **kwargs):
        super().__init__(**kwargs)
        if reference is None:
            reference = {"type": "genome", "value": ""}
        self.reference = reference
        self.tracks = tracks
        self.capture_regions = capture_regions
        self.igv_options = igv_options

    def _check_schema(self, input_file_path):
        base_path = Path(__file__).parent
        schema_path = (base_path / self.INPUT_SCHEMA).resolve()

        with open(input_file_path, 'r') as input_file, open(schema_path, 'r') as schema_file :
            json_input = yaml.safe_load(input_file)
            json_schema = json.load(schema_file)
            validation, message = validate_schema(json_input, json_schema)
            if not validation:
                raise AssertionError(message)

    def _load_data(self, input_file_path):
        self._check_schema(input_file_path)



