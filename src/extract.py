import os
import pdfplumber


PLAYBOOKS_DIR = "playbooks"
OUTPUT_DIR = "data/extracted_text"


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts all text from a PDF using pdfplumber."""
    full_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                full_text.append(f"\n--- Page {i} ---\n{text}")

    return "\n".join(full_text)


def main():
    # Create output folder if missing
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Check PDFs
    if not os.path.exists(PLAYBOOKS_DIR):
        print(f" Folder not found: {PLAYBOOKS_DIR}")
        print("Create the folder and add PDFs inside it.")
        return

    pdf_files = [f for f in os.listdir(PLAYBOOKS_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(" No PDF playbooks found.")
        print(f"Add at least one PDF inside: {PLAYBOOKS_DIR}/")
        return

    print(f" Found {len(pdf_files)} playbook(s) in '{PLAYBOOKS_DIR}/'\n")

    for pdf in pdf_files:
        pdf_path = os.path.join(PLAYBOOKS_DIR, pdf)
        print(f" Extracting: {pdf}")

        try:
            extracted_text = extract_text_from_pdf(pdf_path)

            # Save extracted text as .txt
            txt_filename = pdf.replace(".pdf", ".txt")
            out_path = os.path.join(OUTPUT_DIR, txt_filename)

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(extracted_text)

            print(f" Saved: {out_path}")
            print(f" Characters extracted: {len(extracted_text)}\n")

        except Exception as e:
            print(f" Failed for {pdf}: {e}\n")

    print("Extraction completed.")


if __name__ == "__main__":
    main()
