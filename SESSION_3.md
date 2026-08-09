# glassbox-auditing-training

<div align="center">

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/STaiMIC/glassbox-auditing-training)
[![Nextflow](https://img.shields.io/badge/nextflow-DSL2-blue)](https://www.nextflow.io/)
[![Docker](https://img.shields.io/badge/container-Docker-2496ED)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Training Exercise](https://img.shields.io/badge/defects-6%20seeded-red)](docs/audit-checklist.md)

**A hands-on reproducibility & provenance audit practical for the STaiMIC Nextflow Training Program**
*Six deliberately seeded defects, one real Nextflow subworkflow, fifty minutes to find them all*

---

[Quick Start](#quick-start) · [The Scenario](#the-scenario) · [What Does This Pipeline Do?](#what-does-this-pipeline-actually-do) · [Repository Structure](#repository-structure)

</div>

---

## What is this?

This repository is the **hands-on practical component** of the STaiMIC Nextflow Bioinformatics Training Program (Session 3: *"Beyond 'It Ran Successfully': Auditing Your Own nf-core Pipeline"*). It's a deliberately imperfect training copy of the real [glassbox-ai-triage](https://github.com/STaiMIC/glassbox-ai-triage) pattern — a small Nextflow subworkflow that sits downstream of nf-core/sarek variant calling and produces an auditable "receipt" for every triage decision.

Learn how to:
- Recognize whether a shell script actually parses before you trust it
- Spot a package installed at runtime instead of baked into a container
- Catch a container pinned to a rolling tag instead of an immutable digest
- Find a timestamp hiding inside output that should otherwise be byte-for-byte reproducible
- Tell the difference between a provenance field that's *typed* and one that's *captured*
- Recognize when a repository has no tagged release and no CI to prove it was ever tested clean

Click **"Open in GitHub Codespaces"** above — Nextflow, Docker, and the container images this repo uses are pre-installed and pre-pulled automatically, so you land in a ready terminal. No local installation needed. No HPC required.

> ⚠️ **This repository is intentionally broken.** Six reproducibility/provenance defects have been seeded throughout the codebase on purpose — they're your audit targets tonight. Do not use this as a reference implementation. See [glassbox-ai-triage](https://github.com/STaiMIC/glassbox-ai-triage) for the corrected, real-world version this training copy is based on.
>
> **Do not run `bash setup.sh` directly as your first move** — check its syntax first:
> ```bash
> bash -n setup.sh
> ```
> This is a *syntax check only* — it reads the script without executing it, and it will immediately surface a real, honest error. That error is Defect #1, not a broken Codespace. Once you understand why it fails, you can decide whether to fix it and actually run it.

For full task instructions, see [Your Task](#your-task) below and **[docs/audit-checklist.md](docs/audit-checklist.md)**.

---

## The Scenario

The teaching narrative: you've inherited this subworkflow from a colleague. It "ran successfully" on their machine, and now it's your job to decide whether you'd trust its output enough to put your name on it.

| Question | What you're really asking |
|---|---|
| Which code? | Is there a tagged release or committed version — not just "whatever's on disk"? |
| Which container? | Is it pinned to an exact, immutable digest — not a rolling tag like `latest`? |
| Which input? | Is there a hash or fixed reference to the exact input file used? |
| Which version? | Is the rule/logic version emitted by the code itself — not typed in by a person? |

The real [glassbox-ai-triage](https://github.com/STaiMIC/glassbox-ai-triage) pipeline is built to answer all four automatically. Your job tonight is to find where **this** copy of it quietly fails to.

> ⚠️ **Don't expect this pipeline to run cleanly end-to-end.** Several of the seeded defects will cause odd behavior or outright failure — that's the point. Use `bash -n` on shell scripts before executing them, and read before you run.

---

## What Does This Pipeline Actually Do?

Before auditing *how trustworthy* something is, it helps to know *what it's for*. In plain terms:

After a real tool (`nf-core/sarek`) sequences a patient's DNA and finds thousands of tiny genetic differences called **variants**, this pipeline **triages** them — like a nurse doing hospital triage, deciding what needs attention now versus what can wait. Here, it's deciding which genetic variants look important enough for a human to review.

**Input** — `tests/sample.vcf`, three pretend variants:
```
chr1  12345  A→T   quality=45  PASS      depth=25
chr1  67890  G→GA  quality=12  PASS      depth=8
chr2  11111  C→T   quality=.   LowQual   depth=3
```

**Step 1 — `TRIAGE` scores each one** with simple, fixed rules (passed quality filtering? good sequencing depth? etc.) Real output from this exact test file:
```json
{"variant_id": "chr1_12345_A_T",  "priority_score": 7, "rules_triggered": ["passed_filter", "high_quality_call", "adequate_depth"]}
{"variant_id": "chr1_67890_G_GA", "priority_score": 6, "rules_triggered": ["passed_filter", "indel_variant"]}
{"variant_id": "chr2_11111_C_T",  "priority_score": 0, "rules_triggered": []}
```
Variant 1 passed every check — score 7/10, worth a closer look. Variant 3 failed quality filtering outright — score 0, probably safe to ignore.

**Step 2 — `JSON_VALIDATION` checks the output is well-formed** — anything malformed gets quarantined instead of silently passing through and causing problems later.

**Step 3 — `AUDIT_BUNDLE` writes the receipt.** A real one from this repo:
```json
{
  "input_vcf_sha256": "0690c3d815f0fad80779f4f5d02420483e6274432121fbe653f4c02d23e58f99",
  "rule_version": "v1.0.0",
  "sarek_version": "sarek-3.9.0",
  "n_valid": 3,
  "n_quarantined": 0,
  "validation_status": "PASS"
}
```
That long hash is a fingerprint of the exact input file — change one letter of the VCF and it looks completely different. That's a fact you can trust. Now look right next to it: `"sarek_version": "sarek-3.9.0"` — someone just typed that. Nothing checks whether it's true. **That contrast, sitting in one file, is the entire lesson of tonight's class in miniature.**

> 💡 **Important honesty note:** the "AI" in this pattern's name isn't real AI — it's simple, fixed, readable rules (if quality > 30, add points; if it's an indel, add points). No machine learning, no black box. That's intentional: you can't audit a black box the same way you can audit code you can read line by line.

---

## Pipeline Architecture

```
┌────────────────────────────────────────────────────────────────┐
│              GlassBox Auditing Training Subworkflow            │
│         Deliberately Imperfect Copy — Session 3 Practical      │
└────────────────────────────────────────────────────────────────┘

  VCF (tests/sample.vcf)
       │
       ▼
   ┌──────────┐
   │  TRIAGE  │  ──▶  Rule-based, deterministic variant scoring
   └──────────┘        Output: *.triage.jsonl
       │
       ▼
   ┌────────────────────┐
   │  JSON_VALIDATION    │  ──▶  Validates output against docs/schema.json
   └────────────────────┘        Output: *.valid.jsonl / *.quarantine.jsonl
       │
       ▼
   ┌───────────────┐
   │ AUDIT_BUNDLE  │  ──▶  Provenance receipt: input hash, rule version,
   └───────────────┘        workflow commit/revision, pass/fail status
       │
       ▼
   *.audit_bundle.json  ──▶  Your job: decide if you'd sign your name to it.
```

Every process is defined twice: once in `modules/*.nf` (the Nextflow process wrapper) and once in `bin/*.py` (the actual logic). The defects live in both layers — read both before you decide a process is clean.

---

## Quick Start

```bash
# 1. Does setup.sh even parse? (syntax check only — does not execute)
bash -n setup.sh

# 2. Read the three files most likely to be hiding issues
cat bin/triage.py
cat modules/json_validation.nf
cat modules/audit_bundle.nf

# 3. Try running the actual pipeline (optional — see scenario note above;
#    expect it to behave oddly or fail, that's part of the audit)
nextflow run main.nf -profile docker
```

Full checklist with the four questions and six things to check: **[docs/audit-checklist.md](docs/audit-checklist.md)**.

---

## Your Task

Work solo or in pairs (30 minutes):

1. Run `bash -n setup.sh` as a first check.
2. Read through `bin/triage.py`, `modules/json_validation.nf`, and `modules/audit_bundle.nf`.
3. Find as many of the **6 seeded defects** as you can.
4. For each one, explain *why* it breaks reproducibility or provenance, and how you'd fix it.

Use **[docs/audit-checklist.md](docs/audit-checklist.md)** to guide your review.

After 30 minutes, we'll compare findings as a group (20 minutes), then complete a reproducibility risk map and each fix one issue in your own repository or training fork before the next session.

---

## Repository Structure

```
glassbox-auditing-training/
│
├── README.md                    This file
├── setup.sh                     ← STUDENTS RUN THIS first
├── main.nf                      Entry point — runs the GLASSBOX_TRIAGE subworkflow
├── nextflow.config               Resource limits + Docker profile
├── LICENSE                       MIT
│
├── .devcontainer/
│   ├── devcontainer.json          Codespaces environment config
│   └── post-install.sh            Auto-setup: Nextflow + pre-pulled container images
│
├── bin/
│   ├── triage.py                 Rule-based, deterministic variant scoring
│   ├── json_validation.py        Schema validation logic
│   └── audit_bundle.py           Builds the provenance receipt
│
├── modules/
│   ├── triage.nf                  TRIAGE process definition
│   ├── json_validation.nf         JSON_VALIDATION process definition
│   └── audit_bundle.nf            AUDIT_BUNDLE process definition
│
├── subworkflow/
│   └── glassbox_triage.nf          Wires the three processes together
│
├── docs/
│   ├── audit-checklist.md          Your structured review guide — use this
│   ├── problem-and-methods.md       Background on the real GlassBox pattern
│   ├── literature-summary.md        Supporting references
│   └── schema.json                  JSON schema used by JSON_VALIDATION
│
└── tests/
    ├── sample.vcf                   Small synthetic 3-variant test input
    └── sample*.jsonl                 Example outputs for comparison
```

---

## Technical Configuration

| Parameter | Value | Reason |
|-----------|-------|--------|
| Nextflow DSL | DSL2 | Required for subworkflow-style module composition |
| Containers | `python:3.11-slim` (TRIAGE, JSON_VALIDATION) | Check `AUDIT_BUNDLE`'s container line yourself — is it pinned the same way? |
| Resource limit | 2 CPU / 6GB RAM / 20 min per process | Sized for Codespaces/local laptop; see `nextflow.config` |
| Test input | `tests/sample.vcf` | Small synthetic 3-variant VCF, safe to run repeatedly |
| License | MIT | See `LICENSE` |
| Based on | [glassbox-ai-triage v0.1.0](https://github.com/STaiMIC/glassbox-ai-triage) | The corrected, real-world pattern this training copy is deliberately broken from |

---

## References

| Topic | Reference |
|-------|-----------|
| **nf-core/sarek** | Garcia et al., F1000Research 2020, doi:10.12688/f1000research.16665.2 |
| **Nextflow** | Di Tommaso et al., Nat. Biotechnol. 2017, doi:10.1038/nbt.3820 |
| **nf-core** | Ewels et al., Nat. Biotechnol. 2020, doi:10.1038/s41587-020-0439-x |
| **Reproducibility in biomedical AI** | Han H., BMC Medical Genomics 2025, doi:10.1186/s12920-024-02072-6 |

---

## Questions?

See **[docs/audit-checklist.md](docs/audit-checklist.md)** for the structured review guide, or the real [glassbox-ai-triage](https://github.com/STaiMIC/glassbox-ai-triage) repository for the corrected reference implementation.

---

<div align="center">

Built for the **STaiMIC Nextflow Training Program**
by [Nkiruka Cynthia Efenji](https://github.com/Nkiruka-Cynthia) · Nextflow Ambassador · [@Seqera](https://seqera.io)

</div>
