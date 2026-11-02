# -*- coding: utf-8 -*-
"""Layout Validator — Apna Bihar Samachar video system (Phase 1).

ZERO-OVERLAP frame system: har scene ke elements ke bounding-box
register hote hain; render se pehle ye jaanch chalti hai:
  1. Har box frame ke andar hai (5% safe margin ke saath, jab tak
     element ko 'background' ya 'bleed' na kaha gaya ho).
  2. Koi do foreground boxes aapas me overlap nahi karte
     (background layers ko chhod kar).
  3. Text box ke andar text fit hota hai ya nahi (measure function se).
Galti mile to LayoutError uthta hai — scene render nahi hoga.
"""
from __future__ import annotations

SAFE_MARGIN = 0.05  # frame ka 5%


class Box:
    def __init__(self, name, x, y, w, h, layer="fg"):
        self.name = name
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)
        self.layer = layer  # 'bg' = intentional background layer

    @property
    def x2(self):
        return self.x + self.w

    @property
    def y2(self):
        return self.y + self.h

    def overlaps(self, other: "Box") -> bool:
        return not (self.x2 <= other.x or other.x2 <= self.x
                    or self.y2 <= other.y or other.y2 <= self.y)

    def __repr__(self):
        return f"Box({self.name}, {self.x},{self.y},{self.w}x{self.h}, {self.layer})"


class LayoutError(Exception):
    pass


def validate_scene(boxes, width=1280, height=720, scene="scene"):
    """Return list of problems (empty = OK). Raise nahi karta."""
    problems = []
    mx = int(width * SAFE_MARGIN)
    my = int(height * SAFE_MARGIN)
    for b in boxes:
        if b.x < 0 or b.y < 0 or b.x2 > width or b.y2 > height:
            problems.append(f"{scene}: '{b.name}' frame se bahar hai {b}")
        elif b.layer != "bg" and (b.x < mx or b.y < my or b.x2 > width - mx or b.y2 > height - my):
            problems.append(f"{scene}: '{b.name}' safe margin (5%) ke bahar hai {b}")
    fg = [b for b in boxes if b.layer != "bg"]
    for i in range(len(fg)):
        for j in range(i + 1, len(fg)):
            if fg[i].overlaps(fg[j]):
                problems.append(f"{scene}: OVERLAP '{fg[i].name}' x '{fg[j].name}'")
    return problems


def require_valid(boxes, width=1280, height=720, scene="scene"):
    problems = validate_scene(boxes, width, height, scene)
    if problems:
        raise LayoutError(" | ".join(problems))
    return True


def check_text_fit(measure, text, max_w, max_lines, wrap_fn):
    """measure(text)->width px; wrap_fn(text, max_w)->lines. Fit hai to True."""
    lines = wrap_fn(text, max_w)
    return len(lines) <= max_lines, lines
