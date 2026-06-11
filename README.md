# Design Knowledge Engine

[![Tests](https://github.com/9z4k8fjtw4-dotcom/design-knowledge-engine/actions/workflows/test.yml/badge.svg)](https://github.com/9z4k8fjtw4-dotcom/design-knowledge-engine/actions/workflows/test.yml)
[![Latest Release](https://img.shields.io/github/v/release/9z4k8fjtw4-dotcom/design-knowledge-engine)](https://github.com/9z4k8fjtw4-dotcom/design-knowledge-engine/releases)
[![License](https://img.shields.io/github/license/9z4k8fjtw4-dotcom/design-knowledge-engine)](LICENSE)

Turn visual inspiration into structured knowledge.

A local-first workflow that converts image collections into searchable Markdown knowledge cards and automatically organizes them into a knowledge base.

```text
Images
↓
AI Analysis
↓
Structured Tags
↓
Markdown Cards
↓
Knowledge Base
```

Design Knowledge Engine is not a fashion project, not an AI model project, and not an Obsidian plugin. It is a local workflow engine for turning image collections into structured Markdown knowledge.

## Why It Exists

Visual research is easy to collect and hard to organize. Screenshots, references, mood boards, and downloaded images often stay trapped in folders with no reusable structure.

Design Knowledge Engine gives that collection a repeatable path:

- Local First
- Image Analysis
- Markdown Generation
- Knowledge Management
- Optional Obsidian Integration

## Quick Demo

Input:

```text
sample_data/garden_dress.jpg
```

Output:

```text
sample_output/garden_dress.md
```

Example Markdown card:

```markdown
# Garden Dress

## Summary

Romantic garden-inspired dress with soft pastel colors and floral details.

## Tags

* Garden
* Floral
* Romantic
* Pastel
* Lace
* Vintage

## Color Palette

* Cream White
* Soft Pink
* Sage Green

## Mood

* Gentle
* Dreamy
* Elegant

## Design Elements

* Lace trim
* Ribbon bow
* Floral embroidery
* Layered skirt

## Possible Use Cases

* Fashion Design
* Trend Research
* Inspiration Collection
```

## Core Capabilities

- Image scanning
- SHA256 hash deduplication
- State machine
- Event flow
- Markdown card generation
- Knowledge base archiving
- Reserved metadata fields for future retrieval or automation workflows

## Why Not Just Use ChatGPT?

Traditional AI chat analysis:

- One image at a time
- Difficult to organize
- Hard to build long-term knowledge

Design Knowledge Engine:

- Batch processing
- Structured outputs
- Searchable knowledge base
- Long-term visual knowledge accumulation

## Use Cases

- Fashion Design Research
- Architecture Reference Collection
- Interior Design Inspiration
- Illustration Style Library
- Photography Mood Boards
- Pinterest Archive Management

## Installation

Clone the repository:

```bash
git clone https://github.com/<your-account>/design-knowledge-engine.git
cd design-knowledge-engine
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on macOS / Linux:

```bash
source .venv/bin/activate
```

Activate it on Windows:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy the example config:

```bash
cp automation/config/settings.example.json automation/config/settings.json
```

Initialize runtime folders:

```bash
python automation/scripts/design_knowledge_engine.py init
```

## Usage

Scan new images:

```bash
python automation/scripts/design_knowledge_engine.py scan
```

Import a local image batch:

```bash
python automation/scripts/design_knowledge_engine.py import-batch
```

Generate placeholder analysis Markdown:

```bash
python automation/scripts/design_knowledge_engine.py analyze --tags reference image review
```

Regenerate Markdown:

```bash
python automation/scripts/design_knowledge_engine.py markdown
```

Confirm and archive:

```bash
python automation/scripts/design_knowledge_engine.py confirm --file filename.png --result review
```

Check status:

```bash
python automation/scripts/design_knowledge_engine.py status
```

## Optional Obsidian Integration

This project is not an Obsidian plugin.

This project does not install Obsidian.

This project does not depend on Obsidian.

Generated output is standard Markdown and can be used with:

- Obsidian
- VS Code
- Typora
- Logseq
- Any Markdown-based knowledge system

## State Machine

```text
new
pending_analysis
pending_confirm
archived
rejected
duplicate
error
```

## Event Flow

```text
New_Image_Event
Image_Indexed_Event
Image_Renamed_Event
Image_Analyzed_Event
Human_Confirmed_Event
Markdown_Archived_Event
```

## What is NOT included

This repository only contains the workflow engine.

Private assets are intentionally excluded:

- Design archives
- Commercial case studies
- Sales data
- Brand knowledge bases
- Proprietary design language systems
- Private image collections
- Internal business documents

## Roadmap

v0.1

Markdown workflow

v0.2

CLI package

v0.3

Batch tagging

v0.4

Embedding search

v1.0

Visual knowledge engine

## Data Privacy

Do not commit:

- Real user images
- Private design assets
- Customer data
- Production database files
- Runtime logs
- Private knowledge base notes

## Documentation

- [Directory Structure](docs/DIRECTORY_STRUCTURE.md)
- [Release Guide](docs/RELEASE_GUIDE.md)
- [GitHub Upload Guide](docs/GITHUB_UPLOAD_GUIDE.md)
- [Open Source Review](docs/OPEN_SOURCE_REVIEW.md)
- [Final Release Audit](docs/FINAL_RELEASE_AUDIT.md)
