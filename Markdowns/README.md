# Adzuna Job Matching Pipeline (SOLID Architecture)

A desktop application built with **Tkinter**, **OpenAI embeddings**, and the **Adzuna Job Search API**.  
The tool lets you:

- Upload a resume (TXT or PDF)
- Enter job keywords (“what”) and location (“where”)
- Enter Adzuna API credentials
- Fetch live job postings
- Clean & embed your resume + job descriptions
- Compute cosine similarity scores
- Display the **Top 10 matching jobs** in a scrollable UI table
- Open job postings via clickable links

This project demonstrates a full, SOLID-compliant architecture with a clean GUI and modular pipeline.

---

## 🚀 Features

### **Resume Upload**
- Supports **PDF** (via `pdfplumber`)
- Supports **TXT**
- Automatically cleans and prepares the resume for AI processing

### **Job Search Inputs**
- “What” → job keywords (ex: *software engineer*)
- “Where” → location (ex: *St. Louis, MO*)

### **Combined Credentials Dialog**
Both Adzuna fields (App ID + App Key) appear in **one dialog box**.

### **AI Embeddings**
- Uses OpenAI’s `text-embedding-3-small`
- Converts text into numeric vectors
- Computes similarity with job descriptions

### **Cosine Similarity Ranking**
- Ranks all job postings by relevance
- Returns top 10 best-matching roles

### **Top 10 Popup Window**
- Scrollable table
- Clean layout: Title, Company, Location, Score, Link  
- **Open** button launches the job in your browser

---

## 🗂 Project Structure

```
Adzuna_SOLID/
│
├── gui/
│   ├── app.py
│   ├── theme.py
│   ├── results_popup.py
│
├── core/
│   ├── fetcher/
│   │   └── adzuna_fetcher.py
│   ├── cleaner/
│   │   └── resume_cleaner.py
│   ├── embedder/
│   │   └── openai_embedder.py
│   ├── scrubber/
│   │   └── scrubber.py
│   ├── formatter/
│   │   └── job_formatter.py
│   ├── pipeline/
│   │   └── pipeline.py
│   ├── utils/
│       ├── file_loader.py
│       └── similarity.py
│
├── main.py
└── README.md
```

---

## 🔧 Requirements

- Python 3.13+
- pdfplumber
- numpy
- pandas
- requests
- openai
- tkinter

---

## ▶ How to Run

```
conda activate Project_4_CS325
python main.py
```
