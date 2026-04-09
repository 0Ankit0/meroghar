#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
OUT_DIR="${ROOT_DIR}/artifacts/phase1/${STAMP}"
LOG_FILE="${OUT_DIR}/phase1-baseline.log"

mkdir -p "${OUT_DIR}"

log() {
  printf '[%s] %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$*" | tee -a "${LOG_FILE}"
}

run_cmd() {
  local cmd="$1"
  log "Running: ${cmd}"
  if bash -lc "${cmd}" >>"${LOG_FILE}" 2>&1; then
    log "PASS: ${cmd}"
  else
    log "FAIL: ${cmd}"
    return 1
  fi
}

log "Phase 1 baseline execution started"
log "Logs: ${LOG_FILE}"

run_cmd "make setup"
run_cmd "make infra-up"
run_cmd "make backend-migrate"
run_cmd "make health-check"
run_cmd "make docs"

if [[ -n "${BACKEND_URL:-}" ]]; then
  log "Collecting capability snapshots from ${BACKEND_URL}"
  curl -fsS "${BACKEND_URL%/}/system/capabilities/" -o "${OUT_DIR}/capabilities.json"
  curl -fsS "${BACKEND_URL%/}/system/providers/" -o "${OUT_DIR}/providers.json"
  log "Wrote ${OUT_DIR}/capabilities.json"
  log "Wrote ${OUT_DIR}/providers.json"
else
  log "BACKEND_URL not set; skipping capability/provider snapshots"
  log "Set BACKEND_URL (for example http://localhost:8000) and re-run to capture API evidence"
fi

log "Phase 1 baseline execution completed"
