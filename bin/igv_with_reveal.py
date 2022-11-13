#!/usr/bin/env python

import argparse
import logging
from pathlib import Path
import sys

logger = logging.getLogger()


class Track:
    def __init__(self, label, path):
        self._label = label
        self._path = path

    @property
    def label(self):
        return self._label

    @property
    def path(self):
        return self._path


class IGVSessionBuilder:
    def __init__(self, local_reference_name, local_tracks_with_labels):
        self.reference = local_reference_name
        self.tracks_with_labels = local_tracks_with_labels
        self.tracks = []

    def _check_tracks(self):
        for track_with_label in self.tracks_with_labels:
            label, path = track_with_label.split(":")
            self.tracks.append(Track(label, path))

    def build(self):
        self._check_tracks()
        xml_data = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
        xml_data += f'<Session genome="{self.reference}" hasGeneTrack="false" hasSequenceTrack="true" version="8">\n'
        xml_data += '\t<Resources>\n'
        for track in self.tracks:
            xml_data += f'\t\t<Resource path="{track.path}"/>\n'
        xml_data += '\t</Resources>\n'
        xml_data += '</Session>\n'

        print(xml_data)


class SnapshotsCommandBuilder:
    def __init__(self, bed_file, slops):
        self.regions = bed_file
        self.slops = slops

    def build(self):
        return f"(regions={self.regions }, slops={self.slops})"


def parse_args(argv=None):
    """Define and immediately parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate and transform samplesheet. Output files to same directory",
        epilog="Example: python input_parser.py samplesheet.yaml",
    )

    parser.add_argument(
        "-l",
        "--log-level",
        help="The desired log level (default WARNING).",
        choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
        default="WARNING",
    )

    subparsers = parser.add_subparsers(help='Command to execute', dest='command')

    session_parser = subparsers.add_parser("build-session")
    batch_parser = subparsers.add_parser("build-batch")

    session_parser.add_argument(
        "--reference",
        type=str,
        help="Reference file"
    )

    session_parser.add_argument(
        "--tracks_with_labels",
        nargs='+',
        help="Track files, comma separated"
    )

    batch_parser.add_argument(
        "--regions",
        type=str,
        help="Regions file (bed-3)"
    )

    batch_parser.add_argument(
        "--slops",
        type=int,
        nargs='+',
        help="Slops"
    )

    return parser.parse_args(argv)


def main(argv=None):
    """Coordinate argument parsing and program execution."""
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level, format="[%(levelname)s] %(message)s")

    if args.command == "build-session":
        IGVSessionBuilder(args.reference, args.tracks_with_labels).build()

    if args.command == "build-batch":
        SnapshotsCommandBuilder(args.regions, args.slops).build()


if __name__ == "__main__":
    sys.exit(main())
