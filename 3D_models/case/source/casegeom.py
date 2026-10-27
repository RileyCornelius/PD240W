"""Prism-only modeling helpers: every feature is a Z extrusion from a Front-Plane offset."""
import sys, math
sys.path.insert(0, r"C:/Users/Riley/.claude/skills/solidworks/scripts")
from sw_connect import mm
from sw_part import extrude_boss, extrude_cut, _select_by_id

SW_REF_DISTANCE = 8
SW_REF_FLIP = 256


class Builder:
    def __init__(self, model):
        self.model = model
        self.planes = {0.0: "Front Plane"}

    def plane(self, z_mm):
        z = round(float(z_mm), 4)
        if z in self.planes:
            return self.planes[z]
        m = self.model
        m.ClearSelection2(True)
        assert _select_by_id(m.Extension, "Front Plane", "PLANE")
        cons = SW_REF_DISTANCE | (SW_REF_FLIP if z < 0 else 0)
        feat = m.FeatureManager.InsertRefPlane(cons, mm(abs(z)), 0, 0, 0, 0)
        m.ClearSelection2(True)
        if feat is None:
            raise RuntimeError(f"InsertRefPlane failed at z={z}")
        feat.Name = f"Z{z:+.3f}".replace(".", "_")
        self.planes[z] = feat.Name
        return feat.Name

    def _sketch(self, z_mm, draw):
        m = self.model
        m.ClearSelection2(True)
        assert _select_by_id(m.Extension, self.plane(z_mm), "PLANE")
        m.SketchManager.InsertSketch(True)
        name = m.SketchManager.ActiveSketch.Name
        m.SketchManager.AddToDB = True
        try:
            draw(m.SketchManager)
        finally:
            m.SketchManager.AddToDB = False
            m.SketchManager.InsertSketch(True)
        return name

    def boss(self, z0, z1, draw, merge=True):
        name = self._sketch(z0, draw)
        return extrude_boss(self.model, name, mm(z1 - z0), False, merge)  # False = +Z (verified)

    def cut(self, z0, z1, draw):
        name = self._sketch(z0, draw)
        return extrude_cut(self.model, name, mm(z1 - z0), True, False)  # True = +Z (verified)


# --- profile primitives (all inputs mm, centered coordinates) ---
def rrect(cx, cy, w, h, r):
    def draw(sm):
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
        P = lambda x, y: (mm(x), mm(y), 0)
        sm.CreateLine(*P(x0 + r, y0), *P(x1 - r, y0))
        sm.CreateLine(*P(x1, y0 + r), *P(x1, y1 - r))
        sm.CreateLine(*P(x1 - r, y1), *P(x0 + r, y1))
        sm.CreateLine(*P(x0, y1 - r), *P(x0, y0 + r))
        sm.CreateArc(*P(x1 - r, y0 + r), *P(x1 - r, y0), *P(x1, y0 + r), 1)
        sm.CreateArc(*P(x1 - r, y1 - r), *P(x1, y1 - r), *P(x1 - r, y1), 1)
        sm.CreateArc(*P(x0 + r, y1 - r), *P(x0 + r, y1), *P(x0, y1 - r), 1)
        sm.CreateArc(*P(x0 + r, y0 + r), *P(x0, y0 + r), *P(x0 + r, y0), 1)
    return draw


def rect(x0, y0, x1, y1):
    return lambda sm: sm.CreateCornerRectangle(mm(x0), mm(y0), 0, mm(x1), mm(y1), 0)


def circle(cx, cy, d):
    return lambda sm: sm.CreateCircleByRadius(mm(cx), mm(cy), 0, mm(d / 2))


def many(*draws):
    def draw(sm):
        for d in draws:
            r = d(sm)
    return draw


def slot(x0, y0, x1, y1, width):
    """Straight slot between two arc centers."""
    return lambda sm: sm.CreateSketchSlot(0, 0, mm(width), mm(x0), mm(y0), 0, mm(x1), mm(y1), 0, 0, 0, 0, 1, False)


def body_box(model):
    bodies = model.GetBodies2(0, False) or []
    boxes = [b.GetBodyBox() for b in bodies]
    if not boxes:
        return 0, None
    lo = [min(b[i] for b in boxes) * 1000 for i in range(3)]
    hi = [max(b[i + 3] for b in boxes) * 1000 for i in range(3)]
    return len(bodies), [round(v, 3) for v in lo + hi]
