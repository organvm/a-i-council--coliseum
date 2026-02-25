#!/usr/bin/env bash
set -euo pipefail

# Generate an Anchor program keypair and (optionally) apply the resulting pubkey to
# anchor/Anchor.toml and anchor/programs/ai-coliseum/src/lib.rs.
#
# Usage:
#   scripts/generate-anchor-program-keypair.sh
#   scripts/generate-anchor-program-keypair.sh --apply
#   scripts/generate-anchor-program-keypair.sh --force --apply
#   scripts/generate-anchor-program-keypair.sh --keypair anchor/target/deploy/custom.json

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_KEYPAIR_PATH="${REPO_ROOT}/anchor/target/deploy/ai_coliseum-keypair.json"
KEYPAIR_PATH="${DEFAULT_KEYPAIR_PATH}"
APPLY=0
FORCE=0

ANCHOR_TOML="${REPO_ROOT}/anchor/Anchor.toml"
PROGRAM_LIB="${REPO_ROOT}/anchor/programs/ai-coliseum/src/lib.rs"

usage() {
  cat <<'EOF'
Generate an Anchor program keypair and print/apply the corresponding program ID.

Options:
  --apply                 Patch anchor/Anchor.toml and declare_id! with generated pubkey
  --force                 Overwrite existing keypair file if present
  --keypair <path>        Output keypair path (default: anchor/target/deploy/ai_coliseum-keypair.json)
  -h, --help              Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      APPLY=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --keypair)
      KEYPAIR_PATH="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v solana-keygen >/dev/null 2>&1; then
  echo "solana-keygen is required but was not found on PATH." >&2
  echo "Install Solana CLI first, then rerun this script." >&2
  exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required for portable file patching but was not found on PATH." >&2
  exit 1
fi

mkdir -p "$(dirname "${KEYPAIR_PATH}")"

if [[ -f "${KEYPAIR_PATH}" && "${FORCE}" -ne 1 ]]; then
  echo "Keypair already exists: ${KEYPAIR_PATH}" >&2
  echo "Use --force to overwrite, or pass --keypair to write a different file." >&2
  exit 1
fi

echo "Generating Anchor program keypair at: ${KEYPAIR_PATH}"
solana-keygen new --silent --no-bip39-passphrase -o "${KEYPAIR_PATH}" >/dev/null

PROGRAM_ID="$(solana-keygen pubkey "${KEYPAIR_PATH}")"
echo
echo "Generated program ID:"
echo "${PROGRAM_ID}"
echo

if [[ "${APPLY}" -eq 1 ]]; then
  export PROGRAM_ID ANCHOR_TOML PROGRAM_LIB
  python3 <<'PY'
import os
import re
from pathlib import Path

program_id = os.environ["PROGRAM_ID"]
anchor_toml = Path(os.environ["ANCHOR_TOML"])
program_lib = Path(os.environ["PROGRAM_LIB"])

anchor_text = anchor_toml.read_text()
anchor_text, n1 = re.subn(
    r'(ai_coliseum\s*=\s*")([1-9A-HJ-NP-Za-km-z]+)(")',
    rf'\g<1>{program_id}\g<3>',
    anchor_text,
    count=1,
)
if n1 != 1:
    raise SystemExit("Failed to update ai_coliseum program id in anchor/Anchor.toml")
anchor_toml.write_text(anchor_text)

lib_text = program_lib.read_text()
lib_text, n2 = re.subn(
    r'declare_id!\("([1-9A-HJ-NP-Za-km-z]+)"\);',
    f'declare_id!("{program_id}");',
    lib_text,
    count=1,
)
if n2 != 1:
    raise SystemExit("Failed to update declare_id! in program lib.rs")
program_lib.write_text(lib_text)
PY
  echo "Applied program ID to:"
  echo "  - ${ANCHOR_TOML}"
  echo "  - ${PROGRAM_LIB}"
  echo
fi

echo "Next steps:"
echo "  1. Keep the keypair file safe: ${KEYPAIR_PATH}"
echo "  2. Run: cargo test --manifest-path anchor/programs/ai-coliseum/Cargo.toml"
echo "  3. Commit the code changes, but do NOT commit the keypair JSON"
