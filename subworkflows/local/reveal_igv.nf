include { GENERATE_IGV_FILES } from '../../modules/nf-core/modules/igv/reveal/main'
include { IGV_SNAPSHOTS } from '../../modules/nf-core/modules/igv/reveal/main'

workflow PREPARE_IGV_FILES {

    take:
    tracks // tuple: (label, file)
    regions // tuple(prefix, file)
    slops // file: /path/to/slops.txt

    main:
    tracks.map{ entry ->
        return entry[0] + ":" + entry[1].name
    }
    .collect()
    .set { local_labeled_files }

    regions.map{ entry ->
        return entry[0] + ":" + entry[1].name
    }
    .collect()
    .set { local_prefixed_regions }

    regions.map{ entry ->
        return entry[1]
    }
    .collect()
    .set { all_region_files }

    GENERATE_IGV_FILES (
        local_labeled_files,
        local_prefixed_regions,
        all_region_files,
        slops
    )

    emit:
    session = GENERATE_IGV_FILES.out.session
    batch = GENERATE_IGV_FILES.out.batch
    versions = GENERATE_IGV_FILES.out.versions  // channel: [ versions.yml ]

}

workflow SNAPSHOTS {

    take:
    tracks
    igv_session
    igv_batch
    igv_preferences

    main:

    tracks.map{ track ->
        return track[1]
    }
    .collect()
    .set {final_tracks}

    IGV_SNAPSHOTS (
        file(params.fasta),
        final_tracks,
        igv_session,
        igv_batch,
        igv_preferences
    )

    emit:
    snapshots = IGV_SNAPSHOTS.out.captures
    versions = IGV_SNAPSHOTS.out.versions
}
