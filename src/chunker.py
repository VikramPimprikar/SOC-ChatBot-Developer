import os
import re
import json

INPUT_DIR = "data/extracted_text"
OUTPUT_DIR = "data/chunks"


def clean_line(line: str) -> str:
    """Basic cleanup of lines."""
    return re.sub(r"\s+", " ", line.strip())


def is_page_marker(line: str) -> bool:
    """Detect markers like --- Page 1 ---."""
    return bool(re.match(r"^---\s*Page\s*\d+\s*---$", line.strip(), flags=re.IGNORECASE))


def is_section_heading(line: str) -> bool:
    """
    Detect headings like:
    1. Incident Overview
    2. Phase 1: Preparation & Detection
    3. Phase 2: Analysis & Investigation
    7. Escalation Criteria
    """
    line = clean_line(line)

    patterns = [
        r"^\d+\.\s*Incident Overview$",
        r"^\d+\.\s*Phase\s+\d+\s*:\s*.+$",
        r"^\d+\.\s*Escalation Criteria$",
        r"^\d+\.\s*Objectives$",
        r"^\d+\.\s*References$",
    ]

    return any(re.match(p, line, flags=re.IGNORECASE) for p in patterns)


def split_into_chunks(text: str):
    """
    Split extracted playbook text into section-based chunks.
    Each numbered section becomes its own chunk.
    """
    lines = text.splitlines()

    chunks = []
    current_section = "General"
    current_content = []

    for raw_line in lines:
        if not raw_line.strip():
            continue

        if is_page_marker(raw_line):
            continue

        line = clean_line(raw_line)

        # If this is a section heading, start a new chunk
        if is_section_heading(line):
            if current_content:
                chunks.append({
                    "section": current_section,
                    "content": "\n".join(current_content).strip()
                })

            current_section = line
            current_content = []
        else:
            current_content.append(raw_line)

    # Save final chunk
    if current_content:
        chunks.append({
            "section": current_section,
            "content": "\n".join(current_content).strip()
        })

    # Remove very small chunks (noise)
    clean_chunks = []
    for ch in chunks:
        if len(ch["content"]) >= 150:
            clean_chunks.append(ch)

    return clean_chunks


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not os.path.exists(INPUT_DIR):
        print(f"Input folder not found: {INPUT_DIR}")
        return

    txt_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".txt")]

    if not txt_files:
        print("No extracted text files found.")
        return

    print(f"Found {len(txt_files)} extracted text file(s)\n")

    for file in txt_files:
        playbook_name = file.replace(".txt", "")
        file_path = os.path.join(INPUT_DIR, file)

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()

        chunks = split_into_chunks(text)

        out_path = os.path.join(OUTPUT_DIR, f"{playbook_name}_chunks.json")

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

        print(f"{playbook_name}: created {len(chunks)} chunks")
        print(f"Saved: {out_path}\n")

    print("Chunking completed successfully.")


if __name__ == "__main__":
    main()
