# onboarding

Triggered when user input is vague (e.g., "what can you do?", "make me something"). Skip if user gave actionable input (e.g., "make a 4-page magazine of my cat in cosmos style").

## Behavior (target: <60s)

1. **Run capability discovery**:
   ~~~python
   from tools.tool_registry import registry, discover
   discover()
   catalog = registry.capability_catalog()
   ~~~

2. **Verify Codex `image_gen.imagegen` is available** (Stage 3 requires it):
   - If user is on Claude Code: STOP. See `CLAUDE.md`.

3. **Probe Vertex AI**:
   ~~~bash
   uv run python -c "from tools.image.vertex_gemini_image import VertexGeminiImage; VertexGeminiImage().probe()"
   ~~~

4. **Brief intro (1-2 sentences)**: "I can make cheap 4-page validation magazines or full v0.3 editorial A4 issues about a single subject (pet/person/place/product/concept). Editorial pipeline: research → proposal → articulate → storyboard → upscale → compose → publish."

5. **Show 3 starter prompts**:
   - "Make an editorial magazine of my <pet> in <style> style" (free-form input)
   - "Run with `library/issue-specs/cosmos-luna-may-2026.yaml`" (v0.3 spec input)
   - "Test with `pipeline_defs/smoke-test-4page.yaml`" (smoke test)

6. **Wait for user choice.** Do NOT proceed to any pipeline stage until the user gives an actionable instruction.

## See also

- `AGENT_GUIDE.md` — Rule Zero
- `CODEX.md` / `CLAUDE.md` — runtime adapters
