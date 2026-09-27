# Copyright IBM Corp. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

"""Aggregate the benchmark result JSONs into markdown tables for REPORT.md.

Usage: python aggregate.py <results_dir>
"""

import glob
import json
import os
import sys


def fnum(x, nd=4):
    if isinstance(x, (int, float)):
        return f"{x:.{nd}f}"
    return str(x)[:40]


def load(results_dir):
    out = {}
    for path in glob.glob(os.path.join(results_dir, "*.json")):
        d = json.load(open(path))
        slug = d["model"].replace("ibm-granite/", "").replace("/", "_")
        out[(slug, d["arm"])] = d
    return out


def size_of(slug):
    for s in ("3b", "8b", "30b"):
        if s in slug:
            return s
    return "?"


def val(level, key):
    """Extract the score value from a call_stats dict."""
    v = level.get(key)
    if isinstance(v, dict) and "value" in v:
        return v["value"]
    return v


def main():
    results_dir = sys.argv[1]
    data = load(results_dir)
    lines = []
    for size in ("3b", "8b", "30b"):
        lines.append(f"### granite-4.1-{size}\n")
        arms = {}
        for (slug, arm), d in data.items():
            if "switch" in slug:
                continue
            if size_of(slug) == size and arm in ("before", "middle", "after"):
                arms[arm] = d
        if not arms:
            lines.append(f"<no {size} results yet>\n")
            continue

        def row(label, fn):
            cells = [label]
            for arm in ("before", "middle", "after", "switch"):
                d = arms.get(arm)
                if d is None:
                    cells.append("—" if arm != "switch" else f"switch-{size}: —")
                    continue
                cells.append(fn(d["levels"]))
            return "| " + " | ".join(cells) + " |"

        hdr = "| Metric | before (main) | middle (no repair) | after (PR #1685) | switch |"
        sep = "|---|---|---|---|---|"
        if "switch" in {a for (_, a) in data}:
            sw = next((d for (s, a), d in data.items() if a == "switch" and size_of(s) == size), None)
            if sw:
                arms["switch"] = sw

        lines.append(hdr)
        lines.append(sep)

        def l0(d):
            lv = d.get("L0", {})
            return f"fr {fnum(val(lv, 'french'))} / bu {fnum(val(lv, 'bullets'))}"

        def l1(d):
            lv = d.get("L1", {})
            return f"certain {fnum(val(lv, 'certain'))} / hedged {fnum(val(lv, 'hedged'))}"

        def l2(d):
            lv = d.get("L2", {})
            return (
                f"fr {fnum(val(lv, 'french'))} / bu {fnum(val(lv, 'bullets'))} "
                f"/ cert {fnum(val(lv, 'certainty'))}"
            )

        def l3(d):
            lv = d.get("L3", {})
            ans = val(lv, "answerability")
            if isinstance(ans, dict):
                ans = ans.get("value", ans)
            gr = val(lv, "grounded_check")
            gen = lv.get("generated", {})
            return f"ans {str(ans)[:12]} / grounded {fnum(gr)} / gen {gen.get('latency_s')}s,{gen.get('completion_tokens')}t"

        def l4(d):
            lv = d.get("L4", {})
            scores = [a["score"] for a in lv.get("attempts", [])]
            toks = [a.get("gen_tokens", 0) for a in lv.get("attempts", [])]
            return (
                f"passed={lv.get('passed')} n={len(scores)} "
                f"scores=[{', '.join(fnum(s, 3) for s in scores)}] "
                f"gen_toks={sum(t for t in toks if t)}"
            )

        lines.append(row("**L0 LoRA sanity** (must be arm-invariant)", l0))
        lines.append(row("**L1 certainty** (confident > hedged)", l1))
        lines.append(row("**L2 french / bullets / certainty**", l2))
        lines.append(row("**L3 RAG chain**", l3))
        lines.append(row("**L4 retry loop**", l4))
        lines.append("")

        # performance: per-level wall time
        lines.append(f"Per-level wall time (s):")
        lines.append("")
        lines.append(hdr)
        lines.append(sep)

        def perf(d):
            t = d.get("timings", {}) if "timings" in d else {}
            lv = d["levels"]
            parts = []
            for k in ("L0", "L1", "L2", "L3", "L4"):
                if k in lv:
                    parts.append(f"{k} {lv[k].get('timings', {}).get(k, '?')}")
            return " / ".join(parts)

        for arm in ("before", "middle", "after", "switch"):
            if arm in arms:
                lines.append(row(f"**{arm}**", lambda d, a=arm: perf(arms[a])))
        lines.append("")

    print("\n".join(lines))


if __name__ == "__main__":
    main()
