#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAMP="$(date -u +"%Y%m%dT%H%M%SZ")"
OUT_DIR="${ROOT_DIR}/artifacts/phase2/${STAMP}"
LOG_FILE="${OUT_DIR}/phase2-requirements-lock.log"
TEMPLATE_DIR="${ROOT_DIR}/docs/implementation/phase2"

mkdir -p "${OUT_DIR}"

log() {
  printf '[%s] %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$*" | tee -a "${LOG_FILE}"
}

copy_template() {
  local src="$1"
  local dst="$2"
  cp "${src}" "${dst}"
  log "Generated: ${dst}"
}

log "Phase 2 requirements lock initialization started"
log "Logs: ${LOG_FILE}"

copy_template "${TEMPLATE_DIR}/mvp-backlog-template.md" "${OUT_DIR}/mvp-backlog.md"
copy_template "${TEMPLATE_DIR}/story-surface-mapping-template.md" "${OUT_DIR}/story-surface-mapping.md"
copy_template "${TEMPLATE_DIR}/out-of-scope-v1-template.md" "${OUT_DIR}/out-of-scope-v1.md"

log "Next actions:"
log "1) Fill the generated files with project-specific content"
log "2) Attach product/engineering/QA sign-off records"
log "3) Link finalized docs back into IMPLEMENTATION_CHECKLIST Task 2 evidence"

log "Phase 2 requirements lock initialization completed"
