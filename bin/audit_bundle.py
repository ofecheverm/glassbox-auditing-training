#!/usr/bin/env python3
"""
audit_bundle.py
~~~~~~~~~~~~~~~
Creates one audit "receipt" record per run, capturing everything needed to trace back exactly what produced a given triage result: input hash,
rule version, workflow provenance, and validation outcome counts.

The input file hash is calculated from a committed artefact and cannot be typed wrong.

# DEFECT: sarek_version below is a typed argument a person entered by hand — nothing verifies
# it's actually true. Compare this to input_vcf_sha256, which is calculated, not typed.
"""
import sys
import json
import hashlib


def sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def count_lines(path):
    with open(path) as f:
        return sum(1 for _ in f)


def main(input_vcf, valid_jsonl, quarantine_jsonl, rule_version,
         sarek_version, out_path):

    n_valid = count_lines(valid_jsonl)
    n_quarantined = count_lines(quarantine_jsonl)

    if n_valid == 0:
        validation_status = "FAIL"
    elif n_quarantined == 0:
        validation_status = "PASS"
    else:
        validation_status = "PARTIAL_QUARANTINE"

    bundle = {
        "input_vcf": input_vcf,
        "input_vcf_sha256": sha256_of_file(input_vcf),
        "rule_version": rule_version,
        "sarek_version": sarek_version,
        "sarek_version_source":"manual_argument_not_verified",
        "n_valid": n_valid,
        "n_quarantined": n_quarantined,
        "validation_status": validation_status,
    }

    with open(out_path, "w") as out:
        out.write(json.dumps(bundle, indent=2))

    print(f"Audit bundle written to {out_path}")
    print(json.dumps(bundle, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 7:
        sys.exit(
            "Usage: audit_bundle.py <input.vcf> <valid.jsonl> <quarantine.jsonl> "
            "<rule_version> <sarek_version> <out.json>"
        )
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4],
         sys.argv[5], sys.argv[6])
