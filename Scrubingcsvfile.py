import pandas as pd
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk

# Download NLTK resources (only need to run once)
nltk.download('stopwords')
nltk.download('wordnet')

# Load the original CSV
input_file = r"C:\Users\minif\OneDrive\Desktop\CS326_Project 1\adzuna_cs_jobs.csv"
df = pd.read_csv(input_file)

# Initialize lemmatizer and stopwords
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def clean_text(text):
    """Lowercase, remove punctuation, remove stopwords, and lemmatize"""
    if pd.isna(text):
        return ""
    # Lowercase
    text = text.lower()
    # Remove punctuation/special chars
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Tokenize, remove stopwords, lemmatize
    tokens = [lemmatizer.lemmatize(word) for word in text.split() if word not in stop_words]
    return " ".join(tokens)

# Combine FullDescription + Requirements for matching
df["job_text"] = df["FullDescription"].fillna("") + " " + df["Requirements"].fillna("")

# Clean the text for comparison
df["job_text_clean"] = df["job_text"].apply(clean_text)

# Optional: clean individual columns too
df["Title_clean"] = df["Title"].apply(clean_text)
df["Requirements_clean"] = df["Requirements"].apply(clean_text)

# Save the scrubbed CSV as a new file
output_file = "adzuna_cs_jobs_cleaned.csv"
df.to_csv(output_file, index=False)

print(f"✅ Scrubbed CSV saved as {output_file}")
