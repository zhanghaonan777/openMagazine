# codex-image-gen

`tools/image/codex_image_gen.py` — Codex CLI's native `image_gen.imagegen` wrapper.

## When to use

Stage 3 (storyboard generation). Codex CLI is the only runtime that exposes `image_gen.imagegen`. Claude Code does not have an equivalent — see `CLAUDE.md`.

## The wrapper does not call image_gen.imagegen itself

The Codex agent loop calls `image_gen.imagegen` as a Codex-level tool. This wrapper provides BEFORE/AFTER PNG capture plumbing because the tool's response object does NOT expose bytes/url/path.

## How to use

~~~python
from tools.image.codex_image_gen import CodexImageGen
import pathlib

tool = CodexImageGen()

# 1. Snapshot the BEFORE state
state = tool.run(mode="storyboard")  # returns {"before_path": ..., "ts": ...}

# 2. Agent issues image_gen.imagegen — the storyboard prompt etc.

# 3. Capture the new PNG that landed in ~/.codex/generated_images/
tool.capture_new_png(
    state,
    out_path=pathlib.Path("output/<slug>/storyboard.png"),
    timeout_seconds=5,
)
~~~

## Absolute STOP rule

If `image_gen.imagegen` fails or `capture_new_png` raises, STOP. Do NOT fall back to PIL / Pillow / drawing primitives. Tell the user.

## See also

- Layer 3 doc: `.agents/skills/codex-image-gen-plumbing.md` — file-capture protocol details
- `CODEX.md` — runtime adapter for the Codex CLI
- The full STOP rule lives in `CODEX.md`
