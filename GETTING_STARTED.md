# Getting Started — Session 4

Follow these steps in order, live during class. Takes about 15 minutes, then we move into the hands-on exercise.

> ⚠️ **Important:** Do NOT use the "Open in GitHub Codespaces" badge on the main README for this session — that badge always opens **STaiMIC's original repo**, not your personal copy, and you won't be able to push any changes from there. Follow Step 3 below instead.

---

### Step 1 — Fork the repo (skip if you already forked it before class)

Go to `github.com/STaiMIC/glassbox-auditing-training` → click **Fork** (top right) → creates your own copy under your GitHub account.

**Already forked earlier?** Your copy is missing tonight's updates. Sync it: on your fork's page, look for a **"Sync fork"** button near the top and click it.

---

### Step 2 — Enable GitHub Actions on your fork

GitHub turns Actions **off** by default on forks. On **your fork's** page, click the **Actions** tab. You'll see a yellow banner — click **"I understand my workflows, go ahead and enable them."**

Skip this step and nothing later will work — no red, no green, just silence.

---

### Step 3 — Open a Codespace from YOUR fork

On **your fork's** page (not STaiMIC's original): **Code → Codespaces → Create codespace on main**.

Wait for it to finish building — Nextflow and nf-test are pre-installed automatically.

---

### Step 4 — Run the test, watch it fail

In the Codespace terminal:

```bash
nf-test test tests/modules/triage.nf.test
```

This should fail immediately with a snapshot mismatch — this is Defect #4 (the per-record timestamp), caught automatically.

---

### Step 5 — Apply the fix

Copy the corrected `bin/triage.py` from the **Defect 4** section of `README.md`, and paste it in using the same `cat > bin/triage.py << 'EOF' ... EOF` command shown there.

---

### Step 6 — Reset the snapshot and confirm it's green locally

```bash
rm -rf tests/modules/__snapshot__
nf-test test tests/modules/triage.nf.test
```

---

### Step 7 — Commit and push

```bash
git add bin/triage.py tests/modules/__snapshot__
git commit -m "Fix Defect 4: remove per-record timestamp"
git push
```

---

### Step 8 — Check your Actions tab

Go back to **your fork's** page → **Actions** tab. A new run should appear and turn green ✅ — automatic proof, on GitHub's own servers, that your fix works.

---

### Step 9 — Create your first tagged release

The last piece of Defect #6 was "no tagged release" — a fixed, citable version anyone can point to. Now that your fix is pushed and green, tag it:

```bash
git tag v0.1.0
git push origin v0.1.0
```

Check it worked:

```bash
git ls-remote --tags origin
```

You should see `v0.1.0` listed. That's it — your fork now has working code, an automatic check that guards it forever, and a fixed version anyone can reference. All six defects from Session 3 are now fully closed on your own fork.

---

That's it — you now have your own working CI pipeline that checks itself, forever, without you needing to remember to run anything.
