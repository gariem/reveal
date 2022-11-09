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
        .map { row ->
            return tuple(row.entry_type, row.optional_label, file(row.value))
         }
        .set { reveal }

    emit:
    reveal                                     // channel: [ entry_type, optional_label, file(path) ]
    versions = SAMPLESHEET_CHECK.out.versions // channel: [ versions.yml ]
}
