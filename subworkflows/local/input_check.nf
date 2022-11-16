//
// Check input samplesheet and get read channels
//

include { SAMPLESHEET_CHECK } from '../../modules/local/samplesheet_check'

workflow INPUT_CHECK {
    take:
    samplesheet // file: /path/to/samplesheet.yaml

    main:
    SAMPLESHEET_CHECK ( samplesheet )
        .csv
        .splitCsv ( header:true, sep:',' )
        .map { row -> create_meta_channel(row) }
        .collect()
        .map { create_final_channel(it) }
        .set { reveal }

    emit:
    reveal                                      // channel:  [reference:val, regions:val, slops:val, preferences:val, tracks:[label:val, file:val]]
    versions = SAMPLESHEET_CHECK.out.versions   // channel: [ versions.yml ]
}

def create_meta_channel(LinkedHashMap row) {
    def meta = [:]
    meta.type = row.type
    if ( meta.type == "track" || meta.type == "region" ) {
        meta.label = row.label
    }
    meta.value = file(row.value)
    return meta
}

def create_final_channel(collected_entries){
    def meta = [:]
    def tracks = []
    def regions = []
    for (entry in collected_entries){
        switch(entry.type){
            case "reference": meta.reference = entry.value
                break;
            case "region":
                regions.add([prefix: entry.label, file: entry.value])
                break;
            case "slops": meta.slops = entry.value
                break;
            case "preferences": meta.preferences = entry.value
                break;
            case "track":
                tracks.add([label: entry.label, file: entry.value])
                break;
        }
    }
    meta.tracks = tracks
    meta.regions = regions
    return meta
}
