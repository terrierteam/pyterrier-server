# PyTerrier Server 

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE.md)
[![PyTerrier](https://img.shields.io/badge/PyTerrier-Compatible-orange)](https://github.com/terrier-org/pyterrier)

A lightweight server for hosting and managing [PyTerrier](https://github.com/terrier-org/pyterrier) pipelines — with optional AI integration for dynamic pipeline selection via MCP.

---

## 📘 Overview

**PyTerrier Server** provides a simple way to deploy, expose, and manage information retrieval pipelines built with PyTerrier.  
It can run standalone or connect to an **MCP server**, which allows AI models to automatically choose the right pipeline for a given task.
An example on how the system works is the following:

![Demo Video](videos/demo.gif)

---

## 🚀 Getting Started

### 1. Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/<your-username>/pyterrier-server.git
cd pyterrier-server
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file based on the provided `.env.example` template:

```bash
cp .env.example .env
```

Then edit `.env` to include your configuration values.

---

## 🧩 Ensuring PyTerrier Compatibility

Some versions of PyTerrier may not include the `column_info` attribute within `pyterrier.model`.  
To ensure you’re using a compatible version, you can run the following script before starting the server:

```bash
#!/usr/bin/env bash

echo "🔍 Checking if pyterrier.model.column_info exists..."

python - <<'PYCODE'
import importlib, subprocess, sys
try:
    from pyterrier import model as pt_model
    _ = pt_model.column_info
    print("✅ pyterrier.model.column_info exists, skipping repo clone.")
except (ImportError, AttributeError):
    print("⚠️ pyterrier.model.column_info missing — cloning replacement repo.")
    subprocess.run(["git", "clone", "https://github.com/terrier-org/pyterrier.git", "pyterrier_src"], check=True)
    subprocess.run([sys.executable, "-m", "pip", "install", "--force-reinstall", "./pyterrier_src"], check=True)
PYCODE
```

> 💡 **Tip:** You can save this as a script (e.g., `check_pyterrier.sh`) and run it before deployment or server startup.

---

## ⚙️ Defining PyTerrier Pipelines

You can define one or more PyTerrier pipelines that the server will serve.

Set the `PYTERRIER_SERVER_PIPELINE` environment variable to:

- A **single pipeline definition**, or  
- A **YAML file** containing multiple pipelines.

Each pipeline in the YAML file must follow this structure:

```yaml
functions:
  - name: <pipeline name>
    task: <purpose>
    description: <detailed description>
    pipeline: |
      # Python code defining the pipeline
      # Must assign the final pipeline to a variable named 'p'
```

### Example

```yaml
functions:
  - name: MSMARCO-search
    task: search
    description: Use this function to retrieve relevant documents from the MSMARCO passage dataset using a BM25 index.
    pipeline: |
      import pyterrier_pisa, pyterrier as pt
      dataset = pt.get_dataset('irds:msmarco-passage')
      index = pyterrier_pisa.PisaIndex.from_hf('macavaney/msmarco-passage.pisa').bm25()
      p = index % 10 >> dataset.text_loader()
```

---

## 🖥️ Running the Server

PyTerrier Server consists of **two components**:

1. **MCP Server (optional)** — for AI-assisted pipeline selection.  
2. **Main Server** — the core service that executes your PyTerrier pipelines.

### 1. Run the MCP Server (Optional)

If you want to enable AI-based pipeline selection, start the MCP server:

```bash
export PYTERRIER_MCP=true  # Optional: helps separate logs between servers
python -m pyterrier_server._mcp_server
```

This runs the MCP server locally.  
To make it accessible to external AI models (e.g., OpenAI), you must expose it publicly. For local development, use [ngrok](https://ngrok.com/):

```bash
ngrok http 8000
```

> 💡 Tip: Any method that exposes your localhost to the internet will work (e.g., `localtunnel`, cloud hosting).

### 2. Run the Main Server

In another terminal window:

```bash
python -m pyterrier_server._server
```

If the main server can’t reach the MCP server, it will automatically hide the AI-assisted features.

---

## 👥 Authors

- [Akis Lionis](mailto:e.lionis.1@research.gla.ac.uk)  
- [Sean MacAvaney](mailto:Sean.MacAvaney@glasgow.ac.uk)

---

## 🧾 Version History

| Version | Date       | Changes                |
|----------|------------|------------------------|
| 0.1      | 2025-10-16 | Initial release        |

---


This project is licensed under the **MIT License** — see the [LICENSE.md](./LICENSE) file for details.
