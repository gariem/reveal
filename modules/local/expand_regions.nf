process EXPAND_REGIONS {

    tag "$samplesheet"

    conda (params.enable_conda ? "conda-forge::python=3.8.3" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://github.com/gariem/singularity-reveal/releases/download/22.11.14/gariem-singularity-reveal.latest.sif' :
        'docker.io/raphsoft/reveal:1.0' }"

    input:
    file regions
    file slops

    output:
    path "expanded_regions.bed", emit: expanded_regions
    path "versions.yml", emit: versions

    script:
    """
    max_slop="\$(cat $slops | sort -rn | head -1)"
    awk -v window=\$max_slop -F"\\t" 'BEGIN {OFS=FS}{print \$1,\$2-window,\$3+window}' $regions  | bedtools sort | bedtools merge > expanded_regions.bed

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        bedtools: \$(bedtools --version | sed 's/bedtools //g')
    END_VERSIONS
    """
}
