import json
import os
from langchain_community.document_loaders import PyPDFLoader


def main() -> None:
    pdf_path = os.path.join("data", "manifesto.pdf")
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    pages: dict[int, str] = {}
    for d in docs:
        page_num = int(d.metadata.get("page", 0))
        if page_num not in pages:
            pages[page_num] = ""
        pages[page_num] += d.page_content

    # Keep only first 10 pages and truncate long content for quick review
    sample = {str(k): v[:6000] for k, v in sorted(pages.items())[:10]}

    out_dir = os.path.join("monitoring", "eval")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "pages_sample.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"pages": sample}, f, ensure_ascii=False, indent=2)

    print(f"Wrote sample to {out_path}")


if __name__ == "__main__":
    main()


