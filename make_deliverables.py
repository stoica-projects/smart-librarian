from smart_librarian.dataset import book_summaries
import json, os

os.makedirs("dist", exist_ok=True)

with open("dist/book_summaries.json", "w", encoding="utf-8") as f:
    json.dump(book_summaries, f, ensure_ascii=False, indent=2)

with open("dist/book_summaries.md", "w", encoding="utf-8") as f:
    for b in book_summaries:
        f.write(f"## Titlu: {b['title']}\n{b['summary']}\n\n")

print("Am exportat dist/book_summaries.json si dist/book_summaries.md")
