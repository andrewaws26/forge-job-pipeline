#!/bin/bash
# Render a resume HTML to PDF and enforce the one-page gate.
# Usage: ./render.sh "Candidate - Company - Role"
DIR="$(cd "$(dirname "$0")" && pwd)"
F="$1"
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu \
  --no-pdf-header-footer --print-to-pdf="$DIR/$F.pdf" "file://$DIR/$F.html" 2>/dev/null
PAGES=$(qpdf --show-npages "$DIR/$F.pdf")
echo "pages: $PAGES"
[ "$PAGES" = "1" ] || { echo "PAGE GATE FAILED: trim content, do not shrink below 8.9pt"; exit 1; }
