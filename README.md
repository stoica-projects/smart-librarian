# Smart Librarian

Proiect RAG (Retrieval-Augmented Generation) cu ChromaDB si OpenAI.

## 1) Cerinte
- Python 3.10+ (testat pe 3.13 Windows)
- Cheie OpenAI: variabila de mediu `OPENAI_API_KEY`

## 2) Instalare
In radacina proiectului:
```bash
pip install -r requirements.txt
```

## 3) Configurare cheie
Seteaza `OPENAI_API_KEY=sk-...` in `.env`
  sau seteaza variabila in environment/Run Configuration.

## 4) Rulare rapida (CLI)
La prima rulare recomand reconstruirea indexului (creeaza folderul `./chroma_db` in proiect):
```bash
python main.py --reconstruieste --topn 3 --intrebare "Ce carti stii"
```
Apoi poti apela:
```bash
python main.py --intrebare "Vreau o carte despre libertate si control social."
python main.py --topn 3 --intrebare "Ce-mi recomanzi daca iubesc povestile fantastice?"
python main.py --intrebare "Ce este 1984?"
```

## 5) Export livrabile book_summaries (JSON/MD)
```bash
python make_deliverables.py
```
Rezultate in folderul `dist/`:
- `dist/book_summaries.json`
- `dist/book_summaries.md`

## 6) Ce contine proiectul
- **Fisier book_summaries cu 10+ carti**: `smart_librarian/dataset.py` (32 titluri, RO fara diacritice)
- **Initializare vector store**: `smart_librarian/chroma_setup.py` (Chroma + OpenAI embeddings)
- **Tool get_summary_by_title()**: `smart_librarian/tools.py`
- **Chat complet LLM + tool**: `smart_librarian/rag.py` (functiile `rag_chat` si `rag_chat_many`)
- **UI simplu (CLI)**: `main.py`
- **Persistenta Chroma**: in `./chroma_db` in interiorul proiectului

## 7) Dependinte si limbaje folosite
- **Limbaje**: Python
- **Dependinte Python** (vezi `requirements.txt`):
  - `openai>=1.50.0`
  - `chromadb>=1.0.12`
  - `python-dotenv>=1.0.1`
  - `numpy>=2.2.5`