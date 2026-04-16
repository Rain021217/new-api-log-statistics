#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(awk -F= '/^APP_VERSION=/{print $2}' "${ROOT_DIR}/.env.example" | head -n1)"
VERSION="${VERSION:-0.2.0}"
BUNDLE_NAME="new-api-log-statistics-${VERSION}"
DIST_DIR="${ROOT_DIR}/dist"
BUNDLE_DIR="${DIST_DIR}/${BUNDLE_NAME}"
ARCHIVE_PATH="${DIST_DIR}/${BUNDLE_NAME}.tar.gz"

rm -rf "${BUNDLE_DIR}"
mkdir -p "${BUNDLE_DIR}/config" "${BUNDLE_DIR}/runtime" "${DIST_DIR}"

cp -R "${ROOT_DIR}/app" "${BUNDLE_DIR}/app"
cp -R "${ROOT_DIR}/web" "${BUNDLE_DIR}/web"
cp -R "${ROOT_DIR}/deploy" "${BUNDLE_DIR}/deploy"
cp -R "${ROOT_DIR}/scripts" "${BUNDLE_DIR}/scripts"

cp "${ROOT_DIR}/README.md" "${BUNDLE_DIR}/README.md"
cp "${ROOT_DIR}/LICENSE" "${BUNDLE_DIR}/LICENSE"
cp "${ROOT_DIR}/CHANGELOG.md" "${BUNDLE_DIR}/CHANGELOG.md"
cp "${ROOT_DIR}/CONTRIBUTING.md" "${BUNDLE_DIR}/CONTRIBUTING.md"
cp "${ROOT_DIR}/SECURITY.md" "${BUNDLE_DIR}/SECURITY.md"
cp "${ROOT_DIR}/requirements.txt" "${BUNDLE_DIR}/requirements.txt"
cp "${ROOT_DIR}/Makefile" "${BUNDLE_DIR}/Makefile"
cp "${ROOT_DIR}/.env.example" "${BUNDLE_DIR}/.env.example"
cp "${ROOT_DIR}/.dockerignore" "${BUNDLE_DIR}/.dockerignore"
cp "${ROOT_DIR}/.gitignore" "${BUNDLE_DIR}/.gitignore"
cp "${ROOT_DIR}/config/sources.example.yml" "${BUNDLE_DIR}/config/sources.example.yml"

find "${BUNDLE_DIR}" -type d -name "__pycache__" -prune -exec rm -rf {} +
find "${BUNDLE_DIR}" -type f -name "*.pyc" -delete

tar -czf "${ARCHIVE_PATH}" -C "${DIST_DIR}" "${BUNDLE_NAME}"

echo "Bundle directory: ${BUNDLE_DIR}"
echo "Bundle archive: ${ARCHIVE_PATH}"
