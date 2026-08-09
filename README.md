## Session 3 Recap — The Six Defects, Wrong vs. Corrected

We're reviewing every defect from last session before moving into today's topic. For each one: what was wrong, why it mattered, and the corrected code.

---

### Defect 1 — A shell script that does not parse

**Where:** `setup.sh`

📝 *The opening quote on the first `echo` is never closed. Bash keeps reading everything after it as one giant string until it hits end-of-file — that's why `bash -n setup.sh` reports a syntax error instead of the script actually running.*

❌ **Wrong:**
```bash
#!/bin/bash
echo "Setting up training environment...
mkdir -p results
echo "Ready!"
```

✅ **Corrected:**
```bash
cat > setup.sh << 'EOF'
#!/bin/bash
echo "Setting up training environment..."
mkdir -p results
echo "Ready!"
EOF
```

---

### Defect 2 — A package installed at runtime

**Where:** `modules/json_validation.nf`, `bin/json_validation.py`

📝 *`pip install jsonschema` runs fresh on every single execution. If PyPI is down, or the library releases a breaking change overnight, your "same" pipeline silently behaves differently. The fix: use only Python's standard library, and read the contract from `docs/schema.json` directly instead of depending on an external package to interpret it.*

❌ **Wrong (`modules/json_validation.nf`):**
```groovy
script:
"""
pip install --quiet jsonschema
json_validation.py ${triage_jsonl} ${schema} ${meta.id}.valid.jsonl ${meta.id}.quarantine.jsonl
...
"""
```

✅ **Corrected (`modules/json_validation.nf`):**
```bash
cat > modules/json_validation.nf << 'EOF'
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
EOF
```

✅ **Corrected (`bin/json_validation.py`) — standard library only, no `jsonschema` package:**
```bash
cat > bin/json_validation.py << 'EOF'
#!/usr/bin/env python3
"""
json_validation.py
~~~~~~~~~~~~~~~~~~~
Validates each TRIAGE JSON record against docs/schema.json, using only the Python
standard library — no runtime package install required.

Valid records pass through. Invalid ones (missing/extra fields, wrong types, out-of-range
values) are quarantined with the specific reason they failed. Syntactically malformed JSON
lines are also quarantined rather than crashing the task.
"""
import sys
import json

TYPE_MAP = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "array": list,
    "object": dict,
    "boolean": bool,
}


def load_schema(schema_path):
    with open(schema_path) as f:
        return json.load(f)


def validate_record(record, schema):
    if not isinstance(record, dict):
        return "record is not a JSON object"

    properties = schema.get("properties", {})
    required = schema.get("required", [])

    if schema.get("additionalProperties") is False:
        extra = set(record.keys()) - set(properties.keys())
        if extra:
            return f"unexpected field(s): {sorted(extra)}"

    for field in required:
        if field not in record:
            return f"missing required field: {field}"

    for field, value in record.items():
        field_schema = properties.get(field)
        if field_schema is None:
            continue

        expected_type = TYPE_MAP.get(field_schema.get("type"))
        if expected_type and not isinstance(value, expected_type):
            return f"field '{field}' has wrong type"

        if "minimum" in field_schema and value < field_schema["minimum"]:
            return f"field '{field}' below minimum"
        if "maximum" in field_schema and value > field_schema["maximum"]:
            return f"field '{field}' above maximum"

        if field_schema.get("type") == "array":
            item_type = TYPE_MAP.get(field_schema.get("items", {}).get("type"))
            if item_type and not all(isinstance(v, item_type) for v in value):
                return f"field '{field}' has an item of the wrong type"

    return None


def main(jsonl_path, schema_path, valid_out, quarantine_out):
    schema = load_schema(schema_path)

    n_valid = 0
    n_quarantined = 0

    with open(jsonl_path) as infile, \
         open(valid_out, "w") as valid_f, \
         open(quarantine_out, "w") as quarantine_f:

        for line in infile:
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                quarantine_f.write(json.dumps({
                    "original_record": line,
                    "validation_error": f"malformed JSON: {e.msg}",
                    "failed_field": None,
                }) + "\n")
                n_quarantined += 1
                continue

            error = validate_record(record, schema)
            if error is None:
                valid_f.write(json.dumps(record) + "\n")
                n_valid += 1
            else:
                quarantine_f.write(json.dumps({
                    "original_record": record,
                    "validation_error": error,
                    "failed_field": None,
                }) + "\n")
                n_quarantined += 1

    print(f"Validation complete: {n_valid} valid, {n_quarantined} quarantined")


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("Usage: json_validation.py <input.jsonl> <schema.json> <valid_out.jsonl> <quarantine_out.jsonl>")
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
EOF
```

---

### Defect 3 — A container using a rolling tag

**Where:** `modules/audit_bundle.nf`

📝 *`python:latest` isn't a fixed version — it silently points to whatever the newest build is on any given day. The fix is pinning to an exact, immutable digest instead of a tag. A digest is unique to your machine/moment, so we'll fetch the real one live in class rather than copy-paste a fake one.*

❌ **Wrong:**
```groovy
container 'python:latest'
```

✅ **Corrected approach — run this live to get the real digest:**
```bash
docker pull python:3.11-slim
docker inspect --format='{{index .RepoDigests 0}}' python:3.11-slim
```

This prints something like `python@sha256:abc123...`. Use that exact string:

```groovy
container 'python@sha256:<the digest you just fetched>'
```

---

### Defect 4 — A timestamp inside the compared output

**Where:** `bin/triage.py`

📝 *Every line of output got the same timestamp stamped in — but that timestamp is different every single run, so two runs of identical input never produce byte-identical output. This is today's live demo defect — see the nf-test section below.*

❌ **Wrong:**
```python
record = {
    "variant_id": variant_id,
    "priority_score": score,
    "rules_triggered": rules,
    "rule_version": RULE_VERSION,
    "timestamp": timestamp,
}
```

✅ **Corrected — full file:**
```bash
cat > bin/triage.py << 'EOF'
#!/usr/bin/env python3
"""
triage.py
~~~~~~~~~
Rule-based, deterministic variant triage. No AI model calls, CPU-only.
Reads a VCF, applies simple scoring rules per variant, writes one JSON object per variant (matching docs/schema.json) as JSON Lines.

Per-record output intentionally carries no timestamp: run-level timing lives once, in the
audit bundle. A field that varies between two otherwise-identical runs breaks the
byte-identical determinism this pattern is built to prove.
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
    """Deterministic rule-based scoring. Returns (score, rules_triggered)."""
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
            out.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: triage.py <input.vcf[.gz]> <output.jsonl>")
    main(sys.argv[1], sys.argv[2])
EOF
```

---

### Defect 5 — A provenance field entered manually

**Where:** `main.nf`, `subworkflow/glassbox_triage.nf`, `modules/audit_bundle.nf`

📝 *`params.sarek_version = "sarek-3.9.0"` is a string a human typed once. Nothing checks it's still true. The fix replaces it with `workflow.commitId` and `workflow.revision` — values Nextflow reads from its own execution state, which nobody can mistype because nobody types them.*

❌ **Wrong (`main.nf` — relevant line):**
```groovy
params.sarek_version = "sarek-3.9.0"
...
GLASSBOX_TRIAGE(ch_vcf, ch_schema, params.sarek_version)
```

✅ **Corrected — full `main.nf`:**
```bash
cat > main.nf << 'EOF'
#!/usr/bin/env nextflow
nextflow.enable.dsl = 2
include { GLASSBOX_TRIAGE } from './subworkflow/glassbox_triage.nf'
params.input         = "${projectDir}/tests/sample.vcf"
params.schema        = "${projectDir}/docs/schema.json"
workflow {
    ch_vcf = Channel
        .fromPath(params.input, checkIfExists: true)
        .map { vcf -> [ [id: 'sample'], vcf ] }
    ch_schema = Channel.fromPath(params.schema, checkIfExists: true)
    GLASSBOX_TRIAGE(ch_vcf, ch_schema)
    GLASSBOX_TRIAGE.out.audit_bundle.view { meta, bundle ->
        "Audit bundle for ${meta.id}: ${bundle}"
    }
}
EOF
```

✅ **Corrected — full `subworkflow/glassbox_triage.nf`:**
```bash
cat > subworkflow/glassbox_triage.nf << 'EOF'
include { TRIAGE }          from '../modules/triage.nf'
include { JSON_VALIDATION } from '../modules/json_validation.nf'
include { AUDIT_BUNDLE }    from '../modules/audit_bundle.nf'

workflow GLASSBOX_TRIAGE {

    take:
    ch_vcf          // channel: [ val(meta), path(vcf) ]
    ch_schema       // path: docs/schema.json

    main:
    ch_versions = Channel.empty()

    TRIAGE(ch_vcf)
    ch_versions = ch_versions.mix(TRIAGE.out.versions)

    JSON_VALIDATION(TRIAGE.out.triage_jsonl, ch_schema)
    ch_versions = ch_versions.mix(JSON_VALIDATION.out.versions)

    ch_for_audit = ch_vcf
        .join(JSON_VALIDATION.out.valid_jsonl)
        .join(JSON_VALIDATION.out.quarantine_jsonl)

    // Defect #5 fixed: workflow.commitId / workflow.revision / workflow.manifest.version
    // are read directly inside audit_bundle.nf's script block — no hand-typed
    // sarek_version parameter is passed in or needed here anymore.
    AUDIT_BUNDLE(
        ch_for_audit,
        TRIAGE.out.triage_jsonl.map { meta, jsonl -> "v1.0.0" }.first()
    )
    ch_versions = ch_versions.mix(AUDIT_BUNDLE.out.versions)

    emit:
    valid_jsonl      = JSON_VALIDATION.out.valid_jsonl
    quarantine_jsonl = JSON_VALIDATION.out.quarantine_jsonl
    audit_bundle     = AUDIT_BUNDLE.out.audit_bundle
    versions         = ch_versions
}
EOF
```

✅ **Corrected — full `modules/audit_bundle.nf`:**
```bash
cat > modules/audit_bundle.nf << 'EOF'
process AUDIT_BUNDLE {
    tag "$meta.id"
    label 'process_single'
    // DEFECT #3 still lives here separately — "latest" is a rolling tag.
    // Fixed independently above; not touched by this Defect #5 fix.
    container 'python:latest'

    input:
    tuple val(meta), path(vcf), path(valid_jsonl), path(quarantine_jsonl)
    val rule_version

    output:
    tuple val(meta), path("${meta.id}.audit_bundle.json"), emit: audit_bundle
    path "versions.yml",                                    emit: versions

    script:
    """
    audit_bundle.py ${vcf} ${valid_jsonl} ${quarantine_jsonl} ${rule_version} \\
        "${workflow.commitId}" "${workflow.revision}" "${workflow.manifest.version}" \\
        ${meta.id}.audit_bundle.json

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        python: \$(python3 --version | sed 's/Python //')
    END_VERSIONS
    """
}
EOF
```

✅ **Corrected — full `bin/audit_bundle.py`** (now takes captured Git values instead of a typed string):
```bash
cat > bin/audit_bundle.py << 'EOF'
#!/usr/bin/env python3
"""
audit_bundle.py
~~~~~~~~~~~~~~~
Creates one audit "receipt" record per run, capturing everything needed to trace back exactly what produced a given triage result: input hash,
rule version, workflow provenance, and validation outcome counts.

All provenance fields are either calculated from a committed artefact (the input file hash) or read from Nextflow's own runtime (commit,
revision, release version) — none are supplied as a typed argument that a person could enter incorrectly.
"""
import sys
import json
import hashlib
from datetime import datetime, timezone


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
         workflow_commit, workflow_revision, release_version, out_path):
    timestamp = datetime.now(timezone.utc).isoformat()

    n_valid = count_lines(valid_jsonl)
    n_quarantined = count_lines(quarantine_jsonl)

    if n_valid == 0:
        validation_status = "FAIL"
    elif n_quarantined == 0:
        validation_status = "PASS"
    else:
        validation_status = "PARTIAL_QUARANTINE"

    bundle = {
        "run_timestamp": timestamp,
        "input_vcf": input_vcf,
        "input_vcf_sha256": sha256_of_file(input_vcf),
        "rule_version": rule_version,
        "workflow_commit": workflow_commit,
        "workflow_revision": workflow_revision,
        "release_version": release_version,
        "n_valid": n_valid,
        "n_quarantined": n_quarantined,
        "validation_status": validation_status,
    }

    with open(out_path, "w") as out:
        out.write(json.dumps(bundle, indent=2))

    print(f"Audit bundle written to {out_path}")
    print(json.dumps(bundle, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 9:
        sys.exit(
            "Usage: audit_bundle.py <input.vcf> <valid.jsonl> <quarantine.jsonl> "
            "<rule_version> <workflow_commit> <workflow_revision> "
            "<release_version> <out.json>"
        )
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4],
         sys.argv[5], sys.argv[6], sys.argv[7], sys.argv[8])
EOF
```

---

### Defect 6 — No controlled release evidence (no CI, no tagged version)

**Where:** the repository itself — check the Releases page and Actions tab

📝 *No tag means there's no fixed, citable version to point to. No CI means nothing automatically re-checks the pipeline still works. This is exactly what today's session fixes — see below.*

✅ **Corrected — create a tagged release:**
```bash
git tag v0.1.0
git push origin v0.1.0
```

✅ **Corrected — CI workflow:** see the full Session 4 section below.

---

## Session 4 — From Audit to Automation: nf-test & CI/CD

Last session, finding these six defects meant reading code by hand. Today, we teach a robot to find at least one of them automatically, forever, on every single change — no human needs to remember to check.

### What is nf-test?

Think of it like a teacher who grades your homework against an answer key. You tell it: "run this, and remember exactly what comes out." Every time the code changes, it re-checks: does the output still match? If yes — green. If no — red, and it shows you exactly what's different.

### Step 1 — Run the test twice, watch it fail

```bash
nf-test test tests/modules/triage.nf.test
nf-test test tests/modules/triage.nf.test
```

The second run should fail with a snapshot mismatch — same input, same code, different output. That's Defect #4, caught automatically instead of by a human reading code.

### Step 2 — Apply the Defect #4 fix

Use the corrected `bin/triage.py` from the Defect 4 section above.

### Step 3 — Reset the snapshot and confirm it now stays green

```bash
rm -rf tests/modules/__snapshot__
nf-test test tests/modules/triage.nf.test
nf-test test tests/modules/triage.nf.test
```

First run creates a fresh baseline. Second run should now show `PASSED` — same input, same code, finally the same output every time.

### Step 4 — Add CI so this check runs automatically on every push

```bash
mkdir -p .github/workflows
cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Check out the repository
        uses: actions/checkout@v4

      - name: Install Nextflow
        uses: nf-core/setup-nextflow@v2

      - name: Install nf-test
        uses: nf-core/setup-nf-test@v1

      - name: Run nf-test suite
        run: nf-test test tests/modules/triage.nf.test
EOF
```

Commit and push — GitHub now runs this test on every push, automatically, whether anyone remembers to or not:

```bash
git add .github/workflows/ci.yml tests/modules/__snapshot__
git commit -m "Add nf-test CI workflow"
git push
```

Check the **Actions** tab on GitHub — a green ✅ or red ❌ should now appear directly on your commit.

### Today's exercise

Working in your own fork:
1. Confirm the test fails against the still-broken `main` (run twice, see red)
2. Apply the Defect #4 fix, reset the snapshot, confirm green
3. Add the CI workflow, push, and confirm the Actions tab shows a passing check

We'll compare everyone's Actions tab together at the end of the session.
