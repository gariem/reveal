#!/usr/bin/env python


"""Provide a command line tool to validate and transform tabular samplesheets."""
import argparse
import json
import logging
import sys
from os import path
from pathlib import Path

import yaml
from jsonschema import validate

logger = logging.getLogger()


def validate_schema(json_input, json_schema):
    try:
        validate(instance=json_input, schema=json_schema)
        return True, ""
    except Exception as error:
        message = error.schema['errorMessage'] if 'errorMessage' in error.schema else str(
            error.path) + " " + error.message
        return False, message


def validate_format(filename, valid_formats):
    """Assert that a given filename has one of the expected extensions."""
    if not any(filename.endswith(extension) for extension in valid_formats):
        raise AssertionError(
            f"The input file has an unrecognized extension: {filename}. "
            f"It should be one of: {', '.join(valid_formats)}"
        )


def check_file_exists(filename):
    if not path.exists(filename):
        raise AssertionError(f"The input file doesn't exist: {filename}")


class InputParser:
    """
    Define a service that can validate and transform the input yaml containing tracks, regions, and options.

    """
    INPUT_SCHEMA = "../assets/schema_input.json"
    IGENOMES_CONFIG = "../conf/igenomes.config"

    VALID_TRACKS = (".bed", ".vcf", ".bam")
    VALID_REGIONS = ".bed"
    VALID_REFERENCE = (".fq.gz", ".fastq.gz", ".fa", ".fa.gz")

    def __init__(self, input_file):
        self.input_file = input_file
        self.reference = {"type": "genome", "value": ""}
        self.tracks = []
        self.capture_regions = None
        self.slops = []
        self.igv_options = []

    def _load_data(self):
        validated_json = self._check_schema()

        reference_entry = validated_json['reveal']['reference']
        reference_type = 'genome' if 'genome' in reference_entry else 'fasta'
        self.reference = {"type": reference_type, "value": reference_entry[reference_type]}

        for tracks_entry in validated_json['reveal']['tracks']:
            self.tracks.append({"name": tracks_entry['name'], "path": tracks_entry['path']})

        self.capture_regions = validated_json['reveal']['capture']['regions']

        for option_slop in validated_json['reveal']['capture']['slops']:
            self.slops.append(option_slop)

        for option_entry in validated_json['reveal']['capture']['igvOptions']:
            self.igv_options.append({option_entry['option']: option_entry['value']})

    def _check_schema(self):
        base_path = Path(__file__).parent
        schema_path = (base_path / self.INPUT_SCHEMA).resolve()

        with open(self.input_file, 'r') as input_file, open(schema_path, 'r') as schema_file:
            json_input = yaml.safe_load(input_file)
            json_schema = json.load(schema_file)
            validation, message = validate_schema(json_input, json_schema)

        if not validation:
            raise AssertionError(message)
        return json_input

    def _check_reference(self):
        ref_type = self.reference["type"]
        ref_value = self.reference["value"]

        if ref_type == "genome":
            raise AssertionError(
                f"iGenomes reference is not yet supported, "
                f"please provide a full path to a vali ({', '.join(self.VALID_REFERENCE)}) file")
        elif ref_type == "fasta":
            validate_format(ref_value, self.VALID_REFERENCE)
            check_file_exists(ref_value)

    def _check_regions(self):
        validate_format(self.capture_regions, self.VALID_REGIONS)
        check_file_exists(self.capture_regions)

    def _check_tracks(self):
        for track in self.tracks:
            validate_format(track['path'], self.VALID_TRACKS)
            check_file_exists(track['path'])

    def _generate_file_pointers(self, preferences_path, slops_path):
        with open("reveal_params.csv", "w") as pointer:
            pointer.write("entry_type,optional_label,value\n")
            pointer.write(f"reference,{self.reference['type']},{self.reference['value']}\n")
            for track in self.tracks:
                pointer.write(f"track,{track['name']},{track['path']}\n")
            pointer.write(f"regions,-,{self.capture_regions}\n")
            pointer.write(f"slops,-,{slops_path}\n")
            pointer.write(f"preferences,-,{preferences_path}\n")

    def _generate_slops_file(self):
        with open("slops.txt", "w") as slops_file:
            for slop in self.slops:
                slops_file.write(f"{slop}\n")
        return path.realpath(slops_file.name)

    def _generate_igv_preferences_file(self):
        with open("prefs.properties", "w") as properties:
            for option in self.igv_options:
                option, value = next(iter(option.items()))
                properties.write(f"{option}={value}\n")
        return path.realpath(properties.name)

    def build(self):
        self._load_data()
        self._check_schema()
        self._check_reference()
        self._check_regions()
        self._check_tracks()
        preferences_path = self._generate_igv_preferences_file()
        slops_path = self._generate_slops_file()
        self._generate_file_pointers(preferences_path, slops_path)

def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate and transform samplesheet. Output files to same directory",
        epilog="Example: python input_parser.py samplesheet.yaml",
    )
    parser.add_argument(
        "file_in",
        metavar="FILE_IN",
        type=Path,
        help="Input samplesheet in YAML format.",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        help="The desired log level (default WARNING).",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        default="WARNING",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Coordinate argument parsing and program execution."""
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level, format="[%(levelname)s] %(message)s")
    if not args.file_in.is_file():
        logger.error(f"The given input file {args.file_in} was not found!")
        sys.exit(2)
    InputParser(args.file_in).build()


if __name__ == "__main__":
    sys.exit(main())

