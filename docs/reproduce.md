# D. Reproduce

| Level | Needs | What it reproduces |
|---|---|---|
| 1. Tables | Python 3.9+, no packages | Every table in [Results](results.md) from `data/droid_episodes.csv` |
| 2. Statistics | the same | Power table and Wilson bounds (`seen_vs_followed.stats`) |
| 3. Backbone read test | one GPU, `transformers` ≥ 5, the two backbones from the Hugging Face Hub | `droid/backbone_read.py` (word recall of each policy's own backbone on the cards) |
| 4. Scenes | Isaac Sim 5, NVIDIA `sim-evals` | `droid/build_scenes.py` builds the card scenes; `droid/render_scene.py` renders them at rest |
| 5. Policy runs | Level 4 plus a policy server per model | Not included in this prototype (the servers hold machine-specific paths) |

```
pip install -e .[test]
python -m pytest
python -m seen_vs_followed.report data/droid_episodes.csv
python scripts/gen_docs.py --check
```
