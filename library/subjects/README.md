# Subjects Library

Each `<name>.yaml` is one **protagonist** that can be referenced by an
issue spec. Stores: name, species, reference photo path, and the verbatim
traits string used as `{{TRAITS}}` across all 16 prompts.

When a free-form input run produces a new subject (e.g., agent inferred
traits from a photo), the agent auto-persists a new yaml here so the
next run can reference by name.

See `templates/SCHEMA.md` for the schema.

## Shipped seeds

| File | Subject | Use case |
|---|---|---|
| `luna.yaml` | British Shorthair cat | example for cosmos / shanghai-1930s themes |
| `naipi.yaml` | West Highland White Terrier-like dog | naipi-burberry-4page-01 spec example |
