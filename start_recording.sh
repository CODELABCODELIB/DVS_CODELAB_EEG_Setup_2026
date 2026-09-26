#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "${script_dir}/.python-path" ]]; then
    IFS= read -r python_bin < "${script_dir}/.python-path"
elif [[ -x "${script_dir}/.venv/bin/python" ]]; then
    python_bin="${script_dir}/.venv/bin/python"
else
    python_bin="$(command -v python3)"
fi

echo "Starting the two-camera DVS recorder..."
exec "${python_bin}" "${script_dir}/record_two_cameras.py" "$@"
