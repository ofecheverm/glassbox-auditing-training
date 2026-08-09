# Getting Started — Session 4

Follow these steps in order, live during class. Takes about 15 minutes, then we move into the hands-on exercise.

> ⚠️ **Important:** Do NOT use the "Open in GitHub Codespaces" badge on the main README for this session — that badge always opens **STaiMIC's original repo**, not your personal copy, and you won't be able to push any changes from there. Follow Step 3 below instead.

---

### Step 1 — Fork the repo (skip if you already forked it before class)

Go to `github.com/STaiMIC/glassbox-auditing-training` → click **Fork** (top right) → creates your own copy under your GitHub account.

**Already forked earlier?** Your copy is missing tonight's updates. Sync it: on your fork's page, look for a **"Sync fork"** button near the top and click it.

---

### Step 2 — Enable GitHub Actions on your fork

GitHub turns Actions **off** by default on forks. On **your fork's** page, click the **Actions** tab. You'll see a green banner — click **"I understand my workflows, go ahead and enable them."**

Skip this step and nothing later will work — no red, no green, just silence.

---

### Step 3 — Open a Codespace from YOUR fork

On **your fork's** page (not STaiMIC's original): **Code → Codespaces → Create codespace on main**.

Wait for it to finish building — Nextflow and nf-test are pre-installed automatically.

---

### Step 4 — Trigger your first CI run, and watch it fail on GitHub itself

So far, GitHub Actions hasn't actually run yet on your fork — enabling it in Step 2 doesn't trigger a run by itself, only a `push` does. Let's trigger one now, before touching any code, to see GitHub catch the defect on its own servers, exactly like it caught it for the instructor.

```bash
git commit --allow-empty -m "Trigger first CI run"
git push
```

`--allow-empty` creates a commit with no file changes at all — its only purpose is to trigger the push. Since your fork's `main` still has the broken `triage.py` and an already-committed answer key from before, this push should make GitHub's Actions tab turn red ❌ — go check **your fork's page → Actions tab** to see it.

That red X is GitHub independently confirming the same defect you're about to find locally in the next step.

---

### Step 5 — Run the test locally, watch it fail too

In the Codespace terminal:

```bash
nf-test test tests/modules/triage.nf.test
```

This should fail immediately with a snapshot mismatch — this is Defect #4 (the per-record timestamp), caught automatically, this time on your own machine.

---

### Step 6 — Apply the fix

Copy the corrected `bin/triage.py` from the **Defect 4** section of `README.md`, and paste it in using the same `cat > bin/triage.py << 'EOF' ... EOF` command shown there.

---

### Step 7 — Delete the old answer key and let nf-test write a new one

The snapshot file (`tests/modules/triage.nf.test.snap`) is nf-test's saved "answer key" — the exact output it expects to see. Right now, that saved answer key still reflects the **old, broken** code (the one with the timestamp). Since you just changed the code in Step 6, the correct output has changed too — so the old answer key is now outdated and needs to be replaced, not compared against.

```bash
rm tests/modules/triage.nf.test.snap
```

`rm` deletes a file. This removes the outdated answer key completely — nf-test now has nothing to compare against.

```bash
nf-test test tests/modules/triage.nf.test
```

Run the test again. Since there's no answer key left, nf-test does something different this time: instead of comparing, it **records** whatever your fixed code produces as the new, correct answer key, and saves it. You should see `1 created` and **PASSED** — not a red failure.

Now run it **one more time**, completely unchanged, to prove your fix is genuinely stable:

```bash
nf-test test tests/modules/triage.nf.test
```

This second run compares against the new answer key you just created a moment ago. Since the code is deterministic now (no more timestamp), it should match perfectly — **PASSED**, no mismatch. That's the real "green" moment: same input, same code, same output, every time.

---

### Step 8 — Commit and push the real fix

```bash
git add bin/triage.py tests/modules/triage.nf.test.snap
git commit -m "Fix Defect 4: remove per-record timestamp"
git push
```

---

### Step 9 — Check your Actions tab — now it should be green

Go back to **your fork's** page → **Actions** tab. You should now see two runs: your earlier empty commit showing red ❌, and this new push showing green ✅ — a real, visible before/after, both caused by your own actions, not staged.

---

### Step 10 — Create your first tagged release

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
