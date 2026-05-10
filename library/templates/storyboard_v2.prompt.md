OUTPUT IMAGE FORMAT (HARD CONSTRAINT):
- The OUTPUT IMAGE itself must be 2:3 PORTRAIT orientation ({{OUTER_W}}×{{OUTER_H}}), NOT square.
- Inside that portrait canvas: a {{GRID_ROWS}}×{{GRID_COLS}} grid of {{CELL_COUNT}} cells.
- Each cell has its OWN aspect (not all uniform); see cell layout below.
- Page numbers labeled top-left of each cell.
- White ~24px gutters between cells and around the grid.

Generate one image: a multi-aspect editorial storyboard for a {{PAGE_COUNT}}-page magazine.

Subject in EVERY cell (locked, identical across all):
{{TRAITS}}

Theme world: {{THEME_WORLD}}

Style locked across all cells: {{STYLE_ANCHOR}}

CELL LAYOUT (page label - slot_id (intended aspect, role) - scene description):

{{CELL_LIST}}

Constraints:
- SAME character across all cells (face / markings / build / baseline expression).
- SAME color palette across all cells.
- SAME lighting language across all cells.
- Each cell is low-detail but composition + mood must read clearly.
- Each cell respects its declared intended aspect inside the cell rectangle.
- No text inside cells except the page label.
- No watermarks, no logos, no caption boxes.
