#!/usr/bin/env python3
"""
triage.py — TRAINING VERSION (contains a seeded defect for S03)
Rule-based, deterministic variant triage. No AI model calls, CPU-only.
"""
import sys
import json
import gzip

RULE_VERSION = "v1.0.0"


def open_vcf(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt")
    return open(path, "r")


def score_variant(chrom, pos, ref, alt, qual, filt, info):
    score = 0
    rules = []
    if filt == "PASS":
        score += 3
        rules.append("passed_filter")
    try:
        if qual != "." and float(qual) >= 30:
            score += 2
            rules.append("high_quality_call")
    except ValueError:
        pass
    if len(ref) != len(alt):
        score += 3
        rules.append("indel_variant")
    for field in info.split(";"):
        if field.startswith("DP="):
            try:
                dp = int(field.split("=")[1])
                if dp >= 10:
                    score += 2
                    rules.append("adequate_depth")
            except (ValueError, IndexError):
                pass
    score = min(score, 10)
    return score, rules


def main(vcf_path, out_path):
    # DEFECT: timestamp captured once but written into EVERY record —
    # compare two separate runs and every record differs, even if
    # nothing else changed.
    with open_vcf(vcf_path) as vcf, open(out_path, "w") as out:
        for line in vcf:
            if line.startswith("#"):
                continue
            fields = line.rstrip("\n").split("\t")
            if len(fields) < 8:
                continue
            chrom, pos, _id, ref, alt, qual, filt, info = fields[:8]
            variant_id = f"{chrom}_{pos}_{ref}_{alt}"
            score, rules = score_variant(chrom, pos, ref, alt, qual, filt, info)
            record = {
                "variant_id": variant_id,
                "priority_score": score,
                "rules_triggered": rules,
                "rule_version": RULE_VERSION,
                }
            out.write(json.dumps(record, sort_keys=True) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: triage.py <input.vcf[.gz]> <output.jsonl>")
    main(sys.argv[1], sys.argv[2])
