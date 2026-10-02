"""The timeline contract v0 (docs/contracts/timeline.md): data model, load/dump, validation,
easing, evaluation at a frame, recipes, the build from a template, variant ids. Stdlib only."""

from .build import build_timeline
from .canonical import canonical_json, frac, sha256_hex
from .easing import EASINGS, ease
from .errors import FormatError, Refused, TimelineError, ValidationError, VersionError
from .evaluate import (
    FrameState,
    LayerState,
    TextState,
    evaluate,
    evaluate_at,
    frame_time_ms,
    layer_matrix,
)
from .layout import (
    canvas_size,
    content_safe_rect,
    load_layout,
    resolve_layout,
    safe_rect,
)
from .model import (
    FORMAT_VERSION,
    Recipe,
    Timeline,
    dump,
    dumps,
    from_dict,
    load,
    loads,
)
from .recipes import load_recipe, recipe_sha256, scale_recipe
from .validate import check, problems
from .variant import (
    ManifestRow,
    VariantSpec,
    ad_key,
    append_row,
    read_manifest,
    variant_id,
)

__all__ = [
    "EASINGS", "FORMAT_VERSION", "FormatError", "FrameState", "LayerState", "ManifestRow", "Recipe",
    "Refused", "TextState", "Timeline", "TimelineError", "ValidationError", "VariantSpec",
    "VersionError", "ad_key", "append_row", "build_timeline", "canonical_json", "canvas_size",
    "check", "content_safe_rect", "dump", "dumps", "ease", "evaluate", "evaluate_at", "frac",
    "frame_time_ms", "from_dict", "layer_matrix", "load", "load_layout", "load_recipe", "loads",
    "problems", "read_manifest", "recipe_sha256", "resolve_layout", "safe_rect", "scale_recipe",
    "sha256_hex", "variant_id",
]  # fmt: skip
