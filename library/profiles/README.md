# library/profiles/

Closed registry of publication-type profiles. A profile carries the
hard gates, required proof objects, visual preferences, and banned
motifs for one *kind* of publication (`consumer-retail`, `finance-ir`,
`engineering-platform`, etc.).

Profiles are referenced by `library/design-systems/<slug>.yaml.profile`
and surface in directors / article-writer / image-prompt construction
to enforce the profile's editorial rules.

This file layout mirrors `library/components/registry.yaml`'s
closed-set philosophy from v0.3.1: agents can't invent a new profile
name — adding one is a small PR.

## Adding a new profile

1. Author the yaml file. Use an existing profile (e.g.
   `consumer-retail.yaml`) as a template.
2. Map `presentations_profile` to one of Codex Presentations skill's
   10 profile names (see `~/.codex/plugins/cache/openai-primary-runtime/
   presentations/26.506.11943/skills/presentations/profiles/`).
3. List hard gates, required proof objects, visual preferences.
4. Run `tools/validation/design_system_validate.py` against an example
   design-system that references the new profile.
5. Update `docs/profiles-reference.md`.
