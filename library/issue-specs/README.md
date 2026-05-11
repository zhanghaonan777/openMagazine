# Issue Specs Library

Each `<slug>.yaml` is one **complete issue specification**. v1 specs reference
5 layers (subject / style / theme / layout / brand). v2 editorial specs use
those same references and may also reference an `article`.

When a free-form run resolves enough configuration, the agent
**auto-persists** it here, so subsequent runs can use spec input directly:

```
"用 cosmos-luna-01 spec 跑"
```

## Shipped examples

| File | Configuration | Notes |
|---|---|---|
| `cosmos-luna-01.yaml` | luna × matisse-fauve × cosmos × plain-16 × meow-life | legacy v1 full-issue example |
| `cosmos-luna-may-2026.yaml` | luna × national-geographic × cosmos × editorial-16page × meow-life × article | v0.3 editorial example |
| `naipi-burberry-4page-01.yaml` | naipi × burberry-heritage × burberry-uk × plain-4 × naipi-mag | reverse-persisted from 2026-05-10 successful run |

## Naming convention

Recommended: `<theme>-<subject>-<NN>` for full issues, or
`<subject>-<theme/style>-<page-count>page-<NN>` for ad-hoc / smoke tests.
The slug becomes `output/<slug>/` directory name.

## Validation

```bash
uv run python -m tools.validation.spec_validate library/issue-specs/cosmos-luna-01.yaml
uv run python -m tools.validation.spec_validate library/issue-specs/cosmos-luna-may-2026.yaml
```

Exit 0 = valid. Non-zero with diagnostics if not.

See `library/SCHEMA.md` for the full schema.
