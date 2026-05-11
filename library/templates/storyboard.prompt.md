OUTPUT IMAGE FORMAT (HARD CONSTRAINT):
- The OUTPUT IMAGE itself must be 2:3 PORTRAIT orientation (e.g., 1024×1536), NOT square.
- Inside that portrait canvas: a {{GRID_ROWS}}×{{GRID_COLS}} grid of {{PAGE_COUNT}} cells, each cell also 2:3 PORTRAIT.
- Page numbers ({{PAGE_NUMBER_RANGE}}) drawn inside each cell at the top-left.
- White ~24px gutters between cells and around the grid.
- DO NOT produce a square overall image. DO NOT produce landscape cells.

Generate a single image: a {{GRID_ROWS}}×{{GRID_COLS}} grid storyboard for a {{PAGE_COUNT}}-page photo magazine.

Layout: {{GRID_COLS}} columns × {{GRID_ROWS}} rows. Thin white gutters between cells. Each cell is a vertical 2:3 frame. Top-left of each cell shows a small page number {{PAGE_NUMBER_RANGE}}.

Subject in EVERY cell (locked, identical across all {{PAGE_COUNT}}):
{{TRAITS}}

Theme world: {{THEME_WORLD}}

Style locked across all cells: {{STYLE_ANCHOR}}

Page plan (each scene must be visually distinct; mix wide / medium / close-up / overhead; no two adjacent pages should share the same shot scale):

{{PAGE_PLAN_BLOCK}}

Overlay/layout contracts (use these when composing each cell; these same
contracts are reused by later 4K prompts and HTML/PDF overlays):

{{PAGE_CONTRACT_BLOCK}}

Constraints:
- SAME character across all cells (face / markings / build / baseline expression all identical).
- SAME color palette across all cells.
- SAME lighting language across all cells.
- Each cell is low-detail but composition and mood must read clearly.
- Keep protected subject zones clear of later overlay areas.
- Keep reserved overlay zones visually calm and free of faces, eyes, important props, or high-frequency detail.
- No text inside cells except the page number.
- No watermarks, no logos, no caption boxes.
