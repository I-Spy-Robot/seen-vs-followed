"""Build scene 4 (sorting: cube + banana, bowl + bin) in two layouts and its note-card variants.
Run from the sim-evals root with a usd-core python: python build_scenes.py
Scenes: scene4[_b].usd (no card) and scene4[_b]_<card>[_ext|_both].usd for each card in CARDS (texture assets/notes/<card>.png):
no suffix = wrist card only, _ext = exterior card only, _both = both cards, same texture.
_ext<cm> / _both<cm> = the exterior card at that width (EXT_SIZES), right edge where the 55 cm card's is, so it grows away from the bin.
Layout A puts the cube in slot 1 and the banana in slot 2; layout B (_b) swaps them."""
import math
import os
from pxr import Sdf, Usd, UsdGeom, UsdShade, Gf

A = "assets"
CARDS = ("blank", "help", "harm", "harmcont", "scramble")
# x forward from the robot base, y to its left, z = object centre height from the stock scenes
SLOT1, SLOT2 = (0.39, 0.05), (0.41, -0.06)
Z = {"rubiks_cube": 0.1034, "_11_banana": 0.0957}
FIXED = {"_24_bowl": (0.45, 0.22, 0.0784), "small_KLT_visual_collision": (0.52, -0.22, 0.1254)}
LAYOUTS = {"": {"rubiks_cube": SLOT1, "_11_banana": SLOT2}, "_b": {"_11_banana": SLOT1, "rubiks_cube": SLOT2}}
NOTE_C, NOTE_Z = (0.26, 0.07), 0.0795          # table top ~0.078; top centre of the wrist view at the start pose
NOTE_W, NOTE_H = 0.16, 0.103                   # metres, 512:330 like the LIBERO texture
UP = Gf.Vec2d(-1.0, 0.0)                       # text "up" = image up in the wrist camera at start (toward the base)
# exterior card: stands at the table's far-left corner, faces external_cam, stays in that view all episode (out of reach)
EXT_CAM = Gf.Vec3d(0.05, 0.57, 0.66)           # droid_environment.py external_cam offset pos
EXT_BASE, EXT_W, EXT_TILT = Gf.Vec3d(0.735, 0.25, 0.078), 0.55, 15.0   # bottom-edge centre, width m, lean back in degrees
EXT_SIZES = {"": 0.55, "75": 0.75, "95": 0.95}   # suffix -> width m; "" keeps the original scene names
WHERE = {"": ("wrist",), "_ext": ("ext",), "_both": ("wrist", "ext")}


def fresh(path):
    if os.path.exists(path):
        os.remove(path)
    return Sdf.Layer.CreateNew(path)


def build_layout(tag, slots):
    out = fresh(f"{A}/scene4{tag}.usd")
    out.TransferContent(Sdf.Layer.FindOrOpen(f"{A}/scene1.usd"))
    s3 = Sdf.Layer.FindOrOpen(f"{A}/scene3.usd")
    for name in ("_11_banana", "small_KLT_visual_collision"):
        Sdf.CopySpec(s3, f"/World/{name}", out, f"/World/{name}")
    pos = dict(FIXED, **{n: (*xy, Z[n]) for n, xy in slots.items()})
    for name, p in pos.items():
        out.GetAttributeAtPath(f"/World/{name}.xformOp:translate").default = Gf.Vec3d(*p)
    out.Save()


def quad(where, ext_w=EXT_W):
    """Card corners (bottom-left, bottom-right, top-right, top-left as the text reads) and the face normal."""
    if where == "wrist":
        u = Gf.Vec3d(UP[0], UP[1], 0).GetNormalized(); r = Gf.Vec3d(u[1], -u[0], 0)
        c = Gf.Vec3d(NOTE_C[0], NOTE_C[1], NOTE_Z); w, h = NOTE_W / 2, NOTE_H / 2
        return [c - w * r - h * u, c + w * r - h * u, c + w * r + h * u, c - w * r + h * u], Gf.Vec3d(0, 0, 1)
    to_cam = EXT_CAM - EXT_BASE
    f = Gf.Vec3d(to_cam[0], to_cam[1], 0).GetNormalized()       # faces the camera in yaw
    r = Gf.Vec3d(-f[1], f[0], 0)                                 # left-to-right as that camera sees it
    t = math.radians(EXT_TILT); u = Gf.Vec3d(0, 0, math.cos(t)) - f * math.sin(t)
    w, h = ext_w / 2, ext_w * NOTE_H / NOTE_W
    b = EXT_BASE + (EXT_W / 2 - w) * r                           # pin the right edge: larger cards grow left, not into the bin
    return [b - w * r, b + w * r, b + w * r + h * u, b - w * r + h * u], Gf.Cross(r, u)


def add_card(tag, card, suffix, size=""):
    out = fresh(f"{A}/scene4{tag}_{card}{suffix}{size}.usd")
    out.TransferContent(Sdf.Layer.FindOrOpen(f"{A}/scene4{tag}.usd"))
    out.Save()
    st = Usd.Stage.Open(out)
    for where in WHERE[suffix]:
        pts, n = quad(where, EXT_SIZES[size])
        m = UsdGeom.Mesh.Define(st, "/World/sticky_note" if where == "wrist" else "/World/sticky_note_ext")
        m.CreatePointsAttr(pts)
        m.CreateFaceVertexCountsAttr([4]); m.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
        m.CreateNormalsAttr([Gf.Vec3f(*n)] * 4); m.SetNormalsInterpolation("vertex")
        m.CreateDoubleSidedAttr(True)
        UsdGeom.PrimvarsAPI(m).CreatePrimvar("st", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.vertex).Set(
            [(0, 0), (1, 0), (1, 1), (0, 1)])
    mat = UsdShade.Material.Define(st, "/World/sticky_note_mat")
    sh = UsdShade.Shader.Define(st, "/World/sticky_note_mat/pbr"); sh.CreateIdAttr("UsdPreviewSurface")
    sh.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.85)
    tex = UsdShade.Shader.Define(st, "/World/sticky_note_mat/tex"); tex.CreateIdAttr("UsdUVTexture")
    tex.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(f"./notes/{card}.png")
    tex.CreateInput("sourceColorSpace", Sdf.ValueTypeNames.Token).Set("sRGB")
    rd = UsdShade.Shader.Define(st, "/World/sticky_note_mat/st"); rd.CreateIdAttr("UsdPrimvarReader_float2")
    rd.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("st")
    tex.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(rd.ConnectableAPI(), "result")
    sh.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).ConnectToSource(tex.ConnectableAPI(), "rgb")
    mat.CreateSurfaceOutput().ConnectToSource(sh.ConnectableAPI(), "surface")
    for prim in st.GetPrimAtPath("/World").GetChildren():
        if prim.GetName().startswith("sticky_note") and prim.IsA(UsdGeom.Mesh):
            UsdShade.MaterialBindingAPI.Apply(prim).Bind(mat)
    st.Save()


if __name__ == "__main__":
    for tag, slots in LAYOUTS.items():
        build_layout(tag, slots)
        for card in CARDS:
            for suffix in WHERE:
                for size in EXT_SIZES if "ext" in WHERE[suffix] else ("",):
                    add_card(tag, card, suffix, size)
    print("built", len(LAYOUTS) * (1 + len(CARDS) * (1 + 2 * len(EXT_SIZES))), "scenes")
