# Example Directory Structure

This repository uses mock folders for local tests. Do not place private production assets here.

```text
Design-Knowledge-Engine
├── AGENTS.md
├── DIRECTORY_STRUCTURE.md
├── PROJECT_CONTEXT.md
├── README.md
├── requirements.txt
├── sample_data
│   ├── README.md
│   ├── inbox
│   │   └── 01_new_images
│   └── image_batch
├── sample_output
│   ├── README.md
│   ├── assets
│   │   ├── archive
│   │   ├── raw
│   │   └── reviewed
│   ├── inbox
│   │   ├── 02_pending_analysis
│   │   ├── 03_pending_confirm
│   │   └── 04_rejected
│   └── knowledge_base
│       └── 09_image_analysis_archive
└── automation
    ├── config
    │   └── settings.example.json
    └── scripts
        ├── analyze_images.py
        ├── design_knowledge_engine.py
        ├── generate_markdown.py
        ├── archive_to_knowledge_base.py
        ├── rename_files.py
        └── watch_inbox.py
```

Runtime directories such as `automation/database/`, `automation/logs/`, and `sample_output/` are generated locally and ignored by Git.
