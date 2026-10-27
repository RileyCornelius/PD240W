"""PD240W enclosure: base tray, lid, button cap. Coordinates in mm, origin at board
centre (KiCad 146.5, 92), +Y = KiCad -y, Z = 0 at PCB bottom face."""
import sys, os, json
sys.path.insert(0, r"C:/Users/Riley/.claude/skills/solidworks/scripts")
from sw_runtime import attach, default_template, no_dimension_input_dialog
from sw_documents import DocumentOwnership, new_owned
from sw_connect import save_document
from sw_inspect import snapshot, failing_features
from sw_export import export_to_step, export_to_stl
from casegeom import Builder, rrect, rect, circle, many, slot, body_box

OUT = os.path.normpath(sys.argv[1])
os.makedirs(OUT, exist_ok=True)

def K(kx, ky):
    return kx - 146.5, 92.0 - ky

# ---- envelope ----
OUTER, OUTER_R = 72.0, 6.0      # 2.0 mm walls
CAV, CAV_R = 68.0, 4.0          # 1.0 mm clearance to the 66 x 66 R3 board
Z_BOT, Z_FLOOR, Z_SPLIT = -5.5, -3.5, 0.0
BOARD_TOP = 1.55
Z_CEIL, Z_TOP = 15.6, 17.6      # tallest part under the lid: terminal block 15.05
WALL_IN, WALL_OUT = 33.5, 37.0  # wall-cut X/Y span (cavity face is at 34)

HOLES = [K(116.5, 62), K(176.5, 62), K(116.5, 122), K(176.5, 122)]   # MH2 MH1 MH3 MH4
MH1 = K(176.5, 62)

# ---- side openings (KiCad envelopes from the STEP + 0.5 mm) ----
XT60 = [(-7.95, 5.06), (-27.0, -13.99)]        # Y spans, black J4 / red J3
XT60_Z = (-1.55, 14.35)
USB_Y, USB_Z = (-25.3, -12.7), (-0.465, 6.135)  # J1 plug overmold 12.6 x 6.6
TERM_Y, TERM_Z = (6.66, 28.4), (Z_SPLIT, 10.0)  # J5/J6 wire entries
EVQ_X = [K(135.5, 0)[0], K(157.5, 0)[0]]        # S1 BOOT, S2 RST pin-holes
EVQ_Z = (Z_SPLIT, 3.5)

def wall_x(y0, y1, sign):
    return rect(*((WALL_IN, y0, WALL_OUT, y1) if sign > 0 else (-WALL_OUT, y0, -WALL_IN, y1)))

def build_base(B):
    B.boss(Z_BOT, Z_SPLIT, rrect(0, 0, OUTER, OUTER, OUTER_R))
    B.cut(Z_FLOOR, Z_SPLIT, rrect(0, 0, CAV, CAV, CAV_R))
    B.boss(Z_FLOOR, Z_SPLIT, many(*[circle(x, y, 6.0) for x, y in HOLES]))
    B.cut(Z_BOT, Z_SPLIT, many(*[circle(x, y, 2.9) for x, y in HOLES]))
    B.cut(Z_BOT, Z_BOT + 2.6, many(*[circle(x, y, 5.0) for x, y in HOLES]))   # M2.5 SHCS heads
    B.cut(Z_BOT, Z_FLOOR, many(*[slot(x, -14, x, 14, 2.0) for x in range(-15, 16, 5)]))
    B.cut(XT60_Z[0], Z_SPLIT, many(*[wall_x(y0, y1, +1) for y0, y1 in XT60]))
    B.cut(USB_Z[0], Z_SPLIT, wall_x(*USB_Y, -1))

def build_lid(B):
    B.boss(Z_SPLIT, Z_TOP, rrect(0, 0, OUTER, OUTER, OUTER_R))
    B.cut(Z_SPLIT, Z_CEIL, rrect(0, 0, CAV, CAV, CAV_R))
    # clamp bosses press the board onto the base standoffs
    B.boss(BOARD_TOP, Z_CEIL, many(*[circle(x, y, 5.0 if (x, y) == MH1 else 6.0) for x, y in HOLES]))
    B.cut(BOARD_TOP, Z_CEIL, rect(MH1[0] - 3, 26.0, MH1[0] + 3, 28.3))       # clear J6 housing
    B.cut(BOARD_TOP, BOARD_TOP + 12.0, many(*[circle(x, y, 2.2) for x, y in HOLES]))
    # top-face openings
    tops = [
        rect(-15.6, -20.7, 15.6, 20.7),                     # display window, 30.6 x 40.8 AA + 0.3
        circle(*K(121.5, 74), 7.5),                         # S4 encoder shaft
        circle(*K(121.5, 89), 5.2), circle(*K(121.5, 99), 5.2),   # S3/S5 cap stems
        circle(*K(146.5, 61.5), 3.0),                       # D11 RGB LED
        circle(*K(118, 104.1), 2.5), circle(*K(176, 103), 2.5),   # D4/D7 LEDs
        slot(*K(175, 67.5), *K(175, 82.5), 4.5),            # J5/J6 screw access
    ] + [slot(x, -23.5, x, -31.5, 1.8) for x in range(-12, 13, 4)]
    B.cut(Z_CEIL, Z_TOP, many(*tops))
    # wall openings
    B.cut(Z_SPLIT, XT60_Z[1], many(*[wall_x(y0, y1, +1) for y0, y1 in XT60]))
    B.cut(*TERM_Z, wall_x(*TERM_Y, +1))
    B.cut(Z_SPLIT, USB_Z[1], wall_x(*USB_Y, -1))
    B.cut(*EVQ_Z, many(*[rect(x - 1.25, WALL_IN, x + 1.25, WALL_OUT) for x in EVQ_X]))

# button cap, axis at origin, installed Z on a 6x6x12 tact switch (plunger top 13.55)
CAP = dict(socket_top=13.6, socket_d=3.8, socket_depth=1.0, flange_d=8.0, flange_top=15.3,
           stem_d=4.6, stem_top=19.0)

def build_cap(B):
    c = CAP
    z0 = c["socket_top"] - c["socket_depth"]
    B.boss(z0, c["flange_top"], circle(0, 0, c["flange_d"]))
    B.boss(c["flange_top"], c["stem_top"], circle(0, 0, c["stem_d"]))
    B.cut(z0, c["socket_top"], circle(0, 0, c["socket_d"]))

PARTS = [("PD240W_case_base", build_base), ("PD240W_case_lid", build_lid),
         ("PD240W_button_cap", build_cap)]

app, _ = attach(33)
own = DocumentOwnership(app)
results = {}
try:
    with no_dimension_input_dialog(app):
        for name, fn in PARTS:
            m = new_owned(app, own, default_template(app, "part"))
            fn(Builder(m))
            state = snapshot(m)
            nb, box = body_box(m)
            sld = os.path.join(OUT, name + ".SLDPRT")
            assert save_document(m, sld), sld
            assert export_to_step(m, os.path.join(OUT, name + ".step"))
            assert export_to_stl(m, os.path.join(OUT, name + ".stl"))
            results[name] = {"bodies": nb, "box_mm": box,
                             "volume_mm3": round(state["mass"]["volume_m3"] * 1e9, 1),
                             "failing_features": [str(f) for f in failing_features(state["features"])]}
            print(name, results[name])
            own.close(m)
finally:
    own.close_all()
json.dump(results, open(os.path.join(OUT, "_build_summary.json"), "w"), indent=1)
