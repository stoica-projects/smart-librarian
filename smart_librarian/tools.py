from smart_librarian.dataset import book_summaries_dict
import difflib

def get_summary_by_title(title: str) -> str:
    if title in book_summaries_dict:
        return book_summaries_dict[title]
    candidates = difflib.get_close_matches(title, list(book_summaries_dict.keys()), n=1, cutoff=0.7)
    if candidates:
        return f"(Titlul cel mai apropiat: {candidates[0]})\n" + book_summaries_dict[candidates[0]]
    return "Rezumat indisponibil pentru titlul solicitat."
