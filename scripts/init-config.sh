#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p "${ROOT_DIR}/config" "${ROOT_DIR}/runtime"

if [[ ! -f "${ROOT_DIR}/.env" ]]; then
  cp "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
  echo "Created .env from .env.example"
else
  echo "Kept existing .env"
fi

if [[ ! -f "${ROOT_DIR}/config/sources.yml" ]]; then
  cp "${ROOT_DIR}/config/sources.example.yml" "${ROOT_DIR}/config/sources.yml"
  echo "Created config/sources.yml from config/sources.example.yml"
else
  echo "Kept existing config/sources.yml"
fi

echo "Initialization complete."
