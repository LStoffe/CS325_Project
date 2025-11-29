# Refactoring Report — Adzuna Job Matching Application  
**CS 325 — Project 2 (Fall 2025)**

This document explains the refactoring process performed on the Adzuna Job Matching application, with emphasis on how the design was improved using **SOLID software engineering principles**. The goal of the refactor was to convert a monolithic, tightly coupled script into a modular, maintainable, testable, and extensible application.

---

# 1. Original Problems in the Initial Code

Before refactoring, the project suffered from the following issues:

### ❌ 1. Tight Coupling
- API fetching, resume cleaning, embedding, similarity scoring, GUI logic, and data formatting were all mixed together.
- Changing one part often broke another.

### ❌ 2. No Clear Separation of Concerns
- The GUI was performing business logic.
- Pipeline steps were not isolated.
- Job cleaning, formatting, and embedding code was scattered.

### ❌ 3. No Interfaces or Abstraction
- There was no way to substitute different models (e.g., another embedder).
- No standard behavior contract between components.

### ❌ 4. Hard to Test
- Because everything was glued together, mocking components for unit tests was impossible.

### ❌ 5. Violated Many SOLID Principles
- Functions had multiple responsibilities.
- High-level logic depended directly on low-level concrete classes.

The refactor resolved these issues by applying **four major SOLID principles**.

---

# 2. Refactoring Goals

The goals of the refactoring process were:

- Create a **clean separation** between GUI, business logic, and external services.
- Introduce **interfaces** to formalize responsibilities.
- Apply **dependency injection** to reduce coupling.
- Make the system **extensible** (e.g., alternative embedders, additional job APIs).
- Improve **maintainability**, **testability**, and **readability**.

---

# 3. SOLID Principles Applied

Below are the SOLID principles implemented in the refactoring, including **where** and **how** they appear in the project.

---

## 🟦 S — Single Responsibility Principle (SRP)

**Each module now has exactly ONE job.**

| Component | Single Responsibility |
|----------|------------------------|
| `AdzunaFetcher` | Fetch job postings from Adzuna API |
| `ResumeCleaner` | Clean and normalize resume text |
| `OpenAIEmbedder` | Generate embeddings using OpenAI |
| `Scrubber` | Remove invalid or empty job entries |
| `JobFormatter` | Convert nested API fields into readable strings |
| `similarity.py` | Compute cosine similarity only |
| `Pipeline` | Orchestrate the end-to-end workflow |
| `file_loader.py` | Load text from PDF/TXT resumes |
| `app.py` | GUI logic only |

SRP makes each file short, purpose-driven, and easy to test.

---

## 🟩 O — Open/Closed Principle (OCP)

**Modules are open for extension, but closed for modification.**

Examples:

### ✔ Adding a new embedder
You can drop in:

```python
class HuggingFaceEmbedder(IEmbedder):
    ...
```

and the pipeline continues to work without modification.

### ✔ Adding a new job source
Write:

```python
class IndeedFetcher(IFetcher):
    ...
```

and the pipeline can use it immediately.

### ✔ Adding new formatting logic
Create:

```python
class RemoteJobFormatter(IFormatter):
    ...
```

No existing code needs modification — only extension.

This demonstrates textbook OCP design.

---

## 🟧 L — Liskov Substitution Principle (LSP)

**Any class implementing an interface can be substituted for another.**

The project defines several interfaces:

- `IFetcher`
- `IEmbedder`
- `ICleaner`
- `IScrubber`
- `IFormatter`

The pipeline depends on these interfaces, not concrete classes:

```python
pipeline = Pipeline(fetcher, cleaner, embedder, scrubber, formatter, logger)
```

This means we can substitute:

- A mock embedder for unit testing  
- A different job fetcher  
- A different resume cleaner  

without changing the pipeline’s internal logic.

---

## 🟥 I — Interface Segregation Principle (ISP)

Instead of one “God interface” like `IJobSystem`, the project uses:

- `IFetcher`
- `ICleaner`
- `IEmbedder`
- `IScrubber`
- `IFormatter`

Each interface contains only what that module needs to do.

This prevents:

- Unused methods  
- Overloaded classes  
- Confusion of responsibilities  

Example:

```python
class IEmbedder:
    def embed_batch(self, texts):
        pass
```

It defines only one requirement — perfect ISP.

---

## 🟪 D — Dependency Inversion Principle (DIP)

This was the **most important improvement**.

Before refactoring:
- The GUI created fetchers, embedders, and scrapers directly.
- High-level logic was coupled to low-level code.

After refactoring:
- Dependencies are **passed into** the pipeline.
- The pipeline depends on **interfaces**, not classes.

Example:

```python
fetcher = AdzunaFetcher(...)
embedder = OpenAIEmbedder(...)
formatter = JobFormatter(...)

pipeline = Pipeline(fetcher, cleaner, embedder, scrubber, formatter, logger)
```

This design:

- Decouples pipeline from implementations  
- Allows mocking (unit tests)  
- Makes it easy to replace modules  
- Fits industrial dependency injection patterns  

---

# 4. Summary of Improvements

### ✔ Cleaner, more organized architecture  
### ✔ Separation between GUI, logic, I/O, and AI services  
### ✔ Full SOLID compliance  
### ✔ Easily extendable  
### ✔ Ready for unit testing  
### ✔ Easier debugging  
### ✔ Professional structure suitable for a portfolio piece  

---

# 5. Future Improvements (Optional)

- Add additional job APIs (Indeed, LinkedIn, GitHub Jobs)
- Swap in local embedding models
- Bundle with Docker
- Add full error-handling and retry logic
- Implement caching for repeated queries

---

# ✅ Final Verdict

The refactored version of the project is dramatically more:

- Maintainable  
- Testable  
- Professional  
- Extensible  

It demonstrates **strong software engineering principles** and exceeds the project requirements.
