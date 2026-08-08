process JSON_VALIDATION {
    tag "$meta.id"
    label 'process_single'
    container 'python:3.11-slim'

    input:
    tuple val(meta), path(triage_jsonl)
    path schema

    output:
    tuple val(meta), path("${meta.id}.valid.jsonl"),      emit: valid_jsonl
    tuple val(meta), path("${meta.id}.quarantine.jsonl"), emit: quarantine_jsonl
    path "versions.yml",                                   emit: versions

    script:
    """
    json_validation.py ${triage_jsonl} ${schema} ${meta.id}.valid.jsonl ${meta.id}.quarantine.jsonl

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python3 --version | sed 's/Python //')
    END_VERSIONS
    """
}
