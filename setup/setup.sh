#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Add anaconda to PATH in .bashrc
echo 'export PATH="/apps/anaconda/bin:$PATH"' >> ~/.bashrc

# 2. Apply the updated PATH for the remainder of this script
export PATH="/apps/anaconda/bin:$PATH"

# 3. Install pip if not already available
if ! command -v pip &>/dev/null; then
    echo "pip not found, installing from local wheel..."
    python "$SCRIPT_DIR/pip-26.1.2-py3-none-any.whl/pip" install \
        --no-index "$SCRIPT_DIR/pip-26.1.2-py3-none-any.whl"
fi

# 4. Install osrm_bindings
pip install "$SCRIPT_DIR/osrm_bindings-0.3.0-cp312-abi3-manylinux_2_28_x86_64.whl"

# 5. Install python-dotenv
pip install "$SCRIPT_DIR/python_dotenv-1.2.2-py3-none-any.whl"

echo "Setup complete."
