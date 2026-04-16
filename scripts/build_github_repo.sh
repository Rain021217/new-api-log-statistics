#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="$(awk -F= '/^APP_VERSION=/{print $2}' "${ROOT_DIR}/.env.example" | head -n1)"
VERSION="${VERSION:-0.2.0}"
SOURCE_DIR="${ROOT_DIR}/dist/new-api-log-statistics-${VERSION}"
TARGET_DIR="${ROOT_DIR}/dist/new-api-log-statistics-${VERSION}-github"
ARCHIVE_PATH="${ROOT_DIR}/dist/new-api-log-statistics-${VERSION}-github.tar.gz"

if [[ ! -d "${SOURCE_DIR}" ]]; then
  "${ROOT_DIR}/scripts/build_release_bundle.sh"
  "${ROOT_DIR}/scripts/verify_release_bundle.sh"
fi

rm -rf "${TARGET_DIR}"
cp -R "${SOURCE_DIR}" "${TARGET_DIR}"
mkdir -p "${TARGET_DIR}/docs"
mkdir -p "${TARGET_DIR}/.github"
cp -R "${ROOT_DIR}/.github/." "${TARGET_DIR}/.github"
cp "${ROOT_DIR}/docs/github-auth-faq.zh-CN.md" "${TARGET_DIR}/docs/github-auth-faq.zh-CN.md"
cp "${ROOT_DIR}/docs/maintainer-publishing.zh-CN.md" "${TARGET_DIR}/docs/maintainer-publishing.zh-CN.md"
cp "${ROOT_DIR}/docs/github-web-repository-setup.zh-CN.md" "${TARGET_DIR}/docs/github-web-repository-setup.zh-CN.md"
cp "${ROOT_DIR}/docs/release-notes-v${VERSION}.md" "${TARGET_DIR}/docs/release-notes-v${VERSION}.md"

tar -czf "${ARCHIVE_PATH}" -C "${ROOT_DIR}/dist" "$(basename "${TARGET_DIR}")"

echo "GitHub-ready directory: ${TARGET_DIR}"
echo "GitHub-ready archive: ${ARCHIVE_PATH}"
