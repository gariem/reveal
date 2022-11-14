process SAMPLESHEET_CHECK {

    tag "$samplesheet"

    conda (params.enable_conda ? "conda-forge::python=3.8.3" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://github.com/gariem/singularity-reveal/releases/download/22.11.14/gariem-singularity-reveal.latest.sif' :
        'docker.io/raphsoft/reveal:1.0' }"

    input:
    path samplesheet

    output:
    path '*.csv'       , emit: csv
    path "versions.yml", emit: versions

    script: // This script is bundled with the pipeline, in nf-core/reveal/bin/
    """
    input_parser.py --file_in=$samplesheet --reference=${params.fasta}

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}
