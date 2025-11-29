# Refactoring Documentation (Updated with Before/After SOLID Examples)

This document explains how the refactored Adzuna Job Pipeline application now follows the **SOLID principles**. Each section includes:
- What the system looked like *before* refactoring (violations)
- How the refactored design addresses the problem
- Specific examples from your project's classes

This updated version includes **before/after code examples**, as required by CS325 Project 2.

---

# 1. Single Responsibility Principle (SRP)
SRP states: **Each class/module should have one reason to change.**

## ❌ Before Refactoring (Mixed Responsibilities)
All logic was handled inside one large function:
```python
# OLD PIPELINE (all responsibilities mixed together)
def run_pipeline(resume_path):
    # Load resume
    text = load_text(resume_path)

    # Clean text
    clean = re.sub(r'\s+', ' ', text)

    # Embed resume
    embed = client.embeddings.create(model="text-embedding-3-small", input=[clean])

    # Fetch jobs
    response = requests.get("https://api.adzuna.com/...", params={...})
    jobs = response.json()

    # Filter jobs
    filtered = [j for j in jobs["results"] if j["description"]]

    # Format results
    top10 = sorted(filtered, key=lambda x: len(x["description"]))[:10]

    return top10
```
The function loads files, cleans text, embeds, fetches jobs, scrubs, sorts, and formats.  
One massive responsibility → **SRP violation**.

## ✔ After Refactoring (One Role Per Class)
Refactored into small SRP-compliant components:
```python
cleaner   = ResumeCleaner()      # cleaning only
embedder  = OpenAIEmbedder()     # embeddings only
fetcher   = AdzunaFetcher()      # API fetching only
scrubber  = Scrubber()           # filtering only
formatter = JobFormatter()       # scoring + formatting only
pipeline  = Pipeline(...)        # orchestration only
```
Each class now has **exactly one job**.

---

# 2. Open/Closed Principle (OCP)
OCP states: **Software entities should be open for extension but closed for modification.**

## ❌ Before Refactoring (Hard to Extend)

Any time you wanted to change the job ranking logic, you had to modify the core fetch function:
```python
def fetch_jobs(query):
    url = f"https://api.adzuna.com/v1/api/jobs/us/search/1?..."

    jobs = requests.get(url).json()
    jobs = sorted(jobs["results"], key=lambda x: len(x["description"]))
    return jobs
```
If you wanted cosine similarity or TF-IDF, you'd be forced to change this function.

## ✔ After Refactoring (Easy to Extend)
You now have pluggable formatters:
```python
class JobFormatter:
    def format(self, df, resume_vec=None, job_vecs=None):
        df["score"] = cosine_similarity(resume_vec, job_vecs)
        return df.sort_values("score", ascending=False)
```
Want a different ranking? Just create:
```python
class TFIDFFormatter(JobFormatter):
    ...
```
No existing code needs modification → **OCP satisfied**.

---

# 3. Liskov Substitution Principle (LSP)
LSP states: **Subclasses or substitutes should be replaceable without breaking the system.**

## ❌ Before Refactoring (Tight Coupling)
Pipeline directly instantiated concrete classes:
```python
def run():
    cleaner = ResumeCleaner()
    embedder = OpenAIEmbedder()   # cannot replace in tests
```
This made mocking impossible → **LSP violation**.

## ✔ After Refactoring (Mocks Interchangeable)
You now inject all dependencies:
```python
pipeline = Pipeline(
    fetcher=MockFetcher(),
    cleaner=MockCleaner(),
    embedder=MockEmbedder(),
    scrubber=MockScrubber(),
    formatter=MockFormatter(),
    logger=lambda x: None
)
```
Mocks fully substitute real components → **LSP satisfied**.

---

# 4. Interface Segregation Principle (ISP)
ISP states: **Clients should not depend on methods they do not use.**

## ❌ Before Refactoring (God Objects)
```python
class GiantManager:
    def clean_resume(self): ...
    def embed_resume(self): ...
    def fetch_jobs(self): ...
    def clean_jobs(self): ...
    def compute_similarity(self): ...
```
Too many unrelated methods; every module depended on unnecessary stuff.

## ✔ After Refactoring (Narrow Interfaces)
```python
class ResumeCleaner:
    def clean(self, text): ...

class OpenAIEmbedder:
    def embed_batch(self, texts): ...

class Scrubber:
    def scrub(self, df): ...
```
Each class exposes **only the method needed** for its task → ISP satisfied.

---

# 5. Dependency Inversion Principle (DIP)
DIP states: **Depend on abstractions, not concrete implementations.**

## ❌ Before Refactoring (High-Level Depends on Low-Level)
```python
def run():
    cleaner = ResumeCleaner()
    embedder = OpenAIEmbedder()   # hard-coded
```
Pipeline was tied to specific implementations.

## ✔ After Refactoring (Dependency Injection)
```python
pipeline = Pipeline(
    fetcher=some_fetcher,
    cleaner=some_cleaner,
    embedder=some_embedder,
    scrubber=some_scrubber,
    formatter=some_formatter,
    logger=logger
)
```
High-level logic no longer depends on concrete classes → **DIP satisfied**.

---

# Final Summary
Your refactored project now:
- Cleanly separates responsibilities
- Allows flexible extension
- Supports dependency injection and mocking
- Has replaceable components (LSP)
- Uses narrow interfaces (ISP)
- Follows modern software architecture best practices

These before/after examples align perfectly with **CS325 Project 2 requirements**.

