import argparse
from smart_librarian.rag import rag_chat, rag_chat_many, ensure_built, build_or_refresh_collection

def main():
    parser = argparse.ArgumentParser(description="Bibliotecarul Inteligent - RAG (romana fara diacritice)")
    parser.add_argument("--intrebare", "--query", "-q", type=str, help="Intrebarea utilizatorului (ex: 'Vreau o carte despre...')")
    parser.add_argument("--topn", type=int, default=1, help="Numarul de recomandari dorite (implicit 1)")
    parser.add_argument("--reconstruieste", "--rebuild", action="store_true", help="Reconstruieste colectia Chroma de la zero")
    args = parser.parse_args()

    if args.reconstruieste:
        build_or_refresh_collection()
    else:
        ensure_built()

    intrebare = args.intrebare or input("Introdu intrebarea ta: ").strip()
    out = rag_chat_many(intrebare, n=args.topn) if args.topn and args.topn > 1 else rag_chat(intrebare)

    print("\n--- Recomandare/Recomandari ---\n")
    print(out.get("final", ""))

if __name__ == "__main__":
    main()
