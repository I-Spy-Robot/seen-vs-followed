# Seen vs. Followed

**Status: preliminary work. A positive control is the next step; see `docs/roadmap.md`.**

A protocol for testing whether vision-language-action (VLA) models act on text that appears in the scene, with a DROID instance
(pi0.5, GR00T-N1.7, MolmoAct2, pi0.5 web+sim) in Isaac Sim.

Results so far are tables of counts with confidence intervals, in `docs/results.md`. No summary claim is made yet.

## Layout

| Path | Contents |
|---|---|
| `src/seen_vs_followed/` | cell definitions, episode labelling, statistics, report generator (standard library only) |
| `data/droid_episodes.csv` | one row per episode: policy, card condition, cell, outcome (1,620 episodes) |
| `data/probe_cards.csv`, `data/backbone_read/` | activation-probe and backbone-read results |
| `droid/` | scene builder, renderer, backbone-read and probe scripts, card textures |
| `docs/`, `mkdocs.yml` | project page; `protocol.md` and `results.md` are generated |
| `tests/` | unit tests and a regression test on the released data |

## Quickstart

```
pip install -e .[test]
python -m pytest
python -m seen_vs_followed.report data/droid_episodes.csv
```

See `docs/reproduce.md` for what each level needs.

## Paper

The first version was submitted to the CoRL 2026 SPAIS workshop and received peer review. The submitted PDF and a revised draft are in [`docs/assets/`](docs/assets/). They cover the LIBERO-Goal experiments; the DROID results here are newer.

## Not included yet

Policy servers and run launchers (they hold machine-specific paths), episode videos, raw activations.

## License and citation

Code: MIT (`LICENSE`). Data under `data/`: CC BY 4.0 (`DATA_LICENSE`). Renders of the Isaac Sim / DROID scene are not included until their asset terms are checked.
Citation: not yet available. See `docs/assets/` for the submitted PDF.
