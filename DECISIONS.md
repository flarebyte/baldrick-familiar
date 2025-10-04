# Architecture decision records

An [architecture
decision](https://cloud.google.com/architecture/architecture-decision-records)
is a software design choice that evaluates:

- a functional requirement (features).
- a non-functional requirement (technologies, methodologies, libraries).

The purpose is to understand the reasons behind the current architecture, so
they can be carried-on or re-visited in the future.

## Idea

**Problem**
Design a Python-based MCP server running in Docker to support a Retrieval-Augmented Generation (RAG) workflow. The system must prioritize local execution on macOS with constrained memory (8GB RAM) using a small language model, ideally via Ollama, for responsiveness and stability. The primary goal is to provide efficient and easy access to both general documentation and project-specific knowledge.

---

**Use Cases**

- User queries a technical topic and receives a context-aware answer using indexed documentation.
- Access to markdown or code files in a documentation directory.
- Onboarding a new developer with answers sourced from internal knowledge.
- Quick retrieval of known issues or system design decisions.
- Search across project-specific artifacts (e.g., `README.md`, `/docs/`, code comments).
- Local-only setup without requiring internet access or API calls.

---

**Edge Cases**

- Handling of long documents exceeding model context length.
- System behavior when insufficient memory is available for model loading.
- Docker failing to allocate enough memory on macOS.
- Model not available locally and Ollama unable to pull due to offline constraints.
- Index needs rebuilding after documentation changes.
- Concurrent queries exceeding model or system capacity.
- Documents in unsupported formats (e.g., PDFs without parsing support).

---

**Limitations**

- Do not include large language models unsuitable for an 8GB RAM environment.
- Do not require cloud inference, APIs, or internet access at runtime.
- Do not attempt to extract from dynamic content like websites or JavaScript-heavy apps.
- Do not implement a full UI or web frontend — focus on backend only.
- Avoid tight coupling with macOS-specific APIs or paths — only optimize where needed.
