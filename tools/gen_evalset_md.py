"""Generate EVALSET.md from the case manifests."""
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
rows = []
for d in sorted((root / "evalset").iterdir()):
    m = d / "manifest.json"
    if not m.is_file():
        continue
    data = json.loads(m.read_text())
    prov = data.get("provenance", {})
    note = prov.get("note", "").replace("|", "/")
    n_bugs = len(data.get("bugs", []))
    rows.append((d.name, prov.get("source", "?"),
                 prov.get("model_cutoff_status", "?"), n_bugs, note))

lines = [
    "# Evalset catalog",
    "",
    f"{len(rows)} cases, generated from each case's `manifest.json` "
    "(`python tools/gen_evalset_md.py .` regenerates this file). "
    "`cutoff` is the case's position relative to the reviewer model's "
    "Jan-2026 training cutoff: `post` = merged after (contamination-clean), "
    "`pre` = contamination control, `na` = synthetic/private (never public).",
    "",
    "| case | source | cutoff | bugs | what it tests |",
    "|---|---|---|---|---|",
]
for name, src, cut, n, note in rows:
    lines.append(f"| `{name}` | {src} | {cut} | {n} | {note} |")
out = root / "EVALSET.md"
out.write_text("\n".join(lines) + "\n")
print(f"wrote {out} ({len(rows)} cases)")
