import os
import fitz  # PyMuPDF
import json

PDF_DIR = 'data/therapy_corpus/'
CHUNK_SIZE = 700  # Words per chunk

def chunk_text(text, chunk_size=CHUNK_SIZE):
    import re
    words = re.findall(r'\w+|\W+', text)
    chunks, current = [], ""
    for word in words:
        current += word
        if len(current.split()) >= chunk_size:
            chunks.append(current.strip())
            current = ""
    if current.strip():
        chunks.append(current.strip())
    return chunks

corpus = []
for fname in os.listdir(PDF_DIR):
    if fname.lower().endswith(".pdf"):
        doc = fitz.open(os.path.join(PDF_DIR, fname))
        pdf_text = "\n".join(page.get_text() for page in doc)
        pdf_chunks = chunk_text(pdf_text)
        for i, chunk in enumerate(pdf_chunks):
            corpus.append({
                "doc_id": fname,
                "chunk_id": f"{fname.replace('.pdf','')}_{i}",
                "text": chunk,
                "source_file": fname,
                "tags": [],     # Fill if desired
            })
        print(f"Extracted {len(pdf_chunks)} chunks from {fname}")

print(f"Total chunks extracted: {len(corpus)}")

with open("data/therapeutic_corpus.json", "w", encoding="utf8") as f:
    json.dump(corpus, f, ensure_ascii=False, indent=2)

print("✅ Extracted corpus saved to data/therapeutic_corpus.json")