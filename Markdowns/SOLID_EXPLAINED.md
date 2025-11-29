# SOLID Principles Used in the Adzuna Job Matching App

This project was intentionally structured to demonstrate **SOLID software engineering principles**, making the application modular, maintainable, testable, and extendable.

Below is a breakdown of **each SOLID principle** and where it appears in the codebase.

---

# 🟦 S — Single Responsibility Principle (SRP)

Each component has **one job**:
- Fetcher
- Cleaner
- Scrubber
- Formatter
- Embedder
- Similarity module
- Pipeline orchestrator
- GUI

---

# 🟩 O — Open/Closed Principle (OCP)

Modules are open for extension but closed for modification.
New fetchers, embedders, or similarity models can be added without editing the pipeline.

---

# 🟧 L — Liskov Substitution Principle (LSP)

All major components follow small interfaces, so any implementation can be swapped in:
- IEmbedder
- IFetcher
- ICleaner
- IScrubber
- IFormatter

---

# 🟥 I — Interface Segregation Principle (ISP)

Interfaces are small and focused. No bloated "God interfaces".

---

# 🟪 D — Dependency Inversion Principle (DIP)

High-level modules (Pipeline, GUI) do not instantiate concrete classes.
Dependencies are passed in.

This keeps everything modular, testable, and extendable.
