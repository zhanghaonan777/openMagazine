# design-system-author

How an agent populates `library/design-systems/<slug>.yaml` from spec +
brand + theme + chosen profile.

## When to invoke

Stage 3 (articulate) of editorial pipelines. Called after article copy
is drafted; runs `resolve_design_system()` from `lib.design_system_loader`
and persists the result.

## Authoring rules

### 1. Profile selection (one of)

- `consumer-retail` — animal / person / product / lookbook / lifestyle.
  Default for openMagazine's current use cases.
- `finance-ir` — earnings / investor reviews / financial analysis.
- `product-platform` — SaaS / product narratives.
- `engineering-platform` — developer / AI / infrastructure decks.
- `gtm-growth` — growth / marketing / cohort stories.
- `strategy-leadership` — investor-day / board / strategy.
- `appendix-heavy` — tables / disclosures / source packs.

If spec doesn't dictate a profile, infer from theme + brand. For
openMagazine v0.3.2, default is `consumer-retail`.

### 2. Typography fallback chains

For each typography slot (`display`, `body`, `meta`):

- desired family: from `brand.typography.<slot>.family`
- fallback chain length ≥ 2:
  - 1st: a sibling-style family in the same flavor (e.g. Playfair
    Display → Source Serif 4)
  - 2nd: a system-safe family (Georgia / Times New Roman / Menlo /
    Courier)

Never let a chain be empty; never let it end without a system-safe
option.

### 3. Brand authenticity gates

For `consumer-retail` issues, always include:
- `do_not_generate`: at minimum `logo`, `mascot`, `app_icon`
- Specific brand-name approximations: include exact wordmarks the brand
  doesn't want approximated (e.g. "MEOW LIFE wordmark")

### 4. Output targets

If spec.output_targets is set, copy it through. If not, infer:
- editorial-16page layout + meow-life brand → `a4-magazine`
- explicit editable magazine/PPTX request → add `magazine-pptx`
  with `slide_size: 720x1080`, `page_count: 16`
- explicit pitch/share deck request → add `deck-pptx`
  with `slide_size: 1280x720`

### 5. Auto-persistence at the checkpoint

The resolved yaml lands at `library/design-systems/<slug>.yaml` BEFORE
the user sees the articulate checkpoint. User can edit at the
checkpoint; the edited yaml is what subsequent stages read.

## Self-review before persisting

- Every typography slot has fallback_chain ≥ 1 entry
- Brand authenticity matches the profile's `forbidden_generations`
- output_targets covers the user's actual request
- Validator passes

## See also

- `skills/meta/article-writer.md` — sibling pattern for article copy
- `library/profiles/<name>.yaml` — the profile being inherited
- `docs/design-system-reference.md` — the catalogue
