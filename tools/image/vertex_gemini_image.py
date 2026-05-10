"""Vertex Gemini 3 Pro Image — 4K page generation with multi-reference support.

Replaces helpers/vertex_image.py:generate_page from the predecessor
only_image_magazine_gen. Refactored into a BaseTool subclass.
"""
from __future__ import annotations

import os
import pathlib
import sys
import time
from typing import Optional

from tools.base_tool import BaseTool

DEFAULT_PROJECT = "project-5e0283e4-4d09-4f51-a5f"
DEFAULT_PROXY = "http://127.0.0.1:7897"
GEMINI_MODEL = "gemini-3-pro-image-preview"
GEMINI_LOCATION = "global"
SKIP_MIN_BYTES = 5 * 1024 * 1024


class VertexGeminiImage(BaseTool):
    capability = "image_generation"
    provider = "vertex"
    cost_per_call_usd = 0.24    # 4K Gemini 3 Pro
    agent_skills = ["vertex-gemini-image-prompt-tips"]
    status = "active"

    def run(
        self,
        prompt: str,
        out_path: pathlib.Path,
        *,
        refs: list[pathlib.Path],
        aspect: str = "2:3",
        size: str = "4K",
        skip_existing: bool = False,
    ) -> pathlib.Path:
        """Generate one image using one or more reference images.

        First ref dominates composition; subsequent refs anchor character.
        """
        if self._should_skip(out_path, skip_existing):
            return out_path
        if not refs:
            raise ValueError("at least one reference image required")

        ref_bytes = [pathlib.Path(p).read_bytes() for p in refs]
        return self._generate(prompt, ref_bytes, aspect, size, out_path)

    def probe(self) -> int:
        """Connectivity check. Prints diagnostics and returns 0 if OK."""
        self._ensure_proxy()
        proxy = os.environ.get("HTTPS_PROXY", "(none)")
        project = os.environ.get("OPEN_ZAZHI_GCP_PROJECT", DEFAULT_PROJECT)
        print(f"proxy        = {proxy}", file=sys.stderr)
        print(f"project      = {project}", file=sys.stderr)
        print(f"gemini model = {GEMINI_MODEL} @ {GEMINI_LOCATION}", file=sys.stderr)

        try:
            client = self._client()
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents="reply with the single word OK",
            )
            print(f"text probe   : {resp.text.strip()[:40]}", file=sys.stderr)
            return 0
        except Exception as e:
            print(f"text probe   : FAIL ({e})", file=sys.stderr)
            return 1

    # --- internals ---

    def _ensure_proxy(self) -> None:
        proxy = os.environ.get("OPEN_ZAZHI_PROXY", DEFAULT_PROXY)
        if proxy and proxy != "none":
            os.environ.setdefault("HTTPS_PROXY", proxy)
            os.environ.setdefault("HTTP_PROXY", proxy)

    def _client(self):
        from google import genai
        project = os.environ.get("OPEN_ZAZHI_GCP_PROJECT", DEFAULT_PROJECT)
        return genai.Client(vertexai=True, project=project, location=GEMINI_LOCATION)

    def _retry(self, func, attempts: int = 3, wait: float = 5.0):
        last_exc = None
        for i in range(1, attempts + 1):
            try:
                return func()
            except Exception as exc:
                msg = str(exc)
                transient = ("503" in msg) or ("UNAVAILABLE" in msg) or ("timeout" in msg.lower())
                if not transient or i == attempts:
                    raise
                last_exc = exc
                time.sleep(wait * i)
        if last_exc:
            raise last_exc

    def _extract_image(self, resp) -> bytes:
        for part in resp.candidates[0].content.parts:
            if getattr(part, "inline_data", None) and part.inline_data.data:
                return part.inline_data.data
        raise RuntimeError("No image part in response.")

    def _should_skip(self, out_path: pathlib.Path, skip_existing: bool) -> bool:
        if not skip_existing or not out_path.exists():
            return False
        if out_path.stat().st_size < SKIP_MIN_BYTES:
            return False
        print(f"[skip-existing] {out_path.name}", file=sys.stderr)
        return True

    def _generate(
        self,
        prompt: str,
        ref_bytes: list[bytes],
        aspect_ratio: str,
        image_size: str,
        out_path: pathlib.Path,
    ) -> pathlib.Path:
        self._ensure_proxy()
        client = self._client()
        from google.genai import types

        contents = [types.Part.from_bytes(data=b, mime_type="image/png") for b in ref_bytes]
        contents.append(prompt)

        config = types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(image_size=image_size, aspect_ratio=aspect_ratio),
        )

        def _call():
            return client.models.generate_content(
                model=GEMINI_MODEL, contents=contents, config=config,
            )

        t0 = time.time()
        resp = self._retry(_call)
        dt = time.time() - t0

        img_bytes = self._extract_image(resp)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(img_bytes)
        print(
            f"[vertex-gemini] {out_path.name}  {len(img_bytes)//1024} KB  {dt:.1f}s",
            file=sys.stderr,
        )
        return out_path


# Auto-register
from tools.tool_registry import registry  # noqa: E402

registry.register(VertexGeminiImage())
