#!/bin/sh
# docs/diagrams/src 의 원본에서 SVG(라이트·다크)와 PNG 를 모두 다시 만든다.
# 필요한 도구: python3(표준 라이브러리), rsvg-convert(librsvg), Graphviz dot(.dot 원본이 있을 때).
# 폰트: Pretendard(SIL OFL 1.1). 설치돼 있지 않으면 대체 폰트로 그려진다.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
SRC="$ROOT/docs/diagrams/src"
OUT="$ROOT/docs/diagrams"

for spec in "$SRC"/*.seq.json; do
  [ -e "$spec" ] || continue
  name=$(basename "$spec" .seq.json)
  python3 "$ROOT/scripts/seq.py" "$spec" "$OUT/$name"
done

for dot_src in "$SRC"/*.dot; do
  [ -e "$dot_src" ] || continue
  name=$(basename "$dot_src" .dot)
  dot -Tsvg "$dot_src" -o "$OUT/$name-light.svg"
done

for svg in "$OUT"/*-light.svg "$OUT"/*-dark.svg; do
  [ -e "$svg" ] || continue
  rsvg-convert -w 1600 "$svg" -o "${svg%.svg}.png"
done
echo "rendered: $(ls "$OUT"/*.svg | wc -l | tr -d ' ') svg, $(ls "$OUT"/*.png | wc -l | tr -d ' ') png"
