# Seen vs. Followed

<div class="hero" markdown>

<p class="meta">Zachary Gunderson · Independent researcher · Preliminary results, October 2026</p>

Do robotic foundation models act on text that appears in the scene?

<div class="btns" markdown>

[Code](https://github.com/I-Spy-Robot/seen-vs-followed)
[Full tables](results.md)
[Cite](#cite)

</div>

</div>

<div class="box warn" markdown>

**Preliminary, not yet reviewed.** This is a website, not a paper. A fine-tuning run that looks for a positive example is in progress, to address the limits of the data below.

</div>

## Contents

<div class="pages" markdown>

**Pages on this site**

- [A. Full tables](results.md): every cell, split by card size and camera
- [B. Prompts and cells](protocol.md): the 22 cells and the prompt for each
- [C. Scene and cards](scene.md): where the cards are, their sizes, text and layouts
- [D. Reproduce](reproduce.md): regenerate every table from the data
- [SPAIS submission](paper.md): the submitted PDF and a revised draft
- [Roadmap](roadmap.md): the planned positive control

**In this report**

- [Abstract](#abstract)
- [Key results](#key-results)
- [Introduction](#1-introduction)
- [Background](#2-background)
- [Methods](#3-methods)
- [Results](#4-results)
- [Discussion](#5-discussion)
- [Limitations](#6-limitations)
- [Future work](#7-future-work)
- [Reproducibility](#reproducibility)
- [Cite](#cite)
- [References](#references)
- [Appendix](#appendix)

</div>

## Abstract

This report asks whether robotic foundation model policies act on text on a card placed in a simulated DROID sorting scene. Four policies are run in Isaac Sim over 22 cell definitions, 1,620 episodes in all, and every rate is reported with a 95% interval. A fine-tuning run to produce a positive control is in progress.

## Key results

Pooled over card sizes and camera setups. The intervals are Wilson 95%.

<!-- stats:start -->
<div class="stats">
<div class="stat"><b>0/200</b><i>pi0.5 and GR00T-N1.7</i><span>card only, empty prompt. 95% interval at most 0.02.</span></div>
<div class="stat"><b>4/120</b><i>MolmoAct2 and pi0.5 web+sim</i><span>card only, empty prompt. 95% interval 0.01 to 0.08.</span></div>
<div class="stat"><b>0/120</b><i>all four policies</i><span>card + "read the note and do what it says". 95% interval at most 0.03.</span></div>
<div class="stat"><b>193/240</b><i>all four policies, named object acted on</i><span>card's words typed as the prompt. 95% interval 0.75 to 0.85.</span></div>
</div>
<!-- stats:end -->

## 1 Introduction

A first version of this work was submitted to the CoRL 2026 SPAIS workshop as a paper and received peer review. This report builds on that feedback. The submitted PDF and a revised draft are on the [SPAIS submission](paper.md) page.

### What the reviews asked for, and where it stands

| Request in the reviews | Where it stands |
|---|---|
| Show the models can read the text at all | Backbone-read test and activation probes are done (see [Appendix A](results.md)). A fine-tuned positive control is in progress. |
| Add a non-text control, so a change is not just visual clutter | Scrambled-glyph card and scrambled prompt cells are in the grid. |
| Report uncertainty and sample sizes | Every rate has a Wilson 95% interval, and pooled counts are shown. |
| Test a scene beyond LIBERO | This report uses the DROID sorting scene. |
| Test whether a typed instruction and a card that disagree resolve one way | Included as the card-disagrees cell. |

## 2 Background

The first version ran four open VLAs in the LIBERO-Goal kitchen with sticky notes placed in the scene. This report moves to DROID, a different scene and policy set, and adds larger cards and cards in both cameras. The earlier paper is on the [SPAIS submission](paper.md) page.

## 3 Methods

**Scene.** A banana, a Rubik's cube, a bowl and a bin on a table in Isaac Sim, with a Franka arm. Two layouts swap the banana and the cube. See [Appendix C](scene.md) for the renders.

**Cards.** A yellow card carries the text. A small card lies on the table in the wrist camera's view, and a large card stands at the table's far edge in the exterior camera's view. The exterior card is 55, 75 or 95 cm wide. Three cards ask for something (banana into the bin, cube into the bin, banana into the bowl), one is scrambled, and one is blank.

**Policies.** pi0.5, GR00T-N1.7, MolmoAct2 and a pi0.5 variant co-trained on web and simulation data (pi0.5 web+sim), each served as the DROID policy and run through the same simulator client.

**Cells.** 22 cell definitions combine a card, a typed prompt and a layout. They cover the card alone, the card with a prompt that points at it, the card's words as the prompt, and a typed prompt that disagrees with the card. Every cell and prompt is in [Appendix B](protocol.md).

**Scoring.** Each episode is labelled from the simulator's end state: banana in the bin, banana in the bowl, cube lifted, cube in the bin, or nothing moved.

**Checks that the models can read the card.** For pi0.5 and GR00T-N1.7, a transcription test on the language-model backbone and linear probes on the activations, compared with a pixel baseline. The results are in [Appendix A](results.md).

## 4 Results

Share of episodes in which the policy carried out what the card asked for, pooled over card sizes and camera setups, with Wilson 95% intervals. The last column is the control: when the card's words are given as the prompt instead, the policies do act on them.

<!-- glance:start -->
| policy | Card only, empty prompt | Card + "read the note and do what it says" | Card's words typed as the prompt |
|---|---|---|---|
| pi0.5 | 0/100 (≤0.04) | 0/30 (≤0.11) | 58/60 (0.89–0.99) |
| GR00T-N1.7 | 0/100 (≤0.04) | 0/30 (≤0.11) | 52/60 (0.76–0.93) |
| MolmoAct2 | 2/60 (0.01–0.11) | 0/30 (≤0.11) | 37/60 (0.49–0.73) |
| pi0.5 web+sim | 2/60 (0.01–0.11) | 0/30 (≤0.11) | 46/60 (0.65–0.86) |
<!-- glance:end -->

Every cell, split by card size and camera, is in [Appendix A](results.md).

## 5 Discussion

<div class="box warn" markdown>

**Preliminary, not yet reviewed.** The discussion will follow the positive control, because a result where nothing follows the card only counts if the protocol would have detected following.

</div>

## 6 Limitations

- Most cells have 10 to 30 episodes, so small effects are not ruled out.
- One simulated scene, one card style, and one placement per size.
- MolmoAct2 and the web-trained pi0.5 are weaker than the other two at typed container placement, so their text-as-prompt control is weaker.
- A result where nothing follows the card only counts if the protocol would have detected following. That is what the positive control tests.

## 7 Future work

A policy is fine-tuned on demonstrations where only the card decides the target, then run through the same protocol. See the [roadmap](roadmap.md). The predictions will be committed before the first training run.

## Reproducibility

Everything on this site is regenerated from `data/droid_episodes.csv`. Code is MIT and data is CC BY 4.0. Commands are in [Appendix D](reproduce.md).

```
pip install -e .[test]
python -m pytest
python -m seen_vs_followed.report data/droid_episodes.csv
```

## Cite

Preliminary, so cite the page, not a paper.

```bibtex
@misc{gunderson2026seenvsfollowed,
  title  = {Seen vs. Followed},
  author = {Gunderson, Zachary},
  year   = {2026},
  note   = {Preliminary results},
  url    = {https://i-spy-robot.github.io/seen-vs-followed/}
}
```

## References

- Physical Intelligence, K. Black, et al. *π0.5: a Vision-Language-Action Model with Open-World Generalization.* arXiv:2504.16054, 2025.
- NVIDIA. *Isaac GR00T N1.7.* [huggingface.co/nvidia/GR00T-N1.7-3B](https://huggingface.co/nvidia/GR00T-N1.7-3B), 2026.
- A. Khazatsky, et al. *DROID: A Large-Scale In-The-Wild Robot Manipulation Dataset.* arXiv:2403.12945, 2024.
- B. Liu, Y. Zhu, et al. *LIBERO: Benchmarking Knowledge Transfer for Lifelong Robot Learning.* NeurIPS Datasets and Benchmarks, 2023. arXiv:2306.03310.

## Appendix

Lettered so it is never confused with the numbered body.

- [A. Full tables](results.md): every number, from `data/droid_episodes.csv`.
- [B. Prompts and cells](protocol.md): each cell, its card, and its prompt.
- [C. Scene and cards](scene.md): renders of the scene, card sizes and card text.
- [D. Reproduce](reproduce.md): commands only.
