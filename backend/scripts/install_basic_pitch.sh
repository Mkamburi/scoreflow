#!/usr/bin/env bash
# Install Basic Pitch on macOS with Python 3.12+ (including 3.13).
# Standard `pip install basic-pitch` fails because it tries to pull tensorflow-macos,
# which is not available for Python 3.13. On Mac we use CoreML instead.

set -euo pipefail

cd "$(dirname "$0")/.."
source ../venv/bin/activate

echo "Installing Basic Pitch 0.4.0 with CoreML backend (no TensorFlow)..."

pip install "basic-pitch==0.4.0" --no-deps
pip install \
  "librosa>=0.8.0" \
  "mir-eval>=0.6" \
  "pretty-midi>=0.2.9" \
  "resampy>=0.2.2,<0.4.3" \
  scikit-learn \
  scipy \
  coremltools \
  mido

echo "Verifying basic-pitch CLI..."
basic-pitch --help >/dev/null

echo "Done. Basic Pitch is ready (CoreML on Mac)."
