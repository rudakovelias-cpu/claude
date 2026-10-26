---
name: miro-mindmap
description: Build beautiful, readable mind maps on a Miro board via the Miro MCP (canvas_create_from_svg). Use when the user asks for a mind map, concept map, idea map or topic breakdown on Miro. Covers structure, layout math, palette, typography, connectors and a self-check loop.
---

# Miro mind map

A mind map here is a hand-assembled diagram of shapes + connectors on the Miro canvas.
This skill adds design discipline on top of Miro's own guides. It does not replace them.

## 0. Required order of calls (Miro MCP)

1. `canvas_get_canvas_composer_skill` with no step, then `step="design"`, then `step="dsl"`.
   The `dsl` result is huge (about 65k characters) and gets saved to a file; read it with `jq -r .skill <file>` in slices.
2. `canvas_load_format_skill(format_name="diagramming", notation="free_form")`. Do NOT pass `renderer="native"`: free_form has no native target and errors.
3. Confirm with the user before `board_create` (it cannot be undone). Prefer an existing board if the user gave a URL.
4. Build with `canvas_create_from_svg`, then verify with `canvas_read_as_svg`, then fix with `canvas_update_from_svg`.
5. Call `board_show` once at the end. Do not paste the link in text yourself.

## 1. Content first (before any pixels)

- One central idea, 3 to 7 first-level branches, max 3 levels deep, max 5 children per node (6 at the root level is fine).
- Labels are 1 to 5 words. Nouns and short verb phrases. No sentences, no emojis, no em dashes.
- Group by meaning, not by the order the user typed. Merge duplicates. Keep the user's wording where it is already short.
- If the source is bigger than this, split into several maps (one per branch) rather than shrinking text.

## 2. Visual thesis

State one sentence before drawing, for example: "Calm paper-cut map: one bold center, six colour-coded branches that fade from solid to faint toward the leaves."
Everything below serves that sentence.

## 3. Palette (Miro "Bright Paper")

Only these hex values. Tones within a family never mix with another family.

| Family | Faint | Light | Medium | Dark |
|---|---|---|---|---|
| yellow | #fffbed | #fff6b6 | #ffdc4a | #af7e04 |
| orange | #fff5ed | #f8d3af | #fe9f4d | #9b4a08 |
| red | #fff0f0 | #ffc6c6 | #ff6464 | #bd0a0a |
| green | #eaf9ef | #adf0c7 | #2dc75c | #067429 |
| blue | #f0f5fd | #c6dcff | #659df2 | #305bab |
| purple | #f4f2fd | #dedaff | #8f7fee | #6631d7 |

Neutrals: canvas #ffffff, headline ink #1a1a1a, body ink #595959, connector fallback #313131, dividers #b0b0b0.

Rules:
- One family per first-level branch. All descendants stay in that family.
- Tone fades with depth: level 1 = medium fill, level 2 = light fill, level 3 = faint fill.
- Stroke and text of a node use the same family's dark tone. Exception: text on a medium fill uses #1a1a1a for contrast.
- Connector colour = the branch's medium tone, stroke-width 3 for root-to-branch, 2 below.
- Deliberate deviation from Miro's "max 3 families" rule: a mind map may use up to 6 because colour is the branch category. Use fewer when there are fewer branches. Never use grey or black fills.
- Root: white fill, #1a1a1a stroke width 3, #1a1a1a bold text. Do not make it a dark block.
- Meaning colours stay stable: avoid red/green for branches unless the branch really means bad/good.
- No gradients, shadows, dashed borders, icons or decorative symbols.

## 4. Typography

One font only: Noto Sans (`data-font-family="noto_sans"`), bold for root and level 1, regular for deeper levels.

| Role | font-size | weight |
|---|---|---|
| Map title (standalone textArea above the map) | 33 | bold |
| Root | 33 | bold |
| Level 1 | 22 | bold |
| Level 2 | 18 | regular |
| Level 3 | 13 | regular |

Sizes come from Miro's allowed display ramp. Never shrink text to fit; widen the node or shorten the label.

## 5. Geometry and layout math

Spacing scale only: 10, 20, 32, 64, 160, 320.

Node sizes (siblings always identical):

| Role | width x height | shape |
|---|---|---|
| Root | 360 x 120 | `round_rectangle`, rx 62 |
| Level 1 | 280 x 72 | `round_rectangle`, rx 36 |
| Level 2 | 240 x 56 | `round_rectangle`, rx 28 |
| Level 3 | 200 x 48 | `round_rectangle`, rx 24 |

Pill shapes keep the map friendly. Use the same shape family at every level.

Layout (horizontal tree, root in the middle):
1. Split level-1 branches into a left half and a right half with roughly equal LEAF counts (not equal branch counts). Order clockwise from top-right.
2. Horizontal distance between a parent's near edge and its child's near edge: 160 for root-to-L1, 64 below. Keep one distance per level.
3. Vertical: each leaf takes a slot of (node height + 20). Between sibling groups of different parents add 64 extra.
4. A parent's height-span is the sum of its children's slots. Centre the parent vertically on its children's span.
5. Centre the root at the vertical middle of the left and right stacks. Left side mirrors right.
6. Place a bold title textArea (33) 64 above the top-most node, aligned to the root's left edge. Do not put it in a coloured box.
7. Never overlap, never touch. Whole map stays within one composition. No stray elements in dead canvas.

Do not wrap the map in a frame unless the user asks. If framing, one frame, white fill, padding 64 on all sides, title inside.

## 6. Connectors

- Every link is a `<line>` with `data-start` and `data-end` (node ids) and `data-shape="elbowed"`. Never curved, never free-floating.
- Right half: `data-start-side="right"` to `data-end-side="left"`. Left half: `"left"` to `"right"`.
- No arrowheads on a mind map (omit `data-arrow`).
- A child connects only to its own parent.

## 7. SVG skeleton

```xml
<svg>
  <textArea id="title" x="..." y="..." width="900" font-size="33" font-weight="bold" font-family="noto_sans" fill="#1a1a1a">Topic</textArea>
  <rect id="root" x="..." y="..." width="360" height="120" rx="62" fill="#ffffff" stroke="#1a1a1a" stroke-width="3"
        data-content="Central idea" data-text-color="#1a1a1a" data-font-size="33" data-font-weight="bold" data-font-family="noto_sans"/>
  <rect id="b1" x="..." y="..." width="280" height="72" rx="36" fill="#659df2" stroke="#305bab" stroke-width="2"
        data-content="Branch" data-text-color="#1a1a1a" data-font-size="22" data-font-weight="bold" data-font-family="noto_sans"/>
  <rect id="b1a" x="..." y="..." width="240" height="56" rx="28" fill="#c6dcff" stroke="#305bab" stroke-width="2"
        data-content="Sub topic" data-text-color="#305bab" data-font-size="18" data-font-family="noto_sans"/>
  <line x1="..." y1="..." x2="..." y2="..." stroke="#659df2" stroke-width="3" data-shape="elbowed"
        data-start="root" data-end="b1" data-start-side="right" data-end-side="left"/>
</svg>
```

Generate coordinates with a small script rather than by hand, so spacing is exact. Build the tree as data, compute slots (section 5), emit the SVG.

## 8. Self-check loop (always run)

After creating, call `canvas_read_as_svg` on the new items and check:
- [ ] No overlaps or touching nodes; gaps match the spacing scale.
- [ ] Every connector has both endpoints attached and uses the right sides.
- [ ] Siblings have identical sizes and tones; tone fades by depth.
- [ ] One font, sizes only from the table, text not clipped (long labels need a wider node, not a smaller font).
- [ ] Squint test: at overview zoom you can name the central idea and the branches.
Fix with `canvas_update_from_svg`, re-read, repeat until clean.

## 9. Do not

- Do not use Miro sticky notes for a mind map (they do not fit this style).
- Do not invent colours, mix tones across families, or use black fills.
- Do not exceed 3 levels or 5 children per node to "be complete".
- Do not add content the user did not give or imply.
