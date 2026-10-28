# Seen vs. Followed

Do vision-language-action (VLA) models act on text that appears in the scene? This site reports simulation experiments on a DROID sorting task in Isaac Sim, where a note placed in the scene names an object or a place.

!!! info "Preliminary work"
    This is a website, not a paper. The results are the current state of an ongoing project. A fine-tuning run that looks for a positive example is in progress, to address the limits of the data below.

## Contents

<div class="pages" markdown>

**Pages on this site**

- [Results](results.md): every cell, split by card size and camera
- [Scene](scene.md): where the cards are, their sizes, text and layouts
- [Protocol](protocol.md): the 22 cells and the prompt for each
- [SPAIS submission](paper.md): the submitted PDF and a revised draft
- [Roadmap](roadmap.md): the planned positive control
- [Reproduce](reproduce.md): regenerate every table from the data

**On this page**

- [Where this comes from](#where-this-comes-from)
- [What the reviews asked for, and where it stands](#what-the-reviews-asked-for-and-where-it-stands)
- [Results so far](#results-so-far)
- [Limits of the current data](#limits-of-the-current-data)
- [Next: a positive control](#next-a-positive-control)
- [Code and data](#code-and-data)

</div>

## Where this comes from

A first version of this work was submitted to the CoRL 2026 SPAIS workshop as a paper and received peer review. This site builds on that feedback. The submitted PDF and a revised draft are on the [SPAIS submission](paper.md) page.

## What the reviews asked for, and where it stands

| Request in the reviews | Where it stands |
|---|---|
| Show the models can read the text at all | Backbone-read test and activation probes are done (see [Results](results.md)). A fine-tuned positive control is in progress. |
| Add a non-text control, so a change is not just visual clutter | Scrambled-glyph card and scrambled prompt cells are in the grid. |
| Report uncertainty and sample sizes | Every rate has a Wilson 95% interval, and pooled counts are shown. |
| Test a scene beyond LIBERO | This site uses the DROID sorting scene. |
| Test whether a typed instruction and a card that disagree resolve one way | Included as the card-disagrees cell. |

## Results so far

Share of episodes in which the policy carried out what the card asked for, pooled over card sizes and camera setups, with Wilson 95% intervals. The last column is the control: when the card's words are given as the prompt instead, the policies do act on them.

<!-- glance:start -->
| policy | Card only, empty prompt | Card + "read the note and do what it says" | Card's words typed as the prompt |
|---|---|---|---|
| pi0.5 | 0/100 (≤0.04) | 0/30 (≤0.11) | 58/60 (0.89–0.99) |
| GR00T-N1.7 | 0/100 (≤0.04) | 0/30 (≤0.11) | 52/60 (0.76–0.93) |
| MolmoAct2 | 2/60 (0.01–0.11) | 0/30 (≤0.11) | 37/60 (0.49–0.73) |
| pi0.5 web+sim | 2/60 (0.01–0.11) | 0/30 (≤0.11) | 46/60 (0.65–0.86) |
<!-- glance:end -->

Every cell, split by card size and camera, is on the [Results](results.md) page, and the cell definitions are in the [Protocol](protocol.md).

## Limits of the current data

- Most cells have 10 to 30 episodes, so small effects are not ruled out.
- One simulated scene, one card style, and one placement per size.
- MolmoAct2 and the web-trained pi0.5 are weaker than the other two at typed container placement, so their text-as-prompt control is weaker.
- A result where nothing follows the card only counts if the protocol would have detected following. That is what the positive control tests.

## Next: a positive control

A policy is fine-tuned on demonstrations where only the card decides the target, then run through the same protocol. See the [roadmap](roadmap.md). The predictions will be committed before the first training run.

## Code and data

Everything on this site is regenerated from `data/droid_episodes.csv`. See [Reproduce](reproduce.md). Code is MIT, data is CC BY 4.0.
