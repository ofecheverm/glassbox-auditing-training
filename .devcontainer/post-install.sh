#!/bin/bash
# post-install.sh
# Runs automatically when the GitHub Codespace is created.
# Installs Nextflow, nf-test, and pre-pulls the container images this training repo uses.

set -e

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  GlassBox Auditing Training — Codespace Setup                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

###############################################################################
# Step 1 — Install Nextflow
###############################################################################

echo "Installing Nextflow..."

conda install -y -c bioconda nextflow > /dev/null 2>&1

echo "✓ Nextflow: $(nextflow -version 2>&1 | head -1)"

###############################################################################
# Step 2 — Install nf-test
###############################################################################

echo ""
echo "Installing nf-test..."

curl -fsSL https://get.nf-test.com | bash > /dev/null 2>&1
mkdir -p "$HOME/.local/bin"
mv nf-test "$HOME/.local/bin/"
chmod +x "$HOME/.local/bin/nf-test"
export PATH="$PATH:$HOME/.local/bin"
echo 'export PATH="$PATH:$HOME/.local/bin"' >> "$HOME/.bashrc"

echo "✓ nf-test: $("$HOME/.local/bin/nf-test" version 2>&1 | head -2 | tail -1)"

###############################################################################
# Step 3 — Pre-pull the container images used by this training repo
###############################################################################

echo ""
echo "Pre-pulling container images..."

for i in $(seq 1 10); do
    if docker info > /dev/null 2>&1; then
        break
    fi
    sleep 2
done

if command -v docker >/dev/null 2>&1 && docker info > /dev/null 2>&1; then
    docker pull python:3.11-slim > /dev/null 2>&1 && echo "✓ python:3.11-slim cached"
    docker pull python:latest > /dev/null 2>&1 && echo "✓ python:latest cached"
else
    echo "⚠ Docker is still starting. Images will pull on first pipeline run instead."
fi

###############################################################################
# Step 4 — Verify installation
###############################################################################

echo ""
echo "Verifying installation..."

echo "✓ Java: $(java -version 2>&1 | head -1)"
echo "✓ Nextflow: $(nextflow -version 2>&1 | head -1)"
echo "✓ nf-test: $("$HOME/.local/bin/nf-test" version 2>&1 | head -2 | tail -1)"

if command -v docker >/dev/null 2>&1; then
    echo "✓ Docker: $(docker --version)"
else
    echo "⚠ Docker is still starting. If a pipeline run fails, wait a few seconds and try again."
fi

###############################################################################
# Finished
###############################################################################

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ✅ Setup complete!                                          ║"
echo "║                                                                ║"
echo "║  Start the practical with:                                   ║"
echo "║                                                                ║"
echo "║     bash setup.sh                                             ║"
echo "║                                                                ║"
echo "║  Then work through docs/audit-checklist.md                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""