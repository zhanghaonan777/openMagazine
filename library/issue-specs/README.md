# Issue Specs Library

Each `<slug>.yaml` is one **complete issue specification** that references
5 layers (subject / style / theme / layout / brand) by name and optionally
overrides individual fields.

When a free-form simple-mode run reaches the storyboard gate (Phase 2.5),
the agent **auto-persists** the resolved configuration here, so subsequent
runs can use spec input directly:

```
"用 cosmos-luna-01 spec 跑"
```

## Shipped examples

| File | Configuration | Notes |
|---|---|---|
| `cosmos-luna-01.yaml` | luna × matisse-fauve × cosmos × plain-16 × meow-life | full-issue example, not yet run |
| `naipi-burberry-4page-01.yaml` | naipi × burberry-heritage × burberry-uk × plain-4 × naipi-mag | reverse-persisted from 2026-05-10 successful run |

## Naming convention

Recommended: `<theme>-<subject>-<NN>` for full issues, or
`<subject>-<theme/style>-<page-count>page-<NN>` for ad-hoc / smoke tests.
The slug becomes `output/<slug>/` directory name.

## Validation

```bash
python helpers/spec_validate.py templates/issue-specs/cosmos-luna-01.yaml
```

Exit 0 = valid. Non-zero with diagnostics if not.

See `templates/SCHEMA.md` for the full schema.
