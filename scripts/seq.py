#!/usr/bin/env python3
"""시퀀스 다이어그램 SVG 생성기 (표준 라이브러리만 사용).

쓰임:  python3 scripts/seq.py docs/diagrams/src/<이름>.seq.json docs/diagrams/<이름>
       → <이름>-light.svg, <이름>-dark.svg 를 만든다. PNG 는 render_diagrams.sh 가 rsvg-convert 로 만든다.
점검:  python3 scripts/seq.py --selftest

명세(JSON):
{
  "title": "추천 요청 흐름",
  "lanes": [{"id": "client", "label": "앱", "sub": "Flutter"}, ...],
  "steps": [
    {"kind": "band", "text": "① 요청 접수"},
    {"kind": "call", "from": "client", "to": "user", "text": "POST /api/v1/trips"},
    {"kind": "ret",  "from": "user", "to": "client", "text": "202 + job_id"},
    {"kind": "self", "from": "agent", "text": "LangGraph 실행"}
  ]
}
kind: call(실선 화살표) | ret(점선 화살표) | self(자기 자신) | band(단계 구분 띠)
"""
import html, json, pathlib, sys, xml.etree.ElementTree as ET

FONT = "Pretendard, 'Noto Sans KR', sans-serif"
THEMES = {
    "light": {"bg": "#FFFFFF", "fg": "#1F2328", "line": "#57606A", "lane_fill": "#DDF4FF", "lane_edge": "#0969DA",
              "band": "#F6F8FA", "band_edge": "#D0D7DE", "life": "#8C959F"},
    "dark": {"bg": "#0D1117", "fg": "#E6EDF3", "line": "#8B949E", "lane_fill": "#0C2D6B", "lane_edge": "#58A6FF",
             "band": "#161B22", "band_edge": "#30363D", "life": "#6E7681"},
}
LANE_GAP, MARGIN, HEAD_H, FS, LINE_H = 230, 70, 64, 13, 18


def text_width(s):
    """폰트 측정 없이 쓰는 근사 폭: 한글·전각은 글자 크기만큼, 그 밖은 0.58배."""
    return sum(FS if ord(c) > 0x2E7F else FS * 0.58 for c in s)


def wrap(s, max_px):
    """공백 기준으로 줄을 나누고, 한 단어가 폭을 넘으면(띄어쓰기 없는 긴 한국어 구간) 글자 단위로 자른다."""
    lines, cur = [], ""
    for word in s.split(" "):
        while text_width(word) > max_px:
            cut = 1
            while cut < len(word) and text_width(word[:cut + 1]) <= max_px:
                cut += 1
            if cur:
                lines.append(cur)
                cur = ""
            lines.append(word[:cut])
            word = word[cut:]
        cand = f"{cur} {word}".strip()
        if cur and text_width(cand) > max_px:
            lines.append(cur)
            cur = word
        else:
            cur = cand
    return lines + [cur] if cur else lines or [""]


def render(spec, theme):
    t = THEMES[theme]
    lanes = spec["lanes"]
    x = {ln["id"]: MARGIN + i * LANE_GAP + LANE_GAP / 2 for i, ln in enumerate(lanes)}
    width = MARGIN * 2 + LANE_GAP * len(lanes)
    out, y = [], HEAD_H + 40
    title = spec.get("title", "")
    for st in spec["steps"]:
        kind, txt = st["kind"], st.get("text", "")
        if kind == "band":
            out.append(f'<rect x="{MARGIN/2}" y="{y}" width="{width-MARGIN}" height="26" rx="4" fill="{t["band"]}" stroke="{t["band_edge"]}"/>'
                       f'<text x="{MARGIN/2+10}" y="{y+18}" font-weight="600">{html.escape(txt)}</text>')
            y += 40
            continue
        a = x[st["from"]]
        if kind == "self":
            # 설명은 레인 오른쪽에 쓰되, 오른쪽 여백이 왼쪽보다 좁으면(맨 오른쪽 레인) 왼쪽에 오른쪽 정렬로 쓴다.
            right, left = width - MARGIN / 2 - (a + 36), a - 8 - MARGIN / 2
            to_left = right < left
            lines = wrap(txt, min(left if to_left else right, LANE_GAP * 1.6))
            h = max(30, LINE_H * len(lines) + 8)
            out.append(f'<path d="M{a},{y} h28 v{h-8} h-28" fill="none" stroke="{t["line"]}" marker-end="url(#arr)"/>')
            tx, anchor = (a - 8, ' text-anchor="end"') if to_left else (a + 36, "")
            for i, ln in enumerate(lines):
                out.append(f'<text x="{tx}" y="{y+14+i*LINE_H}"{anchor}>{html.escape(ln)}</text>')
            y += h + 14
            continue
        b = x[st["to"]]
        lines = wrap(txt, max(abs(b - a) - 20, LANE_GAP * 0.8))
        y += LINE_H * len(lines)
        mid = (a + b) / 2
        for i, ln in enumerate(lines):
            out.append(f'<text x="{mid}" y="{y - 6 - (len(lines)-1-i)*LINE_H}" text-anchor="middle">{html.escape(ln)}</text>')
        dash = ' stroke-dasharray="6 4"' if kind == "ret" else ""
        out.append(f'<line x1="{a}" y1="{y}" x2="{b}" y2="{y}" stroke="{t["line"]}"{dash} marker-end="url(#arr)"/>')
        y += 22
    height = y + 30
    head = []
    for ln in lanes:
        cx = x[ln["id"]]
        head.append(f'<line x1="{cx}" y1="{HEAD_H}" x2="{cx}" y2="{height-10}" stroke="{t["life"]}" stroke-dasharray="3 5"/>'
                    f'<rect x="{cx-LANE_GAP/2+14}" y="12" width="{LANE_GAP-28}" height="{HEAD_H-18}" rx="6" fill="{t["lane_fill"]}" stroke="{t["lane_edge"]}"/>'
                    f'<text x="{cx}" y="34" text-anchor="middle" font-weight="700">{html.escape(ln["label"])}</text>'
                    f'<text x="{cx}" y="52" text-anchor="middle" font-size="11">{html.escape(ln.get("sub", ""))}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'font-family="{FONT}" font-size="{FS}" fill="{t["fg"]}" role="img" aria-label="{html.escape(title)}">'
            f'<title>{html.escape(title)}</title>'
            f'<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">'
            f'<path d="M0,0 L10,5 L0,10 z" fill="{t["line"]}"/></marker></defs>'
            f'<rect width="100%" height="100%" fill="{t["bg"]}"/>' + "".join(head) + "".join(out) + "</svg>\n")


def selftest():
    spec = {"title": "점검", "lanes": [{"id": "a", "label": "앱"}, {"id": "b", "label": "서버", "sub": "BFF"}],
            "steps": [{"kind": "band", "text": "① 단계"}, {"kind": "call", "from": "a", "to": "b", "text": "POST /v1/x <&>"},
                      {"kind": "self", "from": "b", "text": "처리 " * 40}, {"kind": "ret", "from": "b", "to": "a", "text": "200"}]}
    for theme in THEMES:
        root = ET.fromstring(render(spec, theme))          # 잘 짜인 XML 인지(특수문자 이스케이프 포함)
        ns = "{http://www.w3.org/2000/svg}"
        assert len(root.findall(f"{ns}line")) == 2 + 2, "레인 생명선 2 + 화살표 2"
        assert any("&lt;&amp;&gt;" in ET.tostring(e, encoding="unicode") for e in root.iter(f"{ns}text"))
        assert THEMES[theme]["bg"] in ET.tostring(root, encoding="unicode")
    assert len(wrap("가" * 100, 260)) > 1, "긴 한국어 문장은 여러 줄로 나뉜다"
    assert all(text_width(ln) <= 260 for ln in wrap("가" * 100 + " abc", 260))
    svg = render(spec, "light")                            # 맨 오른쪽 레인(b)의 자기 호출 설명은 캔버스 안(왼쪽)에 쓴다
    assert 'text-anchor="end"' in svg, "오른쪽 여백이 좁은 레인의 설명은 왼쪽 정렬로 바뀐다"
    print("seq.py selftest ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    elif len(sys.argv) == 3:
        spec = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
        for theme in THEMES:
            pathlib.Path(f"{sys.argv[2]}-{theme}.svg").write_text(render(spec, theme), encoding="utf-8")
    else:
        sys.exit(__doc__)
