"""PD240W case assembly: PCB fixed as datum, case parts located by geometric mates."""
import sys, os, json, math
sys.path.insert(0, r"C:/Users/Riley/.claude/skills/solidworks/scripts")
from sw_runtime import attach, default_template, place_component, component_transform
from sw_documents import DocumentOwnership, new_owned, open_owned, _byref_i4
from sw_connect import save_document, get_com_member as M
from sw_assembly import _add_mate5, _select_entity, surface_data, fix_component, is_component_fully_constrained
from sw_export import export_to_step

CASE = r"C:\Projects\2026\PD240W\3D_models\case"
P = lambda n: os.path.join(CASE, n + ".SLDPRT")
OFF = (146.5, -92.0, 0.0)          # case frame -> KiCad/PCB frame, mm
COINCIDENT, CONCENTRIC, PARALLEL, DISTANCE = 0, 1, 3, 5
CLOSEST = 2
REVIEW = os.path.normpath(sys.argv[1])
os.makedirs(REVIEW, exist_ok=True)
log = {"mates": []}
_face_cache = {}


def faces_of(model):
    """Faces of the model's bodies; on the 1000-body PCB part only the board substrate
    (walking every component body's faces crashed SolidWorks)."""
    key = id(model)
    if key not in _face_cache:
        bodies = list(model.GetBodies2(0, False) or [])
        if len(bodies) > 50:
            bodies = [b for b in bodies if (lambda bb: bb[3] - bb[0] > 0.06)(b.GetBodyBox())]
        _face_cache[key] = [(f, surface_data(f)) for b in bodies for f in (b.GetFaces() or [])]
    return _face_cache[key]


def plane(model, normal, coord_mm, axis, near=None, largest=True, tol=0.02):
    """Planar face (part frame) with the given normal, lying at coord on axis."""
    hits = []
    for f, d in faces_of(model):
        # face normal, not surface normal: STEP faces can be reversed against their surface
        if d["type"] != "plane" or sum(a * b for a, b in zip(f.Normal, normal)) < 0.999:
            continue
        if abs(d["root_mm"][axis] - coord_mm) > tol:
            # root point may lie anywhere on the plane; check via face box instead
            bx = [v * 1000 for v in d["box_m"]]
            if abs(bx[axis] - coord_mm) > tol or abs(bx[axis + 3] - coord_mm) > tol:
                continue
        if near is not None:
            bx = [v * 1000 for v in d["box_m"]]
            if not (bx[0] - 0.1 <= near[0] <= bx[3] + 0.1 and bx[1] - 0.1 <= near[1] <= bx[4] + 0.1):
                continue
        hits.append((d["area_mm2"], f))
    if not hits:
        raise RuntimeError(f"no plane normal={normal} at {coord_mm} on axis {axis} near {near}")
    hits.sort(key=lambda h: h[0], reverse=largest)
    return hits[0][1]


def cyl(model, xy, r_range, tol=0.1):
    hits = []
    for f, d in faces_of(model):
        if d["type"] != "cylinder" or abs(abs(d["axis"][2]) - 1) > 1e-6:
            continue
        if not (r_range[0] <= d["radius_mm"] <= r_range[1]):
            continue
        if math.hypot(d["origin_mm"][0] - xy[0], d["origin_mm"][1] - xy[1]) > tol:
            continue
        hits.append((d["area_mm2"], f, d["radius_mm"]))
    if not hits:
        raise RuntimeError(f"no cylinder r in {r_range} at {xy}")
    hits.sort(key=lambda h: h[0], reverse=True)
    return hits[0][1]


def mate(asm, kind, c1, f1, c2, f2, label, **kw):
    sm = M(asm, "SelectionManager")
    e1, e2 = c1.GetCorresponding(f1), c2.GetCorresponding(f2)
    if e1 is None or e2 is None:
        raise RuntimeError(f"{label}: no assembly-context face")
    asm.ClearSelection2(True)
    d1 = M(sm, "CreateSelectData"); d1.Mark = 1
    d2 = M(sm, "CreateSelectData"); d2.Mark = 1
    ok = _select_entity(e1, False, d1) and _select_entity(e2, True, d2)
    if not ok or sm.GetSelectedObjectCount2(-1) != 2:
        asm.ClearSelection2(True)
        raise RuntimeError(f"{label}: selection failed")
    try:
        m = _add_mate5(asm, kind, alignment=CLOSEST, **kw)
    finally:
        asm.ClearSelection2(True)
    log["mates"].append({"label": label, "type": kind})
    print("mate ok:", label, flush=True)
    return m


app, _ = attach(33)
own = DocumentOwnership(app)
try:
    D = {n: open_owned(app, own, P(n), 1)[0] for n in
         ["PD240W_PCB", "PD240W_case_base", "PD240W_case_lid", "PD240W_button_cap"]}
    asm = new_owned(app, own, default_template(app, "assembly"))
    app.ActivateDoc3(M(asm, "GetTitle"), False, 0, _byref_i4())

    def add(name, xy=(0.0, 0.0), offset=OFF):
        c = asm.AddComponent4(P(name), "", 0, 0, 0)
        if c is None:
            raise RuntimeError(f"AddComponent4 failed: {name}")
        place_component(app, c, ((offset[0] + xy[0]) / 1000, (offset[1] + xy[1]) / 1000, offset[2] / 1000))
        return c

    pcb = add("PD240W_PCB", offset=(0, 0, 0))
    # Component2.Select4 takes (Append, Data, Callout); the helper passes only two
    asm.ClearSelection2(True)
    if not pcb.Select4(False, M(M(asm, "SelectionManager"), "CreateSelectData"), False):
        raise RuntimeError("cannot select PCB component")
    M(asm, "FixComponent")
    asm.ClearSelection2(True)
    if not M(pcb, "IsFixed"):
        raise RuntimeError("PCB did not become fixed")
    base = add("PD240W_case_base")
    lid = add("PD240W_case_lid")
    caps = [add("PD240W_button_cap", (-25, 3)), add("PD240W_button_cap", (-25, -7))]
    # nudge free parts off target so the mates, not the initial placement, locate them
    for c in [base, lid] + caps:
        t = component_transform(c)
        place_component(app, c, (t[9] + 0.0004, t[10] - 0.0003, t[11] + 0.0005))

    base_d, lid_d, cap_d, pcb_d = D["PD240W_case_base"], D["PD240W_case_lid"], D["PD240W_button_cap"], D["PD240W_PCB"]
    # base -> PCB: standoff top on board bottom, MH2 hole concentric, left wall parallel to board edge
    mate(asm, COINCIDENT, base, plane(base_d, (0, 0, 1), 0.0, 2, near=(-30, 30), largest=False),
         pcb, plane(pcb_d, (0, 0, -1), 0.0, 2), "base standoff | PCB bottom")
    mate(asm, CONCENTRIC, base, cyl(base_d, (-30, 30), (1.4, 1.5)),
         pcb, cyl(pcb_d, (116.5, -62), (1.2, 1.5)), "base hole MH2 | PCB hole MH2")
    mate(asm, PARALLEL, base, plane(base_d, (-1, 0, 0), -36.0, 0),
         pcb, plane(pcb_d, (-1, 0, 0), 113.5, 0), "base left wall || PCB left edge")
    # lid -> base: rim on rim, MH2 pilot concentric with base hole, left walls parallel
    mate(asm, COINCIDENT, lid, plane(lid_d, (0, 0, -1), 0.0, 2),
         base, plane(base_d, (0, 0, 1), 0.0, 2), "lid rim | base rim")
    mate(asm, CONCENTRIC, lid, cyl(lid_d, (-30, 30), (1.05, 1.15)),
         base, cyl(base_d, (-30, 30), (1.4, 1.5)), "lid pilot MH2 | base hole MH2")
    mate(asm, PARALLEL, lid, plane(lid_d, (-1, 0, 0), -36.0, 0),
         base, plane(base_d, (-1, 0, 0), -36.0, 0), "lid left wall || base left wall")
    # caps -> lid: stem concentric with lid hole (rotation locked), flange 0.3 mm under the ceiling
    ceiling = plane(lid_d, (0, 0, -1), 15.6, 2)
    stem = cyl(cap_d, (0, 0), (2.25, 2.35))
    flange_top = plane(cap_d, (0, 0, 1), 15.3, 2)
    for i, (c, xy) in enumerate(zip(caps, [(-25, 3), (-25, -7)]), 1):
        mate(asm, CONCENTRIC, c, stem, lid, cyl(lid_d, xy, (2.55, 2.65)),
             f"cap{i} stem | lid hole", lock_rotation=True)
        mate(asm, DISTANCE, c, flange_top, lid, ceiling, f"cap{i} flange 0.3 mm below ceiling",
             distance=0.0003)

    if M(asm, "EditRebuild3") is not True:
        raise RuntimeError("assembly rebuild failed")
    poses = []
    for c, exp in [(pcb, (0, 0, 0)), (base, OFF), (lid, OFF),
                   (caps[0], (121.5, -89, 0)), (caps[1], (121.5, -99, 0))]:
        t = component_transform(c)
        tr = [round(v * 1000, 4) for v in t[9:12]]
        rot = [round(v, 6) for v in t[0:9]]
        poses.append({"component": c.Name2, "translation_mm": tr, "expected_mm": list(exp),
                      "max_err_mm": round(max(abs(a - b) for a, b in zip(tr, exp)), 4),
                      "identity_rotation": rot == [1, 0, 0, 0, 1, 0, 0, 0, 1],
                      "fixed": bool(M(c, "IsFixed")),
                      "fully_constrained": bool(M(c, "IsFixed")) or is_component_fully_constrained(c)})
    log["poses"] = poses
    print(json.dumps(poses, indent=1), flush=True)
    bad = [p for p in poses if p["max_err_mm"] > 0.001 or not p["identity_rotation"] or not p["fully_constrained"]]
    if bad:
        raise RuntimeError(f"pose/constraint check failed: {bad}")

    mgr = M(asm, "InterferenceDetectionManager")
    mgr.TreatSubAssembliesAsComponents = True
    mgr.TreatCoincidenceAsInterference = False
    mgr.IncludeMultibodyPartInterferences = False
    mgr.IgnoreHiddenBodies = True
    mgr.UseTransform = False
    try:
        recs = [{"components": [c.Name2 for c in (M(r, "Components") or [])],
                 "volume_mm3": round(float(M(r, "Volume")) * 1e9, 4)}
                for r in list(M(mgr, "GetInterferences") or [])]
    finally:
        M(mgr, "Done")
    log["interference"] = {"count": len(recs), "records": recs}
    print("interference", log["interference"], flush=True)

    out = os.path.join(CASE, "PD240W_case_assembly.SLDASM")
    step = os.path.join(CASE, "PD240W_case_assembly.step")
    assert save_document(asm, out)
    assert export_to_step(asm, step)
    from sw_review import run_review
    rep, path = run_review(asm, REVIEW, basename="PD240W_case_assembly", expected_outputs=[out, step])
    log["review"] = {"status": rep["evaluation"]["status"], "report": path,
                     "issues": [i["code"] for i in rep["evaluation"].get("issues", [])]}
    print("review", log["review"], flush=True)
finally:
    json.dump(log, open(os.path.join(REVIEW, "assembly_log.json"), "w"), indent=1, default=str)
    own.close_all()
