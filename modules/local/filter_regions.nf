process FILTER_BAM_REGIONS {

    tag "$samplesheet"

    conda (params.enable_conda ? "conda-forge::python=3.8.3" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://github.com/gariem/singularity-reveal/releases/download/22.11.14/gariem-singularity-reveal.latest.sif' :
        'docker.io/raphsoft/reveal:1.0' }"

    input:
    tuple val(label), file(bam_file)
    file regions

    output:
    tuple val(label), file('*.filtered.bam'), emit: filtered_bam
    path "versions.yml", emit: versions

    script:
    final_name = bam_file.name.replace(".bam", ".filtered.bam")

    """
    samtools view -b -L $regions $bam_file > $final_name

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        samtools: \$(samtools --version | sed 's/samtools //g' | head -1)
    END_VERSIONS
    """
}

process FILTER_VCF_REGIONS {

    tag "$samplesheet"

    conda (params.enable_conda ? "conda-forge::python=3.8.3" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://github.com/gariem/singularity-reveal/releases/download/22.11.14/gariem-singularity-reveal.latest.sif' :
        'docker.io/raphsoft/reveal:1.0' }"

    input:
    tuple val(label), file(vcf_file)
    file regions

    output:
    tuple val(label), file('*.filtered.vcf'), emit: filtered_vcf
    path "versions.yml", emit: versions

    script:
    final_name = vcf_file.name.replace(".vcf", ".filtered.vcf")

    """
    bedtools intersect -a $vcf_file -b $regions -header > $final_name

    # Get first variant from VCF if filtered file doesn't contain variants
    if [ -s \$(bcftools view -H $final_name) ]; then
        head -n \$((\$(bcftools view -h $final_name | wc -l) + 1)) $vcf_file > $final_name
    fi

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        bedtools: \$(bedtools --version | sed 's/bedtools //g')
    END_VERSIONS
    """
}
