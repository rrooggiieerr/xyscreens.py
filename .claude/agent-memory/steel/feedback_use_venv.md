---
name: Use venv for pip packages
description: Always use Python virtual environments when installing and testing pip packages — never install globally.
type: feedback
---

Always use a virtual environment (venv) when installing and testing pip packages.

**Why:** User explicitly requested this. Avoids polluting the system Python and ensures reproducible environments.

**How to apply:** Before running `pip install` or `python -m pytest`, create/activate a venv first. When delegating to tungsten or other agents, include this as a MUST DO constraint.
