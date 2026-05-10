# codex-image-gen-plumbing

How to capture output from the Codex CLI's `image_gen.imagegen` tool.

## The problem

`image_gen.imagegen` does not return bytes / url / path / id in its tool response object. The image is shown in the chat UI but not directly addressable from the agent loop.

## The solution

Codex CLI persists every generated PNG to:

~~~
~/.codex/generated_images/<session-uuid>/ig_<hash>.png
~~~

Agents capture this via BEFORE/AFTER snapshot:

~~~bash
# 1. Snapshot before the call
BEFORE=$(ls -t ~/.codex/generated_images/*/ig_*.png 2>/dev/null | head -1)

# 2. Call image_gen.imagegen (agent action)

# 3. Snapshot after, find the new file
sleep 1
AFTER=$(ls -t ~/.codex/generated_images/*/ig_*.png 2>/dev/null | head -1)
if [ -z "$AFTER" ] || [ "$AFTER" = "$BEFORE" ]; then
  echo "no new file produced"; exit 1
fi
cp "$AFTER" /destination/path/output.png
~~~

## Verified end-to-end

Validated 2026-05-10: tomato test image, sub-agent independent lookup, view_image confirmation. Cross-process visible.

## Caveats

- File system flush latency exists; use `sleep 1` after the call.
- `multi_tool_use.parallel` does NOT include `image_gen.imagegen` — must be called serially.
- No URL or attachment_id is exposed; only filesystem capture works.
- The `<session-uuid>` directory is per-Codex-session; agents working across multiple sessions need to glob across all sessions.

## When NOT to fall back

If `image_gen.imagegen` fails or produces no new file, do NOT fall back to PIL / Pillow / drawing primitives. PIL-drawn placeholders used downstream as visual references corrupt the consistency of any storyboard-first pipeline.
