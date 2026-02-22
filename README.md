# App Builder Agent

An AI-powered website/app generator that takes a natural language prompt and creates a complete project scaffold (HTML/CSS/JS and docs) in `generated_project/`.

## What This Project Is

This repository is the **builder itself** (planner + architect + coder agents), not a single generated website.

Workflow:
1. You enter a project prompt.
2. The planner creates a structured plan.
3. The architect converts it into implementation steps.
4. The coder writes project files into `generated_project/`.

## Tech Stack

- Python 3.11+
- LangGraph
- LangChain
- Groq LLM (`openai/gpt-oss-120b`)
- Pydantic

## Repository Structure

```text
.
├─ main.py                 # CLI entrypoint
├─ agent/
│  ├─ graph.py             # planner/architect/coder graph
│  ├─ prompts.py           # prompt templates
│  ├─ states.py            # pydantic state models
│  └─ tools.py             # file and command tools
├─ generated_project/      # output folder for generated projects
├─ pyproject.toml
└─ README.md
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -e .
   ```
3. Add your Groq API key in `.env`:
   ```env
   GROQ_API_KEY=your_key_here
   ```

## Usage

Run:

```bash
python main.py
```

Then enter a prompt, for example:

`Build a responsive expense tracker using HTML, CSS, and vanilla JS with add/edit/delete, filters, search, totals, and localStorage. Create index.html, styles.css, script.js, README.md.`

Generated files will be written to:

`generated_project/`

## Notes

- The generated app is static frontend code by default unless your prompt asks otherwise.
- If you rerun with a new prompt, files in `generated_project/` can be overwritten.
