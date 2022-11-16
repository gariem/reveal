#!/usr/bin/env python


"""Provide a command line tool to validate and transform yml samplesheets."""
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

    def __init__(self, params_file, reference):
        self.params_file = params_file
        self.reference = reference
        self.tracks = []
        self.capture_regions = []
        self.slops = []
        self.igv_options = []

    def _load_data(self):
        validated_json = self._check_schema()

        for tracks_entry in validated_json['reveal']['tracks']:
            self.tracks.append({"name": tracks_entry.get('name'), "path": tracks_entry['path']})

        for region_entry in validated_json['reveal']['capture']['regions']:
            self.capture_regions.append({"prefix": region_entry.get('prefix', ''), "path": region_entry['path']})

        for option_slop in validated_json['reveal']['capture']['slops']:
            self.slops.append(option_slop)

        for option_entry in validated_json['reveal']['capture']['igvOptions']:
            self.igv_options.append({option_entry['option']: option_entry['value']})

    def _check_schema(self):
        base_path = Path(__file__).parent
        schema_path = (base_path / self.INPUT_SCHEMA).resolve()

        with open(self.params_file, 'r') as params_file, open(schema_path, 'r') as schema_file:
            json_input = yaml.safe_load(params_file)
            json_schema = json.load(schema_file)
            validation, message = validate_schema(json_input, json_schema)

        if not validation:
            raise AssertionError(message)
        return json_input

    def _check_reference(self):
        validate_format(self.reference, self.VALID_REFERENCE)
        if not self.reference.startswith("s3://"):
            check_file_exists(self.reference)

    def _check_regions(self):
        for region in self.capture_regions:
            validate_format(region['path'], self.VALID_REGIONS)
            check_file_exists(region['path'])

    def _check_tracks(self):
        for track in self.tracks:
            validate_format(track['path'], self.VALID_TRACKS)
            check_file_exists(track['path'])

    def _generate_file_pointers(self, preferences_path, slops_path):
        with open("reveal_params.csv", "w") as pointer:
            pointer.write("type,value,label\n")
            pointer.write(f"reference,{self.reference}\n")
            for track in self.tracks:
                pointer.write(f"track,{track['path']},{track['name']}\n")
            for region in self.capture_regions:
                pointer.write(f"region,{region['path']},{region['prefix']}\n")
            pointer.write(f"slops,{slops_path}\n")
            pointer.write(f"preferences,{preferences_path}\n")

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
        "--file_in",
        type=Path,
        help="Input samplesheet in YAML format.",
    )
    parser.add_argument(
        "--reference",
        help="Reference file (fasta or igenomes).",
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
    InputParser(args.file_in, args.reference).build()


if __name__ == "__main__":
    sys.exit(main())

