#!/bin/sh
set -eu

# 0) Be in project root
echo "Project: $(pwd)"

pick_first() {
  # prints first existing path from args
  for p in "$@"; do
    [ -f "$p" ] && { echo "$p"; return 0; }
  done
  return 1
}

# 1) Best-known filenames first
BEST="$(pick_first \
  src/screens/NewReportScreen.tsx \
  src/screens/NewReport.tsx \
  src/screens/ReportNew.tsx \
  app/(new|report)*/index.tsx \
  app/new-report.tsx 2>/dev/null || true)"

# 2) Try filename patterns via git (fast) then find (fallback)
if [ -z "${BEST:-}" ]; then
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    CANDS="$(git ls-files | grep -Ei '\.(tsx|jsx|ts|js)$' | grep -Ei 'new[-_]?report|report.*screen|NewReportScreen' || true)"
  else
    CANDS="$(find . -type f \( -name '*.tsx' -o -name '*.jsx' -o -name '*.ts' -o -name '*.js' \) \
      | grep -Ev '/node_modules/' \
      | grep -Ei 'new[-_]?report|report.*screen|NewReportScreen' || true)"
  fi
  BEST="$(printf '%s\n' "$CANDS" | head -n1 || true)"
fi

# 3) Content search (phrases we know are on the first page)
if [ -z "${BEST:-}" ]; then
  CANDS="$(grep -RIl --exclude-dir=node_modules \
      -E 'New Report|Save to Vault|Generate|Description|Photos|Category|Location' . 2>/dev/null || true)"
  # prefer src/screens & files with "Report" in the path
  PREFERRED="$(printf '%s\n' "$CANDS" | grep -Ei '^\.?/src/screens/.*report' | head -n1 || true)"
  BEST="${PREFERRED:-$(printf '%s\n' "$CANDS" | head -n1 || true)}"
fi

if [ -z "${BEST:-}" ] || [ ! -f "$BEST" ]; then
  echo "❌ Could not find a likely New Report UI file."
  echo "Tried patterns under: src/screens, app/, components/."
  exit 1
fi

# 4) Print with line numbers so you can reference specific lines
echo "===== FILE: $BEST ====="
nl -ba "$BEST"
