"""Label an episode from the simulator's end state, and read the label back.

Labels look like "banana→bin", "cube lifted", "banana→bin + cube lifted" or "nothing moved". An object counts as placed when its
final xy is inside a container radius, as lifted when it rose more than LIFT above its start and ended on the table.
"""
OBJ = {"_11_banana": "banana", "rubiks_cube": "cube"}
BIN_R, BOWL_R, LIFT = 0.13, 0.08, 0.05    # metres: xy radius around each container centre; lift threshold


def place(p, end):
    bin_, bowl = end["small_KLT_visual_collision"], end["_24_bowl"]
    d = lambda c: ((p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2) ** 0.5
    return "bin" if d(bin_) < BIN_R else "bowl" if d(bowl) < BOWL_R else "table"


def label(ep):
    """ep = {"start": {obj: xyz}, "end": {obj: xyz}, "max_z": {obj: z}} as logged per episode."""
    parts = []
    for k, name in OBJ.items():
        where = place(ep["end"][k], ep["end"])
        if where != "table":
            parts.append(f"{name}→{where}")
        elif ep["max_z"][k] - ep["start"][k][2] > LIFT:
            parts.append(f"{name} lifted")
    return " + ".join(parts) or "nothing moved"


def parse(outcome):
    """Label -> set of (object, "lifted" | place)."""
    if outcome == "nothing moved":
        return set()
    out = set()
    for part in outcome.split(" + "):
        if part.endswith(" lifted"):
            out.add((part[: -len(" lifted")], "lifted"))
        else:
            obj, where = part.split("→")
            out.add((obj, where))
    return out


def placed(outcome, obj, where):
    return (obj, where) in parse(outcome)


def moved(outcome, obj):
    return any(o == obj for o, _ in parse(outcome))
