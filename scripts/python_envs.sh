#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROOT_VENV="$ROOT_DIR/.venv"
BACKEND_VENV="$ROOT_DIR/backend/venv"
AI_VENV="$ROOT_DIR/ai_services/venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

log() {
  printf "\n[%s] %s\n" "$1" "$2"
}

ensure_venv() {
  local venv_path="$1"
  if [[ ! -d "$venv_path" ]]; then
    "$PYTHON_BIN" -m venv "$venv_path"
  fi
}

install_backend_env() {
  log INFO "Installing backend dependencies into backend/venv"
  "$BACKEND_VENV/bin/python" -m pip install --upgrade pip setuptools wheel
  "$BACKEND_VENV/bin/python" -m pip install -r "$ROOT_DIR/backend/requirements.txt"
  "$BACKEND_VENV/bin/python" -m pip install pytest==8.0.0
}

install_ai_env() {
  log INFO "Installing ai_services dependencies into ai_services/venv"
  "$AI_VENV/bin/python" -m pip install --upgrade pip setuptools wheel
  "$AI_VENV/bin/python" -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.2.2
  "$AI_VENV/bin/python" -m pip install -r "$ROOT_DIR/ai_services/requirements.txt"
}

install_root_env() {
  log INFO "Installing shared root tools into .venv"
  "$ROOT_VENV/bin/python" -m pip install --upgrade pip setuptools wheel
  "$ROOT_VENV/bin/python" -m pip install pytest==8.0.0
}

install_root_full_env() {
  log INFO "Installing full-stack dependencies into .venv (backend + ai_services)"
  "$ROOT_VENV/bin/python" -m pip install --upgrade pip setuptools wheel
  "$ROOT_VENV/bin/python" -m pip install -r "$ROOT_DIR/backend/requirements.txt"

  "$ROOT_VENV/bin/python" -m pip install --index-url https://download.pytorch.org/whl/cpu torch==2.2.2
  "$ROOT_VENV/bin/python" -m pip install -r "$ROOT_DIR/ai_services/requirements.txt"

  "$ROOT_VENV/bin/python" -m pip install pytest==8.0.0
}

bootstrap() {
  log INFO "Creating venvs (root, backend, ai_services)"
  ensure_venv "$ROOT_VENV"
  ensure_venv "$BACKEND_VENV"
  ensure_venv "$AI_VENV"

  install_root_env
  install_backend_env
  install_ai_env

  log OK "Bootstrap complete"
  doctor
}

doctor_env() {
  local name="$1"
  local py="$2"
  if [[ ! -x "$py" ]]; then
    printf -- "- %-10s: missing\n" "$name"
    return
  fi

  local details
  details="$($py -c "import sys, importlib.util; print(sys.version.split()[0]); print(bool(importlib.util.find_spec('pytest'))); print(bool(importlib.util.find_spec('fastapi'))); print(bool(importlib.util.find_spec('sentence_transformers'))); print(bool(importlib.util.find_spec('torch')));")"

  local pyver has_pytest has_fastapi has_st has_torch
  pyver="$(printf '%s' "$details" | sed -n '1p')"
  has_pytest="$(printf '%s' "$details" | sed -n '2p')"
  has_fastapi="$(printf '%s' "$details" | sed -n '3p')"
  has_st="$(printf '%s' "$details" | sed -n '4p')"
  has_torch="$(printf '%s' "$details" | sed -n '5p')"

  printf -- "- %-10s: python=%s pytest=%s fastapi=%s sentence_transformers=%s torch=%s\n" \
    "$name" "$pyver" "$has_pytest" "$has_fastapi" "$has_st" "$has_torch"
}

doctor() {
  log INFO "Environment health check"
  doctor_env "root" "$ROOT_VENV/bin/python"
  doctor_env "backend" "$BACKEND_VENV/bin/python"
  doctor_env "ai_service" "$AI_VENV/bin/python"

  cat <<'EOF'

Recommended usage:
- Root orchestration: source .venv/bin/activate
- Backend coding:     source backend/venv/bin/activate
- AI coding:          source ai_services/venv/bin/activate

Run tests from root (no env switching needed):
- ./scripts/python_envs.sh test-backend
- ./scripts/python_envs.sh test-ai
- ./scripts/python_envs.sh test-all
EOF
}

test_backend() {
  log INFO "Running backend tests with backend/venv"
  (cd "$ROOT_DIR/backend" && "$BACKEND_VENV/bin/python" -m pytest tests -v)
}

test_ai() {
  log INFO "Running ai_services tests with ai_services/venv"
  (cd "$ROOT_DIR/ai_services" && "$AI_VENV/bin/python" -m pytest tests -v)
}

test_all() {
  test_backend
  test_ai
}

usage() {
  cat <<'EOF'
Usage: ./scripts/python_envs.sh <command>

Commands:
  bootstrap      Create/update all 3 venvs and install dependencies
  bootstrap-root-full
                 Install full backend+ai dependencies into root .venv
  doctor         Show health/status of all 3 venvs
  test-backend   Run backend tests using backend/venv
  test-ai        Run ai_services tests using ai_services/venv
  test-all       Run backend + ai_services tests
EOF
}

case "${1:-}" in
  bootstrap)
    bootstrap
    ;;
  bootstrap-root-full)
    ensure_venv "$ROOT_VENV"
    install_root_full_env
    doctor
    ;;
  doctor)
    doctor
    ;;
  test-backend)
    test_backend
    ;;
  test-ai)
    test_ai
    ;;
  test-all)
    test_all
    ;;
  *)
    usage
    exit 1
    ;;
esac
