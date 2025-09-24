# FA-GPT Audit Snapshot

This snapshot includes only the files needed to understand the project architecture, pipelines, and configuration. It excludes datasets, caches, virtual environments, large binaries, and secrets.

Included (high level):
- app/: application source code (minus __pycache__ and data/)
- config/: configuration templates and settings (secrets filtered by pattern)
- init-db/: database init assets if any
- Top-level Python scripts and shell helpers
- Dockerfile(s), docker-compose.yml, requirements.txt
- Project docs (*.md)

Excluded:
- data/, images/, logs/, temp/, backups/, venv (fagpt_env), git history
- PDFs and large model binaries
- Secret-like files (*.env, *.pem, *.key, *secret*, *password*, *credentials*)

Integrity:
- See MANIFEST_FILES_SHA256.txt for filenames and SHA256 sums.

Provenance:
- Created at: 2025-09-24T00:10:05Z
- Source root: /home/drew/FA-GPT

