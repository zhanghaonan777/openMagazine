"""slide_manifest_builder — produce a slide_manifest from spec inputs.

A manifest is the realization-ready document consumed by WeasyprintCompose
and (future) HtmlInteractiveCompose / PresentationsAdapter. One builder
run per `design_system.output_targets` entry.

CLI:
    python -m lib.slide_manifest_builder library/issue-specs/<slug>.yaml \\
        --target a4-magazine --locale en --output -

The builder is the only place where:
  - image_grids are expanded into N independent image regions
  - rect_norm is converted to rect_px against the target's page_size
  - text is localised (one language per manifest)
  - typography fallback chains are composed from brand + design_system
  - claim_role hints are mapped onto regions

Realizers stay dumb: read the manifest, draw the regions, done.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from typing import Any

import yaml

SKILL_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from lib.spec_loader import load_spec, resolve_layers
from lib.regions_loader import load_regions, RegionsNotFoundError


BUILDER_VERSION = "slide_manifest_builder/0.1"


# Literal text fallbacks for decorative regions whose regions.yaml entries
# have no text_field (known v0.3.1 gap: TOC/colophon section headers).
_DEFAULT_LITERAL_TEXT = {
    "toc": {
        "section_label": {"en": "CONTENTS", "zh": "目录"},
        "section_title": {"en": "Contents", "zh": "目录"},
    },
    "colophon": {
        "section_label": {"en": "COLOPHON", "zh": "出版信息"},
    },
}


# text_field name -> claim_role hint. Hardcoded today because article copy
# has not yet been migrated (lead is the de-facto claim, title is a topic).
_TEXT_FIELD_CLAIM_ROLE = {
    "kicker": "kicker",
    "lead": "claim_title",
    "body": "support_note",
    "quote": "claim_title",
    "cover_kicker": "kicker",
    "cover_line": "claim_title",
}


_COMPONENT_TO_TYPOGRAPHY_SLOT = {
    "Masthead": "display",
    "Title": "display",
    "CoverLine": "display",
    "Kicker": "kicker",
    "Lead": "body",
    "Body": "body",
    "BodyWithDropCap": "body",
    "Caption": "caption",
    "CaptionedThumbnail": "caption",
    "PullQuote": "pull_quote",
    "TocList": "body",
    "Folio": "page_number",
    "CreditsBlock": "body",
}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def build_manifest(
    spec: dict,
    layers: dict,
    article: dict,
    target: dict,
    *,
    locale: str = "en",
    regions_by_type: dict[str, dict] | None = None,
    claim_spine_ref: str | None = None,
) -> dict:
    """Build a slide_manifest dict from in-memory inputs.

    All disk I/O is in ``build_from_spec_path``; this function is pure
    over dicts and is what tests should drive.
    """
    layout = layers.get("layout") or {}
    brand = layers.get("brand") or {}
    design_system = layers.get("design_system") or {}
    regions_by_type = regions_by_type or {}

    spread_plan = layout.get("spread_plan") or []
    image_slots_layout = layout.get("image_slots") or []
    spread_copy = article.get("spread_copy") or []
    copy_by_idx = {
        c["idx"]: c for c in spread_copy
        if isinstance(c, dict) and "idx" in c
    }
    claim_spine = article.get("claim_spine") or {}
    claims_by_idx = {
        c["spread_idx"]: c
        for c in (claim_spine.get("spread_claims") or [])
        if isinstance(c, dict) and "spread_idx" in c
    }

    design_tokens = compute_design_tokens(brand, design_system)
    augmented_target = augment_target(target, brand)

    slides: list[dict] = []
    for i, sp_entry in enumerate(spread_plan):
        idx = sp_entry.get("idx")
        spread_type = sp_entry.get("type")
        if idx is None or spread_type is None:
            continue
        copy_entry = copy_by_idx.get(idx, {})
        claim_entry = claims_by_idx.get(idx)
        regions_doc = regions_by_type.get(spread_type)

        pages_per_instance = (
            int(regions_doc.get("pages_per_instance", 1)) if regions_doc else 1
        )
        canvas_w_px, canvas_h_px = _slide_canvas_px(augmented_target, pages_per_instance)

        regions: list[dict] = []
        if regions_doc:
            for region in regions_doc.get("regions", []) or []:
                resolved = _build_region(
                    region,
                    spread_idx=idx,
                    spread_type=spread_type,
                    copy_entry=copy_entry,
                    article=article,
                    image_slots_layout=image_slots_layout,
                    claim_entry=claim_entry,
                    locale=locale,
                    design_tokens=design_tokens,
                    canvas_w_px=canvas_w_px,
                    canvas_h_px=canvas_h_px,
                )
                if isinstance(resolved, list):
                    regions.extend(resolved)
                elif resolved is not None:
                    regions.append(resolved)

        slide = {
            "slide_idx": i + 1,
            "spread_idx": idx,
            "spread_type": spread_type,
            "pages_per_instance": pages_per_instance,
            "regions": regions,
        }
        page_indices = sp_entry.get("pages")
        if isinstance(page_indices, list):
            slide["page_indices"] = list(page_indices)
        slides.append(slide)

    manifest: dict = {
        "schema_version": 1,
        "spec_slug": spec.get("slug", ""),
        "built_at": _now_iso(),
        "builder_version": BUILDER_VERSION,
        "locale": locale,
        "output_target": augmented_target,
        "design_tokens": design_tokens,
        "slides": slides,
    }

    brand_auth = design_system.get("brand_authenticity")
    if isinstance(brand_auth, dict):
        filtered = {
            k: list(v) for k, v in brand_auth.items()
            if k in (
                "do_not_generate",
                "do_not_approximate",
                "asset_provenance_required",
                "asset_provenance_optional",
            )
            and isinstance(v, list) and v
        }
        if filtered:
            manifest["brand_authenticity"] = filtered

    text_safe = design_system.get("text_safe_contracts")
    if isinstance(text_safe, dict) and isinstance(text_safe.get("default_rule"), str):
        rule = text_safe["default_rule"].strip()
        if rule:
            manifest["text_safe_default_rule"] = rule

    if claim_spine_ref is not None:
        manifest["claim_spine_ref"] = claim_spine_ref
    elif "claim_spine" in article:
        slug = spec.get("article") or spec.get("slug") or ""
        manifest["claim_spine_ref"] = (
            f"library/articles/{slug}.yaml#claim_spine"
        )

    return manifest


def build_from_spec_path(
    spec_path: pathlib.Path,
    *,
    target_format: str = "a4-magazine",
    locale: str = "en",
) -> dict:
    """Disk-reading entry: load spec, layers, article, regions, then build."""
    spec, _ = load_spec(spec_path)
    layers = resolve_layers(spec)

    article_slug = spec.get("article") or spec.get("slug")
    if not article_slug:
        raise ValueError("spec is missing both 'article' and 'slug' keys")
    article_path = SKILL_ROOT / "library" / "articles" / f"{article_slug}.yaml"
    article = yaml.safe_load(article_path.read_text(encoding="utf-8"))

    design_system = layers.get("design_system") or {}
    targets = design_system.get("output_targets") or [
        {"format": "a4-magazine", "realizer": "weasyprint"}
    ]
    target = next((t for t in targets if t.get("format") == target_format), None)
    if target is None:
        raise ValueError(
            f"target {target_format!r} not in design_system.output_targets "
            f"(have: {[t.get('format') for t in targets]})"
        )

    regions_by_type: dict[str, dict] = {}
    for sp in layers.get("layout", {}).get("spread_plan", []) or []:
        st = sp.get("type")
        if not st or st in regions_by_type:
            continue
        try:
            regions_by_type[st] = load_regions(st)
        except RegionsNotFoundError:
            pass

    return build_manifest(
        spec, layers, article, target,
        locale=locale, regions_by_type=regions_by_type,
    )


# ---------------------------------------------------------------------------
# Per-region construction
# ---------------------------------------------------------------------------


def _build_region(
    region: dict,
    *,
    spread_idx: int,
    spread_type: str,
    copy_entry: dict,
    article: dict,
    image_slots_layout: list[dict],
    claim_entry: dict | None,
    locale: str,
    design_tokens: dict,
    canvas_w_px: float,
    canvas_h_px: float,
) -> dict | list[dict] | None:
    role = region.get("role")
    rect_norm = region.get("rect_norm")
    if not isinstance(rect_norm, list) or len(rect_norm) != 4:
        return None
    rect_px = _compute_rect_px(rect_norm, canvas_w_px, canvas_h_px)

    if role == "image":
        return _build_image_region(
            region, rect_norm=rect_norm, rect_px=rect_px,
            spread_idx=spread_idx,
            image_slots_layout=image_slots_layout,
            claim_entry=claim_entry,
        )
    if role == "image_grid":
        return _expand_image_grid(
            region, rect_norm=rect_norm,
            spread_idx=spread_idx,
            image_slots_layout=image_slots_layout,
            canvas_w_px=canvas_w_px, canvas_h_px=canvas_h_px,
            claim_entry=claim_entry,
        )
    if role in ("text", "text_decorative"):
        return _build_text_region(
            region, rect_norm=rect_norm, rect_px=rect_px,
            spread_idx=spread_idx, spread_type=spread_type,
            copy_entry=copy_entry, article=article,
            locale=locale, design_tokens=design_tokens,
        )
    if role == "accent":
        return _build_accent_or_decorative(
            region, rect_norm=rect_norm, rect_px=rect_px,
            design_tokens=design_tokens,
        )
    # Unknown role: emit as decorative (permissive).
    return {
        "id": region.get("id", ""),
        "rect_norm": rect_norm,
        "rect_px": rect_px,
        "role": "decorative",
        "z_index": int(region.get("z_index", 0)),
    }


def _build_image_region(
    region: dict,
    *,
    rect_norm: list,
    rect_px: list,
    spread_idx: int,
    image_slots_layout: list[dict],
    claim_entry: dict | None,
) -> dict:
    image_slot = region.get("image_slot") or region.get("id", "")
    aspect = region.get("aspect", "")
    for s in image_slots_layout:
        if (
            isinstance(s, dict)
            and s.get("id") == image_slot
            and s.get("spread_idx") == spread_idx
        ):
            aspect = s.get("aspect", aspect)
            break
    image_block: dict = {
        "source_path": f"images/spread-{spread_idx:02d}/{image_slot}.png",
        "crop_rect_norm": [0.0, 0.0, 1.0, 1.0],
        "fit_mode": "cover",
    }
    if aspect:
        image_block["natural_aspect"] = aspect

    out: dict = {
        "id": region.get("id", image_slot),
        "rect_norm": rect_norm,
        "rect_px": rect_px,
        "role": "image",
        "z_index": int(region.get("z_index", 0)),
        "image": image_block,
    }
    # claim.proof_object.ref points to the image_slot (e.g. 'feature_hero'),
    # not the region id (e.g. 'hero_image'). Match against the slot.
    cr = _image_claim_role(image_slot, claim_entry) or _image_claim_role(out["id"], claim_entry)
    if cr:
        out["claim_role"] = cr
    return out


def _expand_image_grid(
    region: dict,
    *,
    rect_norm: list,
    spread_idx: int,
    image_slots_layout: list[dict],
    canvas_w_px: float,
    canvas_h_px: float,
    claim_entry: dict | None,
) -> list[dict]:
    image_slots = list(region.get("image_slots") or [])
    n = len(image_slots)
    if n == 0:
        return []
    grid_cols = max(1, int(region.get("grid_cols", n)))
    grid_rows = (n + grid_cols - 1) // grid_cols

    x0, y0, x1, y1 = rect_norm
    cell_w = (x1 - x0) / grid_cols
    cell_h = (y1 - y0) / grid_rows

    out: list[dict] = []
    for i, slot in enumerate(image_slots):
        row = i // grid_cols
        col = i % grid_cols
        sub_norm = [
            x0 + col * cell_w,
            y0 + row * cell_h,
            x0 + (col + 1) * cell_w,
            y0 + (row + 1) * cell_h,
        ]
        sub_px = _compute_rect_px(sub_norm, canvas_w_px, canvas_h_px)

        aspect = ""
        for s in image_slots_layout:
            if (
                isinstance(s, dict)
                and s.get("id") == slot
                and s.get("spread_idx") == spread_idx
            ):
                aspect = s.get("aspect", "")
                break

        image_block: dict = {
            "source_path": f"images/spread-{spread_idx:02d}/{slot}.png",
            "crop_rect_norm": [0.0, 0.0, 1.0, 1.0],
            "fit_mode": "cover",
        }
        if aspect:
            image_block["natural_aspect"] = aspect

        item: dict = {
            "id": slot,
            "rect_norm": sub_norm,
            "rect_px": sub_px,
            "role": "image",
            "z_index": int(region.get("z_index", 0)),
            "image": image_block,
        }
        cr = _image_claim_role(slot, claim_entry)
        if cr:
            item["claim_role"] = cr
        out.append(item)
    return out


def _build_text_region(
    region: dict,
    *,
    rect_norm: list,
    rect_px: list,
    spread_idx: int,
    spread_type: str,
    copy_entry: dict,
    article: dict,
    locale: str,
    design_tokens: dict,
) -> dict:
    region_id = region.get("id", "")
    component = region.get("component", "")
    text_field = region.get("text_field")

    # Resolution order: explicit literal_text → article text_field → hardcoded
    # spread/region literal default → leave text absent.
    text = region.get("literal_text")
    if isinstance(text, dict):
        text = _localize(text, locale)
    elif not isinstance(text, str):
        text = None
    if not text and isinstance(text_field, str) and text_field:
        text = _resolve_text_field(text_field, copy_entry, article, locale)
    if not text:
        slot_default = _DEFAULT_LITERAL_TEXT.get(spread_type, {}).get(region_id)
        if slot_default:
            text = _localize(slot_default, locale)

    typography_slot = _COMPONENT_TO_TYPOGRAPHY_SLOT.get(component, "body")
    typography = (design_tokens.get("typography") or {}).get(typography_slot)

    out: dict = {
        "id": region_id,
        "rect_norm": rect_norm,
        "rect_px": rect_px,
        "role": "text",
        "z_index": int(region.get("z_index", 0)),
    }
    if text:
        out["text"] = text
    if component:
        out["component"] = component
    cp = region.get("component_props")
    if isinstance(cp, dict) and cp:
        out["component_props"] = dict(cp)
    if isinstance(typography, dict):
        out["typography"] = dict(typography)

    if isinstance(text_field, str) and text_field:
        if text_field in ("cover_kicker", "cover_line", "masthead_override"):
            out["bind_field"] = text_field
        else:
            out["bind_field"] = f"spread.{spread_idx}.{text_field}"
        if text_field in _TEXT_FIELD_CLAIM_ROLE:
            out["claim_role"] = _TEXT_FIELD_CLAIM_ROLE[text_field]

    if int(region.get("z_index", 0)) > 0:
        out["text_safe_required"] = True

    return out


def _build_accent_or_decorative(
    region: dict,
    *,
    rect_norm: list,
    rect_px: list,
    design_tokens: dict,
) -> dict:
    component = region.get("component", "")
    if component == "AccentRule":
        accent_color = (
            (design_tokens.get("color_palette") or {}).get("accent") or "#000000"
        )
        return {
            "id": region.get("id", ""),
            "rect_norm": rect_norm,
            "rect_px": rect_px,
            "role": "accent",
            "z_index": int(region.get("z_index", 0)),
            "accent": {
                "color": accent_color,
                "thickness_pt": 0.75,
                "style": "hairline",
            },
        }
    # Anything else (VerticalGradient, decorative shapes) → decorative.
    out: dict = {
        "id": region.get("id", ""),
        "rect_norm": rect_norm,
        "rect_px": rect_px,
        "role": "decorative",
        "z_index": int(region.get("z_index", 0)),
    }
    if component:
        out["component"] = component
    cp = region.get("component_props")
    if isinstance(cp, dict) and cp:
        out["component_props"] = dict(cp)
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def compute_design_tokens(brand: dict, design_system: dict) -> dict:
    """Compose typography + color_palette + margins from brand and design_system."""
    brand = brand or {}
    design_system = design_system or {}
    brand_typo = brand.get("typography") or {}
    ds_typo = design_system.get("typography_resolution") or {}
    visual = brand.get("visual_tokens") or {}
    print_specs = brand.get("print_specs") or {}

    typography: dict = {}
    for slot in sorted(set(brand_typo) | set(ds_typo)):
        if slot in ("pairing_notes",):
            continue
        b = brand_typo.get(slot) or {}
        d = ds_typo.get(slot) or {}
        if not isinstance(b, dict):
            b = {}
        if not isinstance(d, dict):
            d = {}

        desired = d.get("desired_family") or b.get("family")
        if not desired:
            continue
        chain: list[str] = [desired]
        for f in (d.get("fallback_chain") or []):
            if isinstance(f, str) and f and f not in chain:
                chain.append(f)
        if not any(
            isinstance(f, str) and f.lower() in ("serif", "sans-serif", "monospace")
            for f in chain
        ):
            chain.append("monospace" if slot in ("meta", "kicker", "page_number") else "serif")

        ts: dict = {"family_chain": chain}
        if isinstance(b.get("size_pt"), (int, float)):
            ts["size_pt"] = float(b["size_pt"])
        weights = b.get("weights")
        if isinstance(weights, list) and weights:
            ts["weight"] = int(weights[0])
        elif isinstance(b.get("weight"), int):
            ts["weight"] = b["weight"]
        if isinstance(b.get("style"), str) and b["style"] in ("normal", "italic", "oblique"):
            ts["style"] = b["style"]
        if isinstance(b.get("leading"), (int, float)):
            ts["line_height"] = float(b["leading"])
        ls = b.get("letter_spacing")
        if isinstance(ls, str):
            try:
                ts["letter_spacing"] = float(ls.rstrip("em").rstrip("ex").strip())
            except ValueError:
                pass
        elif isinstance(ls, (int, float)):
            ts["letter_spacing"] = float(ls)
        if isinstance(b.get("transform"), str) and b["transform"] in (
            "none", "uppercase", "lowercase", "capitalize"
        ):
            ts["transform"] = b["transform"]
        if slot in ("kicker", "meta"):
            color = visual.get("color_accent") or visual.get("color_ink_primary")
        else:
            color = visual.get("color_ink_primary")
        if isinstance(color, str):
            ts["color"] = _normalise_color(color)
        typography[slot] = ts

    palette: dict = {}
    if isinstance(visual.get("color_bg_paper"), str):
        palette["paper"] = _normalise_color(visual["color_bg_paper"])
    if isinstance(visual.get("color_ink_primary"), str):
        palette["ink"] = _normalise_color(visual["color_ink_primary"])
    if isinstance(visual.get("color_accent"), str):
        palette["accent"] = _normalise_color(visual["color_accent"])
    if isinstance(visual.get("color_ink_secondary"), str):
        palette["muted"] = _normalise_color(visual["color_ink_secondary"])

    margins = None
    margin_keys = ("margin_top_mm", "margin_bottom_mm", "margin_outer_mm", "margin_inner_mm")
    if all(isinstance(print_specs.get(k), (int, float)) for k in margin_keys):
        margins = {
            "top": float(print_specs["margin_top_mm"]),
            "bottom": float(print_specs["margin_bottom_mm"]),
            "outer": float(print_specs["margin_outer_mm"]),
            "inner": float(print_specs["margin_inner_mm"]),
            "unit": "mm",
        }

    tokens: dict = {"typography": typography, "color_palette": palette}
    if margins:
        tokens["margins"] = margins
    return tokens


def augment_target(target: dict, brand: dict) -> dict:
    """Fill / normalise target.page_size / bleed / dpi.

    Accepts page_size as either a structured dict (already-augmented) or a
    short string code ('A4') / absent (pull from brand.print_specs or
    target.slide_size).
    """
    out = dict(target)
    out.setdefault("realizer", "weasyprint")

    page_size = out.get("page_size")
    if not isinstance(page_size, dict):
        # Need to resolve the structured form.
        print_specs = (brand or {}).get("print_specs") or {}
        code = page_size if isinstance(page_size, str) else print_specs.get("page_size")
        custom = print_specs.get("page_size_custom_mm")
        resolved: dict | None = None
        if isinstance(custom, list) and len(custom) == 2:
            resolved = {"width": float(custom[0]), "height": float(custom[1]), "unit": "mm"}
        elif code == "A4":
            resolved = {"width": 210, "height": 297, "unit": "mm"}
        elif code == "A5":
            resolved = {"width": 148, "height": 210, "unit": "mm"}
        elif code == "letter":
            resolved = {"width": 215.9, "height": 279.4, "unit": "mm"}
        elif isinstance(target.get("slide_size"), str) and "x" in target["slide_size"]:
            w_s, h_s = target["slide_size"].split("x")
            try:
                resolved = {"width": float(w_s), "height": float(h_s), "unit": "px"}
            except ValueError:
                resolved = None
        if resolved is not None:
            out["page_size"] = resolved
        else:
            out.pop("page_size", None)

    if "bleed" not in out:
        print_specs = (brand or {}).get("print_specs") or {}
        bleed_mm = target.get("bleed_mm") or print_specs.get("bleed_mm")
        if isinstance(bleed_mm, (int, float)):
            out["bleed"] = {"value": float(bleed_mm), "unit": "mm"}

    if "dpi" not in out:
        unit = (out.get("page_size") or {}).get("unit")
        out["dpi"] = 300 if unit == "mm" else 96

    # Drop legacy / pre-augment fields we've already absorbed.
    for legacy in ("slide_size", "page_count", "purpose", "bleed_mm"):
        out.pop(legacy, None)

    return out


def _slide_canvas_px(target: dict, pages_per_instance: int) -> tuple[float, float]:
    ps = target.get("page_size") or {}
    w = float(ps.get("width", 0))
    h = float(ps.get("height", 0))
    if ps.get("unit") == "mm":
        dpi = float(target.get("dpi", 300))
        w = w * dpi / 25.4
        h = h * dpi / 25.4
    return w * pages_per_instance, h


def _compute_rect_px(rect_norm: list, canvas_w_px: float, canvas_h_px: float) -> list[int]:
    x0, y0, x1, y1 = rect_norm
    return [
        int(round(x0 * canvas_w_px)),
        int(round(y0 * canvas_h_px)),
        int(round(x1 * canvas_w_px)),
        int(round(y1 * canvas_h_px)),
    ]


def _localize(value: Any, locale: str) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        if locale in value and isinstance(value[locale], str) and value[locale]:
            return value[locale]
        for v in value.values():
            if isinstance(v, str) and v:
                return v
    return None


def _resolve_text_field(
    text_field: str, copy_entry: dict, article: dict, locale: str
) -> str | None:
    if text_field in copy_entry:
        result = _localize(copy_entry[text_field], locale)
        if result is not None:
            return result
    if text_field in article:
        return _localize(article[text_field], locale)
    return None


def _image_claim_role(image_id: str, claim_entry: dict | None) -> str | None:
    """Return 'proof_object' if image_id is referenced by claim_entry.proof_object.ref."""
    if not isinstance(claim_entry, dict):
        return None
    proof = claim_entry.get("proof_object")
    if not isinstance(proof, dict):
        return None
    ref = proof.get("ref", "")
    if not isinstance(ref, str) or not ref:
        return None
    if ref == image_id:
        return "proof_object"
    bracket = ref.find("[")
    if bracket > 0:
        prefix = ref[:bracket].rstrip(".")
        id_dot = image_id.find(".")
        id_prefix = image_id if id_dot < 0 else image_id[:id_dot]
        if id_prefix == prefix:
            return "proof_object"
    return None


def _normalise_color(s: str) -> str:
    """Uppercase the hex digits so the manifest passes the schema's color regex."""
    s = s.strip()
    if s.startswith("#") and len(s) in (4, 7, 9):
        return "#" + s[1:].upper() if len(s) in (7, 9) else "#" + s[1].upper() * 2 + s[2].upper() * 2 + s[3].upper() * 2
    return s


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("spec_path", type=pathlib.Path,
                   help="Path to a library/issue-specs/<slug>.yaml")
    p.add_argument("--target", default="a4-magazine",
                   help="Target format (e.g. a4-magazine, magazine-pptx)")
    p.add_argument("--locale", default="en")
    p.add_argument("--output", default="-",
                   help="Output path or '-' for stdout")
    args = p.parse_args(argv)

    manifest = build_from_spec_path(
        args.spec_path,
        target_format=args.target,
        locale=args.locale,
    )
    text = json.dumps(manifest, indent=2, ensure_ascii=False)
    if args.output == "-":
        print(text)
    else:
        pathlib.Path(args.output).write_text(text, encoding="utf-8")
        print(f"wrote {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
