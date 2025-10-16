# Adzuna Toolbox 

## Overview

**Adzuna Toolbox** is a complete end-to-end job and resume analysis suite built with Python and Tkinter.
It connects to the [Adzuna Jobs API](https://developer.adzuna.com/), retrieves job listings, cleans and embeds job text, processes a user’s resume, and ranks the most relevant job matches using OpenAI embeddings.

---

## Features

The program is divided into **five stages**, all accessible from a single GUI window:

| Stage                       | Description                                                                                               |
| --------------------------- | --------------------------------------------------------------------------------------------------------- |
| **0. Fetch Adzuna Jobs**    | Connects to the Adzuna API, verifies credentials, and downloads job listings (with pagination).           |
| **1. Clean Adzuna CSV**     | Cleans and lemmatizes job descriptions using NLTK stopwords and regex filters.                            |
| **2. Extract Resume → CSV** | Parses `.pdf` or `.txt` resumes, extracts text, and saves it for analysis.                                |
| **3. Embed Jobs + Resume**  | Uses **OpenAI embeddings** to vectorize job and resume text for comparison. *(Requires `OPENAI_API_KEY`)* |
| **4. Rank Jobs vs Resume**  | Calculates cosine similarity between embeddings and outputs a ranked Top-10 CSV with a GUI viewer.        |

---

## Environment Setup

Before running the toolbox, it’s recommended to create a dedicated virtual environment using a **requirements.yaml** file. This ensures that all necessary libraries are installed in an isolated environment without affecting your global Python setup.

### 1. Create the Environment

```bash
conda env create -f requirements.yaml
```

### 2. Activate the Environment

```bash
conda activate adzuna_toolbox_env
```

### 3. Requirements.yaml Example

```yaml
name: adzuna_toolbox_env
dependencies:
  - python=3.10
  - pip
  - pip:
      - requests
      - pandas
      - numpy
      - nltk
      - openai
      - pdfplumber
```

### 4. What’s Installed

* **requests** → for Adzuna API requests
* **pandas** → for CSV reading/writing and data manipulation
* **numpy** → for numerical computations and cosine similarity
* **nltk** → for text cleaning, stopwords, and lemmatization
* **openai** → for generating text embeddings used in ranking
* **pdfplumber** → for reading text from PDF resumes

After setup, you can run the toolbox within this environment to ensure full compatibility with all dependencies.

---

## Environment Variable

The following variable **must be set** before running stages 3 and 4:

| Variable         | Description                               |
| ---------------- | ----------------------------------------- |
| `OPENAI_API_KEY` | Required for embedding and ranking steps. |

Examples:

```bash
# Windows
setx OPENAI_API_KEY "your_api_key_here"

# macOS / Linux
export OPENAI_API_KEY="your_api_key_here"
```

---

## Output Files

| Stage | Output File                                                    | Description                     |
| ----- | -------------------------------------------------------------- | ------------------------------- |
| 0     | `adzuna_jobs_YYYY-MM-DD.csv`                                   | Raw jobs from Adzuna            |
| 1     | `*_cleaned.csv`                                                | Cleaned and lemmatized job text |
| 2     | `resume_single.csv`                                            | Resume text and contact info    |
| 3     | `jobs_embeddings.npy`, `resume_embedding.npy`, `jobs_meta.csv` | Vectorized job and resume data  |
| 4     | `top10_ranked_jobs.csv`                                        | Final ranked Top-10 matches     |

---

## Interface Preview

When launched, the GUI displays:

* A **left panel** with stage buttons (`Fetch`, `Clean`, `Resume`, `Embed`, `Rank`)
* A **right panel** with a real-time log window showing progress and results

When the ranking stage completes, a pop-up window lists the **Top 10 job matches**, allowing you to open job URLs directly in your browser.

---

## Notes

* Stages must be run **in order (0 → 4)**.
* Embedding stages require a valid OpenAI API key and internet access.
* The program will generate logs in the right panel for every API call, file write, or operation performed.

---

## License

This project is distributed for educational and research purposes.
All Adzuna API usage must comply with [Adzuna’s developer terms](https://developer.adzuna.com/terms).

---
