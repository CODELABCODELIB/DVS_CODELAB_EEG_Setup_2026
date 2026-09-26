#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

echo "Checking the Python environment..."

if [[ -x "${script_dir}/.venv/bin/python" ]]; then
    python_bin="${script_dir}/.venv/bin/python"
    echo "Using the existing project environment: ${script_dir}/.venv"
elif python3 -c "import dv_processing" >/dev/null 2>&1; then
    python_bin="$(command -v python3)"
    echo "Using the existing Python environment: ${python_bin}"
else
    echo "No ready Python environment was found. Creating ${script_dir}/.venv ..."
    python3 -m venv --without-pip "${script_dir}/.venv"
    python_bin="${script_dir}/.venv/bin/python"
fi

echo "Checking required packages..."
if "${python_bin}" -c "import dv_processing" >/dev/null 2>&1; then
    dv_location="$("${python_bin}" -c "import dv_processing; print(dv_processing.__file__)")"
    echo "dv-processing is already installed: ${dv_location}"
else
    echo "dv-processing is missing. Installing dv-processing 2.0.4 ..."
    package_dir="$("${python_bin}" -c "import site; print(site.getsitepackages()[0])")"
    python3 -m pip install --target "${package_dir}" dv-processing==2.0.4
fi

if "${python_bin}" -c "import cv2" >/dev/null 2>&1; then
    echo "OpenCV display package is already installed."
else
    echo "OpenCV display package is missing. Installing opencv-python 5.0.0.93 ..."
    package_dir="$("${python_bin}" -c "import site; print(site.getsitepackages()[0])")"
    python3 -m pip install --target "${package_dir}" --no-deps opencv-python==5.0.0.93
fi

"${python_bin}" -c "import dv_processing"
"${python_bin}" -c "import cv2"
printf '%s\n' "${python_bin}" > "${script_dir}/.python-path"
chmod +x "${script_dir}/start_recording.sh"

echo
echo "Environment check completed successfully."
echo "You can now start recording with:"
echo "  ${script_dir}/start_recording.sh"
