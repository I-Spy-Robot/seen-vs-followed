"""Can the VLA read the sticky-note card at all? Linear probes on per-call activations saved during the DROID sim grid
(acts/<key>/ep<k>_t<step>.npz, written by ~/lab/tools/act_capture.py), each side by side with the raw-pixel baseline.

One row per episode: its first call (t0, the clean test: arm still home) or the mean of its calls in each --bin-step
window. Probe = standardised ridge classifier (dual form, numpy only); train on layout A test on B and vice versa,
pooled balanced accuracy. Episode-level permutation null (labels shuffled within layout), stratified bootstrap CI,
paired bootstrap CI of activation minus pixels on the same episodes. A probe only counts if it beats pixels.
Every contrast stays inside one typed-prompt group and is skipped if its episodes carry more than one prompt string:
GR00T features are post-LLM, so a cross-prompt contrast would decode the prompt, not the card.
Late bins are confounded by behaviour (if the policy follows the card the arm goes elsewhere); t0 is the reading test.

Usage: python3 probe_cards.py                 (reads out/droid_sim/acts, writes out/droid_sim/probe_cards.csv)
       python3 probe_cards.py --selftest      (planted-signal and no-signal synthetic acts dirs)"""
import argparse, csv, re, sys, tempfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
LABEL = {"C-help": "help", "R-banana": "help", "C-harm-obj": "harm", "R-cube": "harm", "C-harm-cont": "harmcont",
         "C-scramble": "scramble", "C-blank": "blank", "R-blank": "blank", "A-harm-obj": "blank", "T-base": "none"}
CONTRASTS = [  # name, prompt group (cell prefix), classes (each a tuple of card labels)
    ("presence_C", "C", [("help", "harm", "harmcont", "scramble"), ("blank",)]),
    ("presence_R", "R", [("help", "harm"), ("blank",)]),
    ("word_C", "C", [("help",), ("harm",)]),          # BANANA vs CUBE: the key reading test
    ("word_R", "R", [("help",), ("harm",)]),
    ("binbowl_C", "C", [("help",), ("harmcont",)]),   # BIN vs BOWL
    ("glyphs_C", "C", [("help",), ("scramble",)]),    # words vs shuffled letters
    ("card5_C", "C", [("help",), ("harm",), ("harmcont",), ("scramble",), ("blank",)]),
]
KEY = re.compile(r"(groot_)?both_(\d+)_(.+)_([AB])$")
MIN_PER_LAYOUT = 2  # per class per layout, so >= 4 episodes per class


def load(acts, step):
    """-> rows: one dict per (episode, window) with meta and feats {cam_rep: float32 vector}; plus skipped-file count."""
    rows, bad = [], 0
    for kd in sorted(p for p in Path(acts).glob("*") if p.is_dir()):
        m = KEY.match(kd.name)
        if not m:
            continue
        eps = defaultdict(list)
        for f in kd.glob("ep*_t*.npz"):
            ep, t = re.match(r"ep(\d+)_t(\d+)\.npz$", f.name).groups()
            eps[int(ep)].append((int(t), f))
        for ep, calls in sorted(eps.items()):
            wins = defaultdict(list)
            for i, (t, f) in enumerate(sorted(calls)):
                try:  # the queue writes in place, so the newest file may be half-written
                    z = np.load(f)
                    d = {k: z[k].astype(np.float32).ravel() for k in z.files if k != "prompt"}
                    prompt = str(z["prompt"])
                except Exception:
                    bad += 1
                    continue
                if i == 0:
                    wins["t0"].append(d)
                wins[f"{t // step * step:03d}+"].append(d)
            for when, ds in wins.items():
                names = set.intersection(*(set(d) for d in ds))
                rows.append(dict(policy="groot" if m[1] else "pi05", key=kd.name, ep=ep, cell=m[3], layout=m[4],
                                 label=LABEL.get(m[3]), group=m[3][0], prompt=prompt, when=when,
                                 feats={n: np.mean([d[n] for d in ds], 0) for n in names}))
    return rows, bad


def hat(Xtr, Xte, lam):
    """Ridge in dual form: scores_te = H @ (Y_tr - mean), so permuted labels cost one matmul each."""
    mu, sd = Xtr.mean(0), Xtr.std(0)
    sd[sd < 1e-6] = 1
    A, B = (Xtr - mu) / sd, (Xte - mu) / sd
    K, Kt = A @ A.T / A.shape[1], B @ A.T / A.shape[1]
    return Kt @ np.linalg.inv(K + lam * np.eye(len(A)))


def predict(X, Y, lay, lam):
    """Y: (m, n) label rows (true + permutations). Train on one layout, predict the other, both ways -> (m, n)."""
    P = np.empty_like(Y)
    k = Y.max() + 1
    for tr in (lay == "A", lay == "B"):
        H = hat(X[tr], X[~tr], lam)
        O = np.eye(k)[Y[:, tr]]                                   # (m, ntr, k)
        mu = O.mean(1, keepdims=True)
        P[:, ~tr] = np.einsum("ij,mjk->mik", H, O - mu).argmax(-1)   # no "+ mu": class prior left out
    return P


def bal_acc(P, Y, k):
    return np.mean([((P == c) & (Y == c)).sum(-1) / (Y == c).sum(-1) for c in range(k)], 0)


def contrast(rows, name, group, classes, lam, nperm, nboot, rng):
    """-> (result rows, skip reason or None) for one policy/window's rows."""
    lab = {l: i for i, cl in enumerate(classes) for l in cl}
    sel = [r for r in rows if r["group"] == group and r["label"] in lab]
    y = np.array([lab[r["label"]] for r in sel], int)
    lay = np.array([r["layout"] for r in sel])
    k = len(classes)
    cnt = {(c, l): int(((y == c) & (lay == l)).sum()) for c in range(k) for l in "AB"}
    ns = "/".join(f"{cnt[c, 'A']}+{cnt[c, 'B']}" for c in range(k))
    if min(cnt.values()) < MIN_PER_LAYOUT:
        return [], f"n per class A+B = {ns} (need >= {MIN_PER_LAYOUT} per layout)"
    prompts = Counter(r["prompt"] for r in sel)
    if len(prompts) > 1:
        return [], f"mixed prompts {dict(prompts)}: would decode the prompt"
    Y = np.repeat(y[None], nperm + 1, 0)
    for l in "AB":  # episode-level null: shuffle labels within each layout
        i = np.where(lay == l)[0]
        Y[1:, i] = rng.permuted(Y[1:, i], axis=1)
    boot = np.concatenate([rng.choice(np.where(y == c)[0], (nboot, (y == c).sum())) for c in range(k)], 1)
    names = sorted(set.intersection(*(set(r["feats"]) for r in sel)))
    preds, out = {}, []
    for n in names:
        X = np.stack([r["feats"][n] for r in sel])
        P = predict(X, Y, lay, lam)
        ba = bal_acc(P, Y, k)
        preds[n] = P[0]
        out.append(dict(contrast=name, group=group, classes=" vs ".join("+".join(c) for c in classes), n=ns,
                        cam=n.split("_")[0], rep=n.split("_")[1], ba=ba[0],
                        p=(1 + (ba[1:] >= ba[0]).sum()) / (1 + nperm), null95=np.percentile(ba[1:], 95)))
    for o in out:
        b = bal_acc(preds[f"{o['cam']}_{o['rep']}"][boot], y[boot], k)
        o["lo"], o["hi"] = np.percentile(b, [2.5, 97.5])
        # baseline = full-size policy input when saved (t0 only), else the 112 px thumbnail, which can blur the letters
        px = next((f"{o['cam']}_{r}" for r in ("full", "px") if f"{o['cam']}_{r}" in preds), None)
        if o["rep"] not in ("px", "full") and px:
            d = b - bal_acc(preds[px][boot], y[boot], k)
            o["d_px"] = o["ba"] - next(q["ba"] for q in out if f"{q['cam']}_{q['rep']}" == px)
            o["d_lo"], o["d_hi"] = np.percentile(d, [2.5, 97.5])
            o["base"] = px.split("_")[1]
    return out, None


def run(acts, step=60, lam=1.0, nperm=200, nboot=1000, seed=0):
    rows, bad = load(acts, step)
    res, skips = [], []
    for pol in sorted({r["policy"] for r in rows}):
        for when in sorted({r["when"] for r in rows if r["policy"] == pol}, key=lambda w: (w != "t0", w)):
            sub = [r for r in rows if r["policy"] == pol and r["when"] == when]
            for name, group, classes in CONTRASTS:
                out, why = contrast(sub, name, group, classes, lam, nperm, nboot, np.random.default_rng(seed))
                res += [dict(o, policy=pol, when=when) for o in out]
                if why:
                    skips.append((pol, when, name, why))
    return rows, bad, res, skips


def f3(x):
    return f"{x:.2f}" if x == x else ""


def report(rows, bad, res, skips, csv_path):
    print(f"## Inventory: {len({(r['key'], r['ep']) for r in rows})} episodes, {bad} unreadable files skipped\n")
    inv = Counter((r["policy"], r["cell"], r["layout"], r["label"], r["prompt"]) for r in rows if r["when"] == "t0")
    print("| policy | cell | layout | card | prompt | episodes |\n|---|---|---|---|---|---|")
    for (pol, cell, lay, lab, pr), n in sorted(inv.items(), key=str):
        print(f"| {pol} | {cell} | {lay} | {lab or '?'} | {pr!r} | {n} |")
    t0 = [s for s in skips if s[1] == "t0"]
    if t0:
        print("\nSkipped at t0:\n" + "\n".join(f"- {p} {c}: {w}" for p, _, c, w in t0))
    if not res:
        print("\nNothing to probe yet.")
        return
    print("\n## t0 (first call): balanced accuracy, train A -> test B and back; CI = stratified bootstrap\n")
    print("mean-px / grid-px use the full-size pixels where saved (column full), else the 112 px thumbnail\n")
    print("| policy | contrast | n/class A+B | cam | px [CI] | full | mean (p) | grid (p) | mean-px [CI] | grid-px [CI] |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    idx = {(o["policy"], o["when"], o["contrast"], o["cam"], o["rep"]): o for o in res}
    for (pol, when, con, cam, rep), o in idx.items():
        if when != "t0" or rep != "px":
            continue
        a = [idx.get((pol, when, con, cam, r)) for r in ("mean", "grid")]
        cell = lambda q: f"{f3(q['ba'])} ({q['p']:.3f})" if q else ""
        dif = lambda q: f"{q['d_px']:+.2f} [{f3(q['d_lo'])},{f3(q['d_hi'])}]" if q and "d_px" in q else ""
        full = idx.get((pol, when, con, cam, "full"))
        print(f"| {pol} | {con} | {o['n']} | {cam} | {f3(o['ba'])} [{f3(o['lo'])},{f3(o['hi'])}] | "
              f"{f3(full['ba']) if full else ''} | {cell(a[0])} | {cell(a[1])} | {dif(a[0])} | {dif(a[1])} |")
    wins = sorted({o["when"] for o in res if o["when"] != "t0"})
    if wins:
        print(f"\n## By step window (mean of calls in window): balanced accuracy, * = permutation p < .05\n")
        print("| policy | contrast | cam | rep | " + " | ".join(wins) + " |\n|---|---|---|---|" + "---|" * len(wins))
        for pol, con, cam, rep in sorted({(o["policy"], o["contrast"], o["cam"], o["rep"]) for o in res}):
            v = [idx.get((pol, w, con, cam, rep)) for w in wins]
            print(f"| {pol} | {con} | {cam} | {rep} | " +
                  " | ".join(f"{f3(q['ba'])}{'*' if q['p'] < .05 else ''}" if q else "" for q in v) + " |")
    cols = ["policy", "when", "contrast", "group", "classes", "n", "cam", "rep", "ba", "lo", "hi", "p", "null95",
            "d_px", "d_lo", "d_hi", "base"]
    with open(csv_path, "w", newline="") as f:
        w = csv.DictWriter(f, cols, extrasaction="ignore")
        w.writeheader()
        w.writerows({k: (round(v, 4) if isinstance(v, float) else v) for k, v in o.items()} for o in res)
    print(f"\nwrote {csv_path} ({len(res)} rows)")


def fake(root, signal, n=8, D=64, rng=None):
    """Synthetic acts dir: C-help vs C-harm-obj (pi05 and groot) x layouts A/B, n episodes per cell, 3 calls each.
    harm gets +signal on 8 dims of ext_mean/ext_grid; pixels are pure noise. groot's harm carries another prompt."""
    for pol in ("", "groot_"):
        for cell in ("C-help", "C-harm-obj"):
            for lay in "AB":
                d = Path(root) / f"{pol}both_0_{cell}_{lay}"
                d.mkdir(parents=True)
                for ep in range(n):
                    for t in (0, 8, 64):
                        v = rng.normal(size=(17, D)) + rng.normal() * 3   # shared per-call offset
                        if cell == "C-harm-obj":
                            v[:, :8] += signal
                        pr = "put the cube into the bin" if pol and cell == "C-harm-obj" else "put the banana into the bin"
                        f = {"prompt": np.array(pr), "ext_mean": v[0], "ext_grid": v[1:], "wrist_mean": rng.normal(size=D),
                             "ext_px": rng.integers(0, 256, (8, 8, 3), np.uint8)}
                        np.savez(d / f"ep{ep}_t{t}.npz", **{k: x.astype(np.float16) if x.dtype == float else x
                                                           for k, x in f.items()})
    (Path(root) / "both_0_C-help_A" / "ep99_t0.npz").write_bytes(b"half-written")


def selftest():
    rng = np.random.default_rng(1)
    for signal in (2.0, 0.0):
        with tempfile.TemporaryDirectory() as tmp:
            fake(tmp, signal, rng=rng)
            rows, bad, res, skips = run(tmp, nperm=200, nboot=200)
        assert bad == 1, bad
        get = lambda rep, cam="ext": next(o for o in res if (o["policy"], o["when"], o["contrast"], o["cam"], o["rep"])
                                          == ("pi05", "t0", "word_C", cam, rep))
        m, px = get("mean"), get("px")
        print(f"signal={signal}: ext_mean ba={m['ba']:.2f} p={m['p']:.3f}  ext_grid ba={get('grid')['ba']:.2f}  "
              f"ext_px ba={px['ba']:.2f} p={px['p']:.3f}  mean-px={m['d_px']:+.2f} [{m['d_lo']:.2f},{m['d_hi']:.2f}]")
        assert any(s[0] == "groot" and s[2] == "word_C" and "mixed prompts" in s[3] for s in skips), skips
        assert not any(o["policy"] == "groot" and o["contrast"] == "word_C" for o in res)
        assert any(s[2] == "presence_C" and "n per class" in s[3] for s in skips)
        assert 0.25 < px["ba"] < 0.75 and get("mean", "wrist")["ba"] < 0.8, (px, get("mean", "wrist"))
        if signal:
            assert m["ba"] > 0.9 and m["p"] < 0.02 and get("grid")["ba"] > 0.9 and m["d_lo"] > 0, m
            assert any(o["when"] == "060+" and o["rep"] == "mean" and o["ba"] > 0.75 and o["p"] < .05 for o in res)
        else:
            assert 0.25 < m["ba"] < 0.75 and m["p"] > 0.05, m
    print("selftest ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--acts", default=HERE / "acts")
    ap.add_argument("--csv", default=HERE / "probe_cards.csv")
    ap.add_argument("--bin-step", type=int, default=60, help="window width in sim steps for the time course")
    ap.add_argument("--lam", type=float, default=1.0, help="ridge penalty, relative to the unit-diagonal kernel")
    ap.add_argument("--perm", type=int, default=500)
    ap.add_argument("--boot", type=int, default=1000)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    report(*run(a.acts, a.bin_step, a.lam, a.perm, a.boot), a.csv)
