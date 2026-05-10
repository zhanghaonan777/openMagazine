# CODEX adapter — openMagazine

Codex CLI is the **default and recommended runtime** for openMagazine. Stage 3 (storyboard) requires `image_gen.imagegen` which only Codex provides.

## File capture plumbing

The `image_gen.imagegen` tool's response object does NOT expose bytes/url/path. The Codex CLI persists every generated PNG to:

```
~/.codex/generated_images/<session-uuid>/ig_<hash>.png
```

After `image_gen.imagegen` is called, the storyboard director MUST shell-capture the new PNG:

```bash
BEFORE=$(ls -t ~/.codex/generated_images/*/ig_*.png 2>/dev/null | head -1)
echo "${BEFORE:-NONE}" > /tmp/imagegen_before.txt

# < image_gen.imagegen is called >

sleep 1
AFTER=$(ls -t ~/.codex/generated_images/*/ig_*.png 2>/dev/null | head -1)
if [ -z "$AFTER" ] || [ "$AFTER" = "$(cat /tmp/imagegen_before.txt)" ]; then
  echo "ERROR: no new file. STOP."
  exit 1
fi
cp "$AFTER" output/<slug>/storyboard.png
```

## ABSOLUTE STOP RULE

If `image_gen.imagegen` fails or doesn't produce a new file, STOP. Do NOT fall back to PIL / Pillow / drawing primitives. Tell the user the error.

PIL mockup cells used as Phase 4 composition refs produce flat-shot-scale 4K outputs (validated failure mode in predecessor naigai-fauvist test, 2026-05-10).

## Skill installation

```bash
ln -s ~/github/openMagazine ~/.codex/skills/openmagazine
```

Codex auto-discovers on session start.
