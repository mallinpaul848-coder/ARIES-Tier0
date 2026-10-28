#!/data/data/com.termux/files/usr/bin/bash
set -e
cd "$(dirname "$0")"
if ! command -v python >/dev/null 2>&1; then
  echo "Python is missing. In Termux, run: pkg update && pkg install python"
  exit 1
fi
echo "MALLIN self-hosted site starting on port 8080."
echo "Keep this terminal open and keep the phone powered and connected to home Wi-Fi."
echo "This is HTTP demo hosting only. Do not enter passwords or private data."
python server.py --bind 0.0.0.0 --port 8080
