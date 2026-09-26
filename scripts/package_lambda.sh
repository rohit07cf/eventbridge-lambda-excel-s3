#!/usr/bin/env bash
# =============================================================================
# package_lambda.sh
# =============================================================================
# Packages the Lambda source files and Python dependencies into a single ZIP
# archive (lambda.zip) ready for deployment via Terraform.
#
# The output ZIP contains:
#   - lambda_function.py   (Lambda handler / orchestrator)
#   - data_provider.py     (report data layer)
#   - excel_generator.py   (Excel workbook generation)
#   - openpyxl/            (and all transitive dependencies)
#
# openpyxl is NOT included in the standard Lambda Python runtime and must be
# bundled here.  boto3 IS provided by the Lambda runtime and is NOT included.
#
# Output:
#   lambda.zip             (repository root — git-ignored)
#   lambda_package/        (working directory — git-ignored)
#
# Usage:
#   bash scripts/package_lambda.sh
#
# Run from the repository root.
# =============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${REPO_ROOT}/lambda_package"
ZIP_PATH="${REPO_ROOT}/lambda.zip"
SRC_DIR="${REPO_ROOT}/src"
REQUIREMENTS="${SRC_DIR}/requirements.txt"

echo "=== Lambda packaging ==="
echo "Repository root : ${REPO_ROOT}"
echo "Build directory : ${BUILD_DIR}"
echo "Output ZIP      : ${ZIP_PATH}"
echo ""

# -----------------------------------------------------------------------------
# 1. Clean previous build
# -----------------------------------------------------------------------------
echo "[1/5] Cleaning previous build..."
rm -rf "${BUILD_DIR}"
rm -f  "${ZIP_PATH}"

# -----------------------------------------------------------------------------
# 2. Create fresh build directory
# -----------------------------------------------------------------------------
echo "[2/5] Creating build directory..."
mkdir -p "${BUILD_DIR}"

# -----------------------------------------------------------------------------
# 3. Install Python dependencies into the build directory
#    --platform manylinux2014_x86_64 ensures binary wheels are compatible with
#    the Lambda Amazon Linux 2 runtime.  openpyxl is pure Python so this flag
#    is a no-op for it, but it is good practice for any future binary deps.
# -----------------------------------------------------------------------------
echo "[3/5] Installing dependencies from ${REQUIREMENTS}..."
pip3 install \
    -r "${REQUIREMENTS}" \
    --target "${BUILD_DIR}" \
    --platform manylinux2014_x86_64 \
    --only-binary=:all: \
    --quiet

# -----------------------------------------------------------------------------
# 4. Copy Lambda source files into the build directory
# -----------------------------------------------------------------------------
echo "[4/5] Copying Lambda source files..."
cp "${SRC_DIR}/lambda_function.py" "${BUILD_DIR}/"
cp "${SRC_DIR}/data_provider.py"   "${BUILD_DIR}/"
cp "${SRC_DIR}/excel_generator.py" "${BUILD_DIR}/"

# -----------------------------------------------------------------------------
# 5. Create the ZIP archive (exclude .pyc files and __pycache__ directories)
# -----------------------------------------------------------------------------
echo "[5/5] Creating lambda.zip..."
cd "${BUILD_DIR}"
zip -r "${ZIP_PATH}" . \
    --exclude "*.pyc" \
    --exclude "*/__pycache__/*" \
    --exclude "__pycache__/*" \
    -q
cd "${REPO_ROOT}"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
ZIP_SIZE=$(du -sh "${ZIP_PATH}" | cut -f1)
echo ""
echo "=== Lambda package ready ==="
echo "File : ${ZIP_PATH}"
echo "Size : ${ZIP_SIZE}"
echo ""
echo "Verify contents with:"
echo "  unzip -l lambda.zip | grep openpyxl | head -5"
