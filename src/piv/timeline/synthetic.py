"""A synthetic template.json (copy-in-product-picture's template.md v1 shape) with made-up
geometry: the structure of a stacked design (background, hero, three detail circles, three
fades, a headline and a sub-line) and none of any brand's content. For tests, and for a
renderer's synthetic layers made at run time."""

from __future__ import annotations


def synthetic_template(size: tuple[int, int] = (1080, 1350)) -> dict:
    W, H = size
    sx, sy = W / 1080, H / 1350

    def b(x0, y0, x1, y1):
        return [round(x0 * sx), round(y0 * sy), round(x1 * sx), round(y1 * sy)]

    layers = [
        {
            "id": "L00",
            "kind": "pixel",
            "role": "background",
            "bbox": b(0, 0, 1080, 1350),
        },
        {"id": "L01", "kind": "pixel", "role": "hero", "bbox": b(200, -20, 880, 720)},
    ]
    circles = [(270, 870), (540, 870), (810, 870)]
    slots_details = []
    n = 2
    # the designer's stacking puts the rightmost circle lowest (as an imported PSD may)
    for i in (2, 1, 0):
        cx, cy = circles[i]
        mask, img, ring = f"L{n:02d}", f"L{n + 1:02d}", f"L{n + 2:02d}"
        layers += [
            {"id": mask, "kind": "shape", "role": "detail_mask", "bbox": b(cx - 160, cy - 160, cx + 160, cy + 160)},
            {"id": img, "kind": "pixel", "role": "detail_image", "clip_to": mask,
             "bbox": b(cx - 400, cy - 400, cx + 400, cy + 400)},
            {"id": ring, "kind": "shape", "role": "detail_ring", "bbox": b(cx - 166, cy - 166, cx + 166, cy + 166)},
        ]  # fmt: skip
        slots_details.append(
            {"image_layer": img, "mask_layer": mask, "ring_layer": ring,
             "circle": [cx * sx, cy * sy, 160 * sx]}
        )  # fmt: skip
        n += 3
    slots_details.reverse()  # slots are left to right
    for i in range(3):
        layers.append(
            {
                "id": f"L{n:02d}",
                "kind": "pixel",
                "role": "gradient",
                "bbox": b(0, 880 + 20 * i, 1080, 1350),
            }
        )
        n += 1
    head, sub = f"L{n:02d}", f"L{n + 1:02d}"
    layers += [
        {"id": head, "kind": "type", "role": "headline", "bbox": b(90, 1080, 990, 1220),
         "text": {"content": "SYNTHETIC LINE ONE\nLINE TWO", "font": "Synthetic-Condensed", "size": 70.0 * sy,
                  "color": "#FFFFFF", "rendered_color": "#FFFFFF", "tracking": -20, "leading": None,
                  "auto_leading": 1.2, "align": "center", "anchor": [540 * sx, 1140 * sy],
                  "box": b(60, 1080, 1020, 1220), "max_lines": 2}},
        {"id": sub, "kind": "type", "role": "subline", "bbox": b(440, 1240, 640, 1266),
         "text": {"content": "example.com", "font": "Synthetic-Condensed", "size": 28.0 * sy,
                  "color": "#FFFFFF", "rendered_color": "#33CC99", "tracking": -20, "leading": None,
                  "auto_leading": 1.2, "align": "center", "anchor": [540 * sx, 1266 * sy],
                  "box": b(60, 1240, 1020, 1266), "max_lines": 1}},
        {"id": f"L{n + 2:02d}", "kind": "pixel", "role": "guide", "visible": False, "bbox": b(0, 0, 1080, 1350)},
    ]  # fmt: skip
    for layer in layers:
        layer.setdefault("visible", True)
        layer.setdefault("opacity", 1.0)
        layer.setdefault("name", layer["id"])
        layer.setdefault("png", f"layers/{layer['id']}.png")
    return {
        "format_version": 1,
        "id": "synthetic-stack",
        "source": {"kind": "synthetic", "path": None, "sha256": "0" * 64},
        "size": [W, H],
        "layers": layers,
        "slots": {
            "hero": {
                "layer": "L01",
                "frame": b(200, -20, 880, 720),
                "product_box": b(260, 40, 820, 700),
                "box": b(230, 40, 850, 700),
            },
            "details": slots_details,
            "headline": {"layer": head},
            "subline": {"layer": sub},
            "accent": {"layers": [sub], "default": "#33CC99"},
        },
        "roles_confirmed_by": None,
    }
