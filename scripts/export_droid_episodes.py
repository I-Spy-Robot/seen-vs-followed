"""Tidy one-row-per-episode table from the scorer's episodes.csv. Drops run directories and video paths (they hold machine names).
Usage: python scripts/export_droid_episodes.py <episodes.csv> data/droid_episodes.csv"""
import csv
import re
import sys

sys.path.insert(0, "src")
from seen_vs_followed.cells import CELLS  # noqa: E402

PAT = re.compile(r"^(?:(groot|molmo|pi05web)_)?(?:(both)(\d*)_)?(.+)$")
FIELDS = ["policy", "cards", "ext_cm", "cell", "block", "layout", "seed", "episode", "card", "prompt", "outcome"]


def main(src, dst):
    out, bad = [], 0
    for r in csv.DictReader(open(src, encoding="utf-8")):
        pol, both, cm, name = PAT.match(r["cell"]).groups()
        c = CELLS[name]
        prompt = "" if r["prompt"] == "<empty>" else r["prompt"]
        bad += prompt != c["prompt"]
        out.append(dict(policy=pol or "pi05", cards="both" if both else "wrist", ext_cm=(int(cm) if cm else 55) if both else 0,
                        cell=name, block=c["block"], layout=r["layout"], seed=r["seed"], episode=r["episode"],
                        card=c["card"], prompt=prompt, outcome=r["outcome"]))
    assert not bad, f"{bad} episodes whose prompt differs from cells.py"
    with open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(out)
    print(f"{len(out)} episodes -> {dst}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
