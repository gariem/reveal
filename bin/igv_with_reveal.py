#!/usr/bin/env python

import argparse
import logging
import sys
import csv

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
        xml_data = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' \
                   f'<Session genome="{self.reference}" hasGeneTrack="false" hasSequenceTrack="true" version="8">\n' \
                   '\t<Resources>\n'
        for track in self.tracks:
            xml_data += f'\t\t<Resource path="{track.path}"/>\n'
        xml_data += '\t</Resources>\n'

        panel_num = 1
        panel_factors = [0]

        bam_factor = 20
        vcf_factor = 4
        contigs_factor = 6
        sequence_factor = 2
        other_factor = 5

        xml_data += f'\t<Panel name="Panel_{panel_num}">\n'
        xml_data += f'\t\t<Track attributeKey="Reference sequence" clazz="org.broad.igv.track.SequenceTrack" ' \
                    f'fontSize="10" id="Reference sequence" name="Reference sequence" sequenceTranslationStrandValue="POSITIVE" ' \
                    f'shouldShowTranslation="true" visible="true"/>\n'
        factor = sequence_factor
        for track in self.tracks:
            if track.path.endswith(".vcf"):
                xml_data += f'\t\t<Track attributeKey="{track.label}" clazz="org.broad.igv.variant.VariantTrack" colorScale="ContinuousColorScale;0.0;0.0;255,255,255;0,0,178" ' \
                            f'displayMode="EXPANDED" fontSize="10" groupByStrand="false" id="{track.path}" name="{track.label}" ' \
                            f'siteColorMode="ALLELE_FREQUENCY" squishedHeight="1" visible="true"/>\n'

                panel_num += 1
                factor += vcf_factor
        panel_factors.append(panel_factors[-1] + factor)

        xml_data += f'\t</Panel>\n'

        for track in self.tracks:
            if track.path.endswith(".bam"):
                xml_data += f'\t<Panel name="Panel_{panel_num}">\n' \
                            f'\t\t<Track attributeKey="{track.label} Coverage" autoScale="true" clazz="org.broad.igv.sam.CoverageTrack" color="175,175,175" ' \
                            f'colorScale="ContinuousColorScale;0.0;60.0;255,255,255;175,175,175" fontSize="10" id="{track.path}_coverage" name="{track.label} Coverage" ' \
                            f'snpThreshold="0.2" visible="true">\n' \
                            f'\t\t\t<DataRange baseline="0.0" drawBaseline="true" flipAxis="false" maximum="13.0" minimum="0.0" type="LINEAR"/>\n' \
                            f'\t\t</Track>\n' \
                            f'\t\t<Track attributeKey="{track.label}" clazz="org.broad.igv.sam.AlignmentTrack" displayMode="COLLAPSED" ' \
                            f'experimentType="THIRD_GEN" fontSize="10" id="{track.path}" name="{track.label}" visible="true">\n' \
                            f'\t\t\t<RenderOptions/>\n' \
                            f'\t\t</Track>\n' \
                            f'\t</Panel>\n'
                panel_num += 1
                if "contigs" in track.label.lower():
                    panel_factors.append(panel_factors[-1] + contigs_factor)
                else:
                    panel_factors.append(panel_factors[-1] + bam_factor)

        xml_data += f'\t<Panel name="Panel_{panel_num}">\n'

        factor = 0
        for track in self.tracks:
            if not track.path.endswith(".bam") and not track.path.endswith(".vcf"):
                xml_data += f'\t\t<Track attributeKey="{track.label}" clazz="org.broad.igv.track.FeatureTrack" colorScale="ContinuousColorScale;0.0;0.0;255,255,255;0,0,178" ' \
                            f'fontSize="10" groupByStrand="false" id="{track.path}" name="{track.label}" visible="true"/>\n'
                panel_num += 1
                factor += other_factor
        panel_factors.append(panel_factors[-1] + factor)

        factors_values = ','.join([str(factor / panel_factors[-1]) for factor in panel_factors])
        xml_data += f'\t</Panel>\n' \
                    f'<PanelLayout dividerFractions="{factors_values}"/>\n' \
                    f'</Session>\n'

        print(xml_data)


class SnapshotsCommandBuilder:
    def __init__(self, bed_file, slops, out_dir):
        self.regions = bed_file
        self.slops = slops
        self.out_dir = out_dir

    def build(self):
        batch_command = f'snapshotDirectory {self.out_dir}\n'

        with open(self.regions, 'r') as regions_file:
            for region in csv.reader(regions_file, delimiter='\t'):
                for value in self.slops:
                    batch_command += f'goto {region[0]}:{int(region[1])-value}-{int(region[2])+value}\n' \
                                     f'snapshot {region[0]}_{region[1]}_{region[2]}_slop{value}.png\n'

        print(batch_command)


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

    batch_parser.add_argument(
        "--snapshots_dir",
        type=str,
        help="Output directory for snapshots"
    )

    return parser.parse_args(argv)


def main(argv=None):
    """Coordinate argument parsing and program execution."""
    args = parse_args(argv)
    logging.basicConfig(level=args.log_level, format="[%(levelname)s] %(message)s")

    if args.command == "build-session":
        IGVSessionBuilder(args.reference, args.tracks_with_labels).build()

    if args.command == "build-batch":
        SnapshotsCommandBuilder(args.regions, args.slops, args.snapshots_dir).build()


if __name__ == "__main__":
    sys.exit(main())
