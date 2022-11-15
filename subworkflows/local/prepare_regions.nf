include { EXPAND_REGIONS } from '../../modules/local/expand_regions'
include { FILTER_BAM_REGIONS } from '../../modules/local/filter_regions'
include { FILTER_VCF_REGIONS } from '../../modules/local/filter_regions'

workflow PREPARE_TRACKS {

    take:
    tracks // [[label: 'abc', file: file.(bam|vcf|bed)]]
    regions // [[prefix: 'abc', file: file.(bed)]]
    slops // file: /path/to/slops.txt

    main:
    tracks.flatMap { entries ->
        def labeled_tracks=[]
        for (entry in entries) {
            labeled_tracks.add(tuple(entry.label, entry.file))
        }
        return labeled_tracks
    }.branch {
        bam: it[1].name.endsWith('.bam')
        vcf: it[1].name.endsWith('.vcf')
        other: !it[1].name.endsWith('.bam') && !it[1].name.endsWith('.vcf')
    }.set { track_files }

    regions.map { entries ->
        def region_files=[]
        for (entry in entries) {
            region_files.add(entry.file)
        }
        return region_files
    }
    .set { region_files }

    EXPAND_REGIONS ( region_files, slops )
    .expanded_regions
    .set { expanded_regions }

    FILTER_BAM_REGIONS (track_files.bam, expanded_regions)
    .filtered_bam
    .set { filtered_bam }

    FILTER_VCF_REGIONS (track_files.vcf, expanded_regions)
    .filtered_vcf
    .set { filtered_vcf }

    regions.flatMap { entries ->
        def prefixed_regions=[]
        for (entry in entries) {
            prefixed_regions.add(tuple(entry.prefix, entry.file))
        }
        return prefixed_regions
    }.
    set {prefixed_regions}

    emit:
    tracks = filtered_vcf.concat(filtered_bam).concat(track_files.other)   // channel:  [alignment.filtered.(bam|vcf|bed)]
    prefixed_regions = prefixed_regions
    versions = EXPAND_REGIONS.out.versions.concat(FILTER_BAM_REGIONS.out.versions).concat(FILTER_VCF_REGIONS.out.versions)   // channel: [ versions.yml ]

}
