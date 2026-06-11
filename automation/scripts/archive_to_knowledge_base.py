#!/usr/bin/env python3
from design_knowledge_engine import main


if __name__ == "__main__":
    raise SystemExit(main(["confirm", *(__import__("sys").argv[1:])]))
