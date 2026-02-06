import json
import os
import re

INPUT_FILE = "/Users/dhruubb/Desktop/embedding-api/CUSTOMER PHISHING TP.txt"
OUTPUT_FILE = "app/chunks.json"

os.makedirs("data/chunks", exist_ok=True)

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    text = f.read()

# Split by page markers
pages = re.split(r"--- Page \d+ ---", text)

chunks = []
MAX_CHUNK_SIZE = 500  # Target chunk size

for page_num, page in enumerate(pages):
    page = page.strip()

    if len(page) < 50:
        continue
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', page)
    
    current_chunk = []
    current_length = 0
    sub_chunk_num = 1
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        
        sentence_length = len(sentence)
        
        # If adding this sentence exceeds max size
        if current_length + sentence_length > MAX_CHUNK_SIZE and current_chunk:
            chunks.append({
                "section": f"Page {page_num + 1} - Part {sub_chunk_num}",
                "content": ' '.join(current_chunk)
            })
            sub_chunk_num += 1
            current_chunk = [sentence]
            current_length = sentence_length
        else:
            current_chunk.append(sentence)
            current_length += sentence_length + 1
    
    # Add remaining sentences
    if current_chunk:
        chunks.append({
            "section": f"Page {page_num + 1} - Part {sub_chunk_num}",
            "content": ' '.join(current_chunk)
        })

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)

print(f"✅ Created {len(chunks)} chunks")
print(f"📊 Average chunk size: {sum(len(c['content']) for c in chunks) // len(chunks)} chars")
print(f"📦 Max chunk size: {max(len(c['content']) for c in chunks)} chars")
print(f"📦 Min chunk size: {min(len(c['content']) for c in chunks)} chars")
print(f"💾 Saved to {OUTPUT_FILE}")