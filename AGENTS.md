# AGENTS.md

You are working in the open-source Design-Knowledge-Engine package.

## Scope

This repository contains only the local workflow automation code and mock folder structure.

Allowed work:

- Bug fixes
- Stability fixes
- Documentation
- Example configuration
- Local workflow validation

Do not add:

- Retrieval system implementation
- Agents
- Embeddings
- Vector databases
- Cloud sync
- Web services
- Private knowledge base content

## Privacy Rules

Never commit:

- Real images
- Private design assets
- Private business data
- Customer data
- Production database files
- Runtime logs
- Private knowledge base notes

Use only mock files in `sample_data/` and `sample_output/`.

## Local Workflow

```text
sample_data/inbox/01_new_images
scan
sample_output/inbox/02_pending_analysis
analyze
sample_output/inbox/03_pending_confirm
confirm
sample_output/assets/reviewed
sample_output/knowledge_base/09_image_analysis_archive
```
