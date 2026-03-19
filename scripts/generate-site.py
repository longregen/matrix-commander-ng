#!/usr/bin/env python3
"""Generate the GitHub Pages site for matrix-commander-ng test results."""

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path


def generate(output_dir, comparison_path=None, parity_path=None, summary_path=None):
    comparison = []
    if comparison_path:
        with open(comparison_path) as f:
            comparison = json.load(f)

    parity = None
    if parity_path:
        with open(parity_path) as f:
            parity = json.load(f)

    summary = None
    if summary_path:
        with open(summary_path) as f:
            summary = json.load(f)

    # --- Tab 1: Output Comparison ---
    n_identical = 0
    n_ws_only = 0
    n_key_order = 0
    n_different = 0
    n_empty = 0

    def strip_ws(s):
        """Remove all whitespace for comparison."""
        return "".join(s.split())

    def json_equal(a, b):
        """Check if two strings are equivalent JSON (ignoring key order)."""
        try:
            return json.loads(a) == json.loads(b)
        except (json.JSONDecodeError, TypeError):
            return False

    for entry in comparison:
        py = entry.get("py_stdout", "").strip()
        rs = entry.get("rs_stdout", "").strip()
        if not py and not rs:
            n_empty += 1
        elif py == rs:
            n_identical += 1
        elif strip_ws(py) == strip_ws(rs):
            n_ws_only += 1
        elif json_equal(py, rs):
            n_key_order += 1
        else:
            n_different += 1
    n_total = len(comparison)

    comparison_html = ""
    for entry in comparison:
        cid = entry["id"]
        if "-" in cid:
            parts = cid.rsplit("-", 1)
            if parts[1] in ("text", "json"):
                label = f"{parts[0]} ({parts[1]})"
            else:
                label = cid
        else:
            label = cid

        cmd_py = html.escape(entry.get("command_py", ""))
        cmd_rs = html.escape(entry.get("command_rs", ""))
        py_out = html.escape(entry.get("py_stdout", ""))
        rs_out = html.escape(entry.get("rs_stdout", ""))
        py_err = html.escape(entry.get("py_stderr", ""))
        rs_err = html.escape(entry.get("rs_stderr", ""))
        py_rc = entry.get("py_rc", "")
        rs_rc = entry.get("rs_rc", "")

        py_raw = entry.get("py_stdout", "").strip()
        rs_raw = entry.get("rs_stdout", "").strip()
        both_empty = not py_raw and not rs_raw
        match = py_raw == rs_raw

        ws_match = strip_ws(py_raw) == strip_ws(rs_raw)

        if both_empty:
            dot_cls = "dot-empty"
            status_tag = '<span class="tag tag-empty">no output</span>'
        elif match:
            dot_cls = "dot-pass"
            status_tag = '<span class="tag tag-pass">identical</span>'
        elif ws_match:
            dot_cls = "dot-ws"
            status_tag = '<span class="tag tag-ws">whitespace</span>'
        elif json_equal(py_raw, rs_raw):
            dot_cls = "dot-keyorder"
            status_tag = '<span class="tag tag-keyorder">key order</span>'
        else:
            dot_cls = "dot-diff"
            status_tag = '<span class="tag tag-diff">different</span>'

        def rc_badge(rc):
            if not rc:
                return ""
            cls = "rc-ok" if rc == "0" else "rc-err"
            return f'<span class="{cls}">exit {html.escape(rc)}</span>'

        rs_rc_badge = rc_badge(rs_rc)
        py_rc_badge = rc_badge(py_rc)

        has_stderr = py_err.strip() or rs_err.strip()
        stderr_section = ""
        if has_stderr:
            stderr_section = f'''<div class="stderr-row">
<div class="col">
<div class="col-label">Rust stderr</div>
<pre>{rs_err or "(empty)"}</pre>
</div>
<div class="col">
<div class="col-label">Python stderr</div>
<pre>{py_err or "(empty)"}</pre>
</div>
</div>'''

        is_json = cid.endswith("-json")
        fmt_btn = f'<button class="fmt-btn" onclick="toggleFmt(this)">pretty</button>' if is_json else ""

        comparison_html += f'''<details class="row">
<summary><span class="{dot_cls}"></span>{status_tag}<span class="row-label">{html.escape(label)}</span></summary>
<div class="row-body">
<div class="cmd-row">
<div class="col"><span class="cmd-prefix">$</span> {cmd_rs or "(not captured)"} {rs_rc_badge}</div>
<div class="col"><span class="cmd-prefix">$</span> {cmd_py or "(not captured)"} {py_rc_badge}</div>
</div>
<div class="output-row">{fmt_btn}
<div class="col">
<div class="col-label">Rust</div>
<pre>{rs_out or "(empty)"}</pre>
</div>
<div class="col">
<div class="col-label">Python</div>
<pre>{py_out or "(empty)"}</pre>
</div>
</div>
{stderr_section}
</div>
</details>
'''

    comp_stats = f"{n_total} commands"
    if n_identical:
        comp_stats += f" &mdash; {n_identical} identical"
    if n_ws_only:
        comp_stats += f", {n_ws_only} whitespace-only"
    if n_key_order:
        comp_stats += f", {n_key_order} key-order"
    if n_different:
        comp_stats += f", {n_different} different"
    if n_empty:
        comp_stats += f", {n_empty} empty"

    # --- Tab 2: Parity Tests ---
    parity_html = ""
    p_pass = p_fail = p_skip = p_total = 0
    if parity:
        p_pass = parity["pass"]
        p_fail = parity["fail"]
        p_skip = parity["skip"]
        p_total = parity["total"]

        for check in parity.get("checks", []):
            label = html.escape(check["label"])
            detail = html.escape(check.get("detail", ""))
            status = check["status"]
            dot_cls = {"pass": "dot-pass", "fail": "dot-fail", "skip": "dot-empty"}.get(status, "dot-empty")

            py_s = html.escape(check.get("py_sample", "").strip())
            rs_s = html.escape(check.get("rs_sample", "").strip())
            has_samples = py_s or rs_s

            if has_samples:
                parity_html += f'''<details class="row">
<summary><span class="{dot_cls}"></span><span class="row-label">{label}</span>{f'<span class="row-detail">{detail}</span>' if detail else ''}</summary>
<div class="row-body">
<div class="output-row">
<div class="col">
<div class="col-label">Rust</div>
<pre>{rs_s or "(empty)"}</pre>
</div>
<div class="col">
<div class="col-label">Python</div>
<pre>{py_s or "(empty)"}</pre>
</div>
</div>
</div>
</details>
'''
            else:
                detail_span = f'<span class="row-detail">{detail}</span>' if detail else ""
                parity_html += f'<div class="row-flat"><span class="{dot_cls}"></span><span class="row-label">{label}</span>{detail_span}</div>\n'

    parity_stats = f"{p_pass} pass, {p_fail} fail, {p_skip} skip" if parity else ""

    # --- Tab 3: Integration Tests ---
    int_total = summary["total"] if summary else 0
    int_passed = summary["passed"] if summary else 0
    int_failed = summary["failed"] if summary else 0

    int_html = ""
    if summary:
        for t in summary.get("tests", []):
            status = t["status"]
            name = html.escape(t["name"])
            if status == "PASS":
                dot_cls = "dot-pass"
            elif status == "SKIP":
                dot_cls = "dot-empty"
            else:
                dot_cls = "dot-fail"
            output = t.get("output", "").strip()
            if output:
                int_html += f'''<details class="row">
<summary><span class="{dot_cls}"></span><span class="row-label">{name}</span></summary>
<div class="row-body"><pre>{html.escape(output)}</pre></div>
</details>
'''
            else:
                int_html += f'<div class="row-flat"><span class="{dot_cls}"></span><span class="row-label">{name}</span></div>\n'

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>matrix-commander-ng</title>
<style>
*,*::before,*::after{{box-sizing:border-box}}
body{{
  margin:0;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  background:#000;
  color:#ededed;
  line-height:1.5;
  -webkit-font-smoothing:antialiased;
}}
.wrap{{max-width:1120px;margin:0 auto;padding:2rem 1.5rem}}

header{{
  display:flex;
  align-items:center;
  gap:1rem;
  padding-bottom:1.5rem;
  border-bottom:1px solid #222;
  margin-bottom:2rem;
}}
header img{{height:48px;filter:invert(1)}}
header h1{{font-size:1.25rem;font-weight:600;letter-spacing:-0.02em}}
header p{{font-size:.875rem;color:#888}}
header .links{{margin-left:auto;display:flex;gap:.75rem}}
header .links a{{
  color:#888;font-size:.8rem;text-decoration:none;
  padding:.35rem .65rem;border:1px solid #333;border-radius:6px;
  transition:border-color .15s,color .15s;
}}
header .links a:hover{{border-color:#666;color:#ededed}}

/* Tabs */
.tabs{{
  display:flex;
  gap:0;
  border-bottom:1px solid #222;
  margin-bottom:1.5rem;
}}
.tab{{
  padding:.6rem 1.25rem;
  font-size:.85rem;
  color:#666;
  cursor:pointer;
  border-bottom:2px solid transparent;
  transition:color .15s,border-color .15s;
  user-select:none;
}}
.tab:hover{{color:#ededed}}
.tab.active{{color:#ededed;border-bottom-color:#ededed}}
.tab .tab-stats{{
  font-size:.7rem;
  color:#444;
  margin-left:.5rem;
}}
.tab.active .tab-stats{{color:#666}}
.tab-panel{{display:none}}
.tab-panel.active{{display:block}}

/* Sections */
.section{{margin-bottom:2.5rem}}
.section-stats{{
  font-size:.8rem;
  font-weight:400;
  color:#666;
  margin-bottom:.75rem;
}}

/* Rows */
.row,.row-flat{{border-bottom:1px solid #111;font-size:.8rem}}
.row-flat{{padding:.5rem 0;display:flex;align-items:center;gap:.5rem}}
.row summary{{
  padding:.5rem 0;cursor:pointer;
  display:flex;align-items:center;gap:.5rem;list-style:none;
}}
.row summary::-webkit-details-marker{{display:none}}
.row summary::after{{
  content:"";display:inline-block;width:5px;height:5px;
  border-right:1.5px solid #444;border-bottom:1.5px solid #444;
  transform:rotate(-45deg);margin-left:auto;flex-shrink:0;
  transition:transform .15s;
}}
.row[open] summary::after{{transform:rotate(45deg)}}

.dot-pass,.dot-fail,.dot-diff,.dot-ws,.dot-keyorder,.dot-empty{{
  width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0;
}}
.dot-pass{{background:#3fb950}}
.dot-fail{{background:#f85149}}
.dot-diff{{background:#d29922}}
.dot-ws{{background:#58a6ff}}
.dot-keyorder{{background:#79c0ff}}
.dot-empty{{background:#333;border:1px solid #555}}

.tag{{
  font-size:.65rem;padding:.1rem .4rem;border-radius:3px;
  flex-shrink:0;
}}
.tag-pass{{color:#3fb950;background:#0a2e1a}}
.tag-ws{{color:#58a6ff;background:#0a1a2e}}
.tag-keyorder{{color:#79c0ff;background:#0a1a2e}}
.tag-diff{{color:#d29922;background:#2e1a0a}}
.tag-empty{{color:#666;background:#1a1a1a}}

.row-label{{color:#ededed}}
.row-detail{{color:#666;margin-left:.5rem;font-size:.75rem}}

.row-body{{padding:.75rem 0 .75rem 1.25rem}}

.cmd-row,.output-row,.stderr-row{{
  display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-bottom:.75rem;
}}
.cmd-row .col{{
  font-family:'SF Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace;
  font-size:.75rem;color:#888;padding:.4rem .6rem;
  background:#0a0a0a;border-radius:4px;border:1px solid #1a1a1a;
  overflow-x:auto;white-space:nowrap;
}}
.cmd-prefix{{color:#444;margin-right:.25rem}}
.col-label{{
  font-size:.7rem;font-weight:600;color:#666;
  text-transform:uppercase;letter-spacing:.05em;margin-bottom:.25rem;
}}
.output-row pre,.stderr-row pre,.row-body>pre{{
  font-family:'SF Mono',SFMono-Regular,Consolas,'Liberation Mono',Menlo,monospace;
  font-size:.75rem;line-height:1.6;
  background:#0a0a0a;border:1px solid #1a1a1a;border-radius:4px;
  padding:.6rem .75rem;margin:0;overflow-x:auto;
  white-space:pre-wrap;word-break:break-all;color:#c9d1d9;
  max-height:400px;overflow-y:auto;
}}
.stderr-row pre{{color:#f0883e}}
.rc-ok,.rc-err{{
  font-size:.65rem;padding:.1rem .4rem;border-radius:3px;margin-left:.5rem;
  font-family:'SF Mono',SFMono-Regular,Consolas,monospace;
}}
.rc-ok{{background:#0a2e1a;color:#3fb950}}
.rc-err{{background:#2e0a0a;color:#f85149}}
.fmt-btn{{
  position:absolute;top:.25rem;right:.25rem;z-index:1;
  font-size:.65rem;padding:.15rem .5rem;
  background:#1a1a1a;color:#888;border:1px solid #333;border-radius:3px;
  cursor:pointer;font-family:inherit;
  transition:border-color .15s,color .15s;
}}
.fmt-btn:hover{{border-color:#666;color:#ededed}}
.output-row{{position:relative}}

footer{{
  padding-top:1.5rem;border-top:1px solid #222;font-size:.75rem;color:#444;
}}
footer a{{color:#666;text-decoration:none}}
footer a:hover{{color:#888}}

@media(max-width:768px){{
  .cmd-row,.output-row,.stderr-row{{grid-template-columns:1fr}}
  .wrap{{padding:1rem}}
  .tabs{{overflow-x:auto}}
}}
</style>
</head>
<body>
<div class="wrap">

<header>
<img src="logo.svg" alt="">
<div>
<h1>matrix-commander-ng</h1>
<p>CLI Matrix client &mdash; Rust</p>
</div>
<div class="links">
<a href="https://github.com/longregen/matrix-commander-ng">Source</a>
<a href="comparison.json">JSON</a>
</div>
</header>

<div class="tabs">
<div class="tab active" data-tab="comparison">Output Comparison <span class="tab-stats">{n_total}</span></div>
<div class="tab" data-tab="parity">Parity Tests <span class="tab-stats">{p_total}</span></div>
<div class="tab" data-tab="integration">Integration Tests <span class="tab-stats">{int_total}</span></div>
</div>

<div id="comparison" class="tab-panel active">
<div class="section-stats">{comp_stats}</div>
{comparison_html}
</div>

<div id="parity" class="tab-panel">
<div class="section-stats">{parity_stats}</div>
{parity_html}
</div>

<div id="integration" class="tab-panel">
<div class="section-stats">{int_passed}/{int_total} passed</div>
{int_html}
</div>

<footer>
Generated {now} &mdash;
<a href="https://github.com/longregen/matrix-commander-ng">matrix-commander-ng</a>
</footer>

</div>
<script>
document.querySelectorAll('.tab').forEach(function(tab) {{
  tab.addEventListener('click', function() {{
    document.querySelectorAll('.tab').forEach(function(t) {{ t.classList.remove('active') }});
    document.querySelectorAll('.tab-panel').forEach(function(p) {{ p.classList.remove('active') }});
    tab.classList.add('active');
    document.getElementById(tab.dataset.tab).classList.add('active');
  }});
}});
function toggleFmt(btn) {{
  var row = btn.closest('.output-row');
  var pres = row.querySelectorAll('pre');
  var pretty = btn.textContent === 'pretty';
  pres.forEach(function(pre) {{
    if (pretty) {{
      if (!pre.dataset.raw) pre.dataset.raw = pre.textContent;
      try {{
        var lines = pre.dataset.raw.trim().split('\\n');
        var formatted = lines.map(function(line) {{
          try {{ return JSON.stringify(JSON.parse(line), null, 2); }}
          catch(e) {{ return line; }}
        }}).join('\\n');
        pre.textContent = formatted;
      }} catch(e) {{}}
    }} else {{
      if (pre.dataset.raw) pre.textContent = pre.dataset.raw;
    }}
  }});
  btn.textContent = pretty ? 'raw' : 'pretty';
}}
</script>
</body>
</html>"""

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(page)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--comparison", default=None)
    parser.add_argument("--parity", default=None)
    parser.add_argument("--summary", default=None)
    args = parser.parse_args()
    generate(args.output_dir, args.comparison, args.parity, args.summary)
