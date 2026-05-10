# openMagazine

Agentic photo magazine generation skill, magazine-specialized adaptation of the OpenMontage architecture pattern.

## What it makes

A4 portrait PDF photo magazines. One subject (pet / person / place / product / concept) explored across N pages of 4K imagery with cover and back cover typography integrated into the photographs.

## Status

v0.1 (MVP). Single pipeline (`smoke-test-4page`) implemented. End-to-end runnable from a free-form input or a spec yaml.

## Quick start

~~~bash
git clone https://github.com/zhanghaonan777/openMagazine.git ~/github/openMagazine
cd ~/github/openMagazine
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# Verify Vertex auth (one-time)
gcloud auth login --no-launch-browser --update-adc
gcloud config set project <your-gcp-project-id>

# Symlink to codex skills directory
ln -s "$PWD" ~/.codex/skills/openmagazine
~~~

In a codex session:

~~~
make me a 4-page magazine of my <subject> in <style> style
~~~

## Architecture

See [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) for the architecture overview and file map.
See [`AGENT_GUIDE.md`](AGENT_GUIDE.md) for agent operating instructions.

## License

AGPLv3
