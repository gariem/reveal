process GENERATE_IGV_FILES {

    tag "$samplesheet"

    conda (params.enable_conda ? "conda-forge::python=3.8.3" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://github.com/gariem/singularity-reveal/releases/download/22.11.14/gariem-singularity-reveal.latest.sif' :
        'docker.io/raphsoft/reveal:1.0' }"

    input:
    val tracks_with_labels // String: [label1:path1, label2:path2]
    path bed_regions
    path slops

    output:
    path 'igv.session.xml'    , emit: session
    path 'batch.txt'    , emit: batch
    path "versions.yml" , emit: versions

    script: // This script is bundled with the pipeline, in nf-core/reveal/bin/
    tracks_param=tracks_with_labels.toString().replace("[", "").replace("]", "").replace("," ,"")
    """
    igv_with_reveal.py build-session --reference=${file(params.fasta).name} \
        --tracks_with_labels $tracks_param > igv.session.xml

    igv_with_reveal.py build-batch --regions=$bed_regions --slops \$(cat $slops | xargs) \
        --snapshots_dir=captures > batch.txt

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """
}

process IGV_SNAPSHOTS {

    tag "$samplesheet"

    conda (params.enable_conda ? "conda-forge::python=3.8.3" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://github.com/gariem/singularity-reveal/releases/download/22.11.14/gariem-singularity-reveal.latest.sif' :
        'docker.io/raphsoft/reveal:1.0' }"

    stageInMode 'copy'

    input:
    file reference
    file tracks
    file igv_session
    file igv_batch
    file igv_preferences


    output:
    path "captures/*.png", emit: captures
    path "versions.yml" , emit: versions

    script:
    """
    echo "load $igv_session" > snapshots.txt
    cat $igv_batch >> snapshots.txt
    echo "exit" >> snapshots.txt

    ls *.bam | xargs -n1 -P5 samtools index

    xvfb-run --auto-servernum -s "-screen 0 1920x1080x24" java -Xmx32000m \
        --module-path=/IGV_Linux_2.12.2/lib \
        --module=org.igv/org.broad.igv.ui.Main -b snapshots.txt -o $igv_preferences

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python --version | sed 's/Python //g')
    END_VERSIONS
    """

}
