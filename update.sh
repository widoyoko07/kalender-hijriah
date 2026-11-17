#!/usr/bin/env bash
# Perbarui kalender Hijriah: bangun ulang .ics dari kemenag.json, commit, dan push (Pages ikut terbarui).
# Pakai: ./update.sh [tahun_mulai] [tahun_akhir]   (default 2026 2035)
set -euo pipefail
cd "$(dirname "$0")"
PY=../.venv/bin/python
[ -x "$PY" ] || PY=python3
"$PY" buat_kalender.py "${1:-2026}" "${2:-2035}"
git add -A
if git diff --cached --quiet; then
  echo "Tidak ada perubahan."
else
  git commit -qm "Perbarui kalender"
  git push -q
  echo "Terbarui: https://widoyoko07.github.io/kalender-hijriah/"
fi
