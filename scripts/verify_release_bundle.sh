#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${1:-}"

if [[ -z "${TARGET_DIR}" ]]; then
  VERSION="$(awk -F= '/^APP_VERSION=/{print $2}' "${ROOT_DIR}/.env.example" | head -n1)"
  VERSION="${VERSION:-0.1.0}"
  TARGET_DIR="${ROOT_DIR}/dist/new-api-log-statistics-${VERSION}"
fi

if [[ ! -d "${TARGET_DIR}" ]]; then
  echo "Release bundle directory not found: ${TARGET_DIR}" >&2
  exit 1
fi

required_paths=(
  "README.md"
  "LICENSE"
  "CHANGELOG.md"
  "CONTRIBUTING.md"
  "SECURITY.md"
  "Makefile"
  ".env.example"
  ".dockerignore"
  ".gitignore"
  "requirements.txt"
  "app/main.py"
  "web/index.html"
  "deploy/docker-compose.yml"
  "deploy/Dockerfile"
  "config/sources.example.yml"
  "scripts/init-config.sh"
  "scripts/smoke_test.sh"
)

for path in "${required_paths[@]}"; do
  if [[ ! -e "${TARGET_DIR}/${path}" ]]; then
    echo "Missing required release file: ${path}" >&2
    exit 1
  fi
done

forbidden_paths=(
  ".env"
  "config/sources.yml"
  "get_token.py"
  "TASKLIST.md"
  "new-api-log-statistics-plan.zh-CN.md"
  "database-access-and-onboarding.zh-CN.md"
  "export.csv"
  "docs"
  ".github"
)

for path in "${forbidden_paths[@]}"; do
  if [[ -e "${TARGET_DIR}/${path}" ]]; then
    echo "Forbidden release file exists: ${path}" >&2
    exit 1
  fi
done

if find "${TARGET_DIR}/runtime" -type f | grep -q .; then
  echo "Runtime directory must be empty in release bundle" >&2
  exit 1
fi

echo "Release bundle verified: ${TARGET_DIR}"
