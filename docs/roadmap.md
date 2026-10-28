# Roadmap: a positive control on DROID

The results here are nulls: the off-the-shelf policies do not follow the card. A null only counts if the protocol would have caught following. The next release tests that by fine-tuning a policy on note-conditioned demos and running the unchanged protocol on it.

This page is committed before any fine-tune result exists.

## Questions

- **Capability.** Can a DROID policy be trained to act on a card, with the instruction left generic?
- **Sensitivity.** Does the unchanged protocol detect that following?

## Design

- Scene: the DROID sorting scene in Isaac Sim, card in both cameras at 95 cm, layouts A and B swapped.
- Target: the card names an object (banana or cube); success is the named object moved or lifted, scored from simulator state.
- Demos: a policy that follows typed object names is run with the matching typed instruction. Sim-verified successes are kept, the instruction is replaced with the generic one, and both targets are generated on every init state.
- Student: a policy fine-tuned on those demos, starting with the action head only.
- Held out: init states and card wordings.
- Evaluation: the existing grid, unchanged, with at least 30 episodes per cell, plus blank-card, scrambled-card and no-card controls.

## Predictions

The predictions and decision rules will be committed to this page before the first training run.

## Schedule

Demos, a smoke fine-tune, training and evaluation run over about a week. Results are added as v1.1 of this repository, whatever they show.

## Limits

A trained-in result shows that the protocol can see following. It does not show that the existing policies read cards.
