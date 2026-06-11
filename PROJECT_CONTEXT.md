# Project Context

## Project Name

Design-Knowledge-Engine

## Positioning

Design-Knowledge-Engine is a local-first workflow that turns visual inspiration into structured Markdown knowledge cards.

It validates a simple local workflow:

```text
Images
→ AI Analysis
→ Structured Tags
→ Markdown Cards
→ Knowledge Base
```

## Current Scope

This open-source version focuses on the local workflow only.

In scope:

- Directory scaffolding
- File movement
- SHA256 deduplication
- Runtime index maintenance
- Markdown card generation
- Event history
- Runtime logs
- Reserved future fields

Out of scope:

- Retrieval system implementation
- Agent implementation
- Embedding generation
- Vector database
- Web service
- User accounts
- Cloud synchronization

## Optional Markdown Tools

Generated files are standard Markdown. They can be used with Obsidian, VS Code, Typora, Logseq, or any Markdown-based knowledge system.

## Privacy Boundary

The open-source package must not contain private knowledge base content, real images, private business documents, case study images, or production logs.

Use `sample_data/` and `sample_output/` for mock local tests only.
