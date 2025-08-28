import json
from typing import Dict, Any, List

from smart_librarian.config import CHAT_MODEL
from smart_librarian.dataset import book_summaries
from smart_librarian.chroma_setup import get_collection, recreate_collection
from smart_librarian.tools import get_summary_by_title

from openai import OpenAI
client = OpenAI()

BAD_WORDS = {
    "injurii": ["idiot", "moron", "retard", "stupid"],
    "explicit": ["nsfw_word_1", "nsfw_word_2"],
}

def contine_limbaj_nepotrivit(text: str) -> bool:
    t = (text or "").lower()
    for _, words in BAD_WORDS.items():
        for w in words:
            if w and w in t:
                return True
    return False

def construieste_sau_reimprospateaza() -> int:
    collection = recreate_collection("book_summaries")
    ids, documents, metadatas = [], [], []
    for i, b in enumerate(book_summaries):
        ids.append(str(i))
        doc = (
            f"Title: {b['title']}\n"
            f"Summary: {b['summary']}\n"
            f"Themes: {', '.join(b['themes'])}\n"
            f"Genre: {b['genre']}"
        )
        documents.append(doc)
        metadatas.append({
            "title": b["title"],
            "genre": b["genre"],
            "themes": ", ".join(b["themes"]),
        })
    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    try:
        return collection.count()
    except Exception:
        return len(ids)

def numar_documente() -> int:
    try:
        c = get_collection("book_summaries")
        return c.count()
    except Exception:
        return 0

def ensure_built(forta: bool = False) -> None:
    if forta or numar_documente() == 0:
        cnt = construieste_sau_reimprospateaza()
        if cnt == 0:
            raise RuntimeError("Nu am reusit sa construiesc colectia Chroma. Verifica OPENAI_API_KEY si reteaua.")

def retrieve(query: str, k: int = 5) -> Dict[str, Any]:
    collection = get_collection("book_summaries")
    result = collection.query(query_texts=[query], n_results=k)
    return result

def _system_prompt() -> str:
    return (
        "Esti Bibliotecarul Inteligent. Primesti cererea utilizatorului si o lista de carti candidate "
        "recuperate dintr-un vector store. ROL: \n"
        "  1) Alege UN SINGUR titlu care se potriveste cel mai bine.\n"
        "  2) Explica PE SCURT de ce (2-4 fraze).\n"
        "IMPORTANT: Dupa ce alegi titlul, TREBUIE sa apelezi o singura data tool-ul get_summary_by_title, "
        "transmitand exact titlul ales. Nu insera tu rezumatul complet.\n"
        "La MESAJUL FINAL: raspunde EXCLUSIV in limba romana FARA DIACRITICE. "
        "Daca rezumatul returnat de tool nu este in romana, trad-l fidel in romana fara diacritice. "
        "Include doua sectiuni: \n"
        "  - Recomandare: titlul ales si motivarea scurta.\n"
        "  - Rezumat complet: continutul tool-ului (tradus daca e cazul, fara diacritice)."
    )

def rag_chat(intrebare: str, k: int = 5, temperatura: float = 0.2) -> Dict[str, Any]:
    if contine_limbaj_nepotrivit(intrebare):
        politicos = "Nu pot procesa cererea din cauza limbajului nepotrivit. Te rog reformuleaza si reincearca."
        return {"final": politicos, "retrieval": None, "messages": []}

    try:
        ensure_built()
    except Exception as e:
        return {"final": f"Eroare la construirea indexului: {e}", "retrieval": None, "messages": []}

    retrieved = retrieve(intrebare, k=k)
    docs = (retrieved.get("documents") or [[]])[0]
    metas = (retrieved.get("metadatas") or [[]])[0]

    context_items: List[Dict[str, Any]] = []
    if not docs or not metas:
        for b in book_summaries[:k]:
            context_items.append({
                "title": b["title"],
                "genre": b["genre"],
                "themes": ", ".join(b["themes"]),
                "snippet": b["summary"].split(". ")[0]
            })
    else:
        for doc, meta in zip(docs, metas):
            context_items.append({
                "title": meta.get("title"),
                "genre": meta.get("genre"),
                "themes": meta.get("themes"),
                "snippet": "\n".join(doc.split("\n")[:2])
            })

    sistem = _system_prompt()
    user_msg = {
        "role": "user",
        "content": (
            "Cerere utilizator: " + intrebare + "\n\n"
            "Carti candidate (JSON):\n" + json.dumps(context_items, ensure_ascii=False)
        ),
    }

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_summary_by_title",
                "description": "Returneaza rezumatul local complet pentru un titlu exact.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "Titlul exact selectat pentru recomandare"}
                    },
                    "required": ["title"],
                    "additionalProperties": False
                }
            }
        }
    ]

    primul = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=temperatura,
        messages=[{"role": "system", "content": sistem}, user_msg],
        tools=tools,
        tool_choice="auto",
    )

    messages = [{"role": "system", "content": sistem}, user_msg]
    rasp = primul.choices[0].message
    messages.append({"role": "assistant", "content": rasp.content or "", "tool_calls": rasp.tool_calls})

    tool_calls = rasp.tool_calls or []
    if not tool_calls:
        nudj = {"role": "user", "content": "Te rog apeleaza get_summary_by_title cu titlul ales."}
        al2 = client.chat.completions.create(
            model=CHAT_MODEL,
            temperature=temperatura,
            messages=messages + [nudj],
            tools=tools,
            tool_choice="auto",
        )
        rasp = al2.choices[0].message
        messages.append({"role": "assistant", "content": rasp.content or "", "tool_calls": rasp.tool_calls})
        tool_calls = rasp.tool_calls or []

    for call in tool_calls:
        if getattr(call, "type", "") == "function" and call.function.name == "get_summary_by_title":
            try:
                args = json.loads(call.function.arguments or "{}")
            except Exception:
                args = {}
            titlu = args.get("title", "")
            tool_result = get_summary_by_title(titlu)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "name": "get_summary_by_title",
                "content": tool_result
            })

    final_resp = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=temperatura,
        messages=messages
    )
    final_text = final_resp.choices[0].message.content
    return {"final": final_text, "retrieval": context_items, "messages": messages}

def rag_chat_many(intrebare: str, n: int = 3, temperatura: float = 0.2) -> Dict[str, Any]:
    if contine_limbaj_nepotrivit(intrebare):
        politicos = "Nu pot procesa cererea din cauza limbajului nepotrivit. Te rog reformuleaza."
        return {"final": politicos, "retrieval": None, "messages": []}

    try:
        ensure_built()
    except Exception as e:
        return {"final": f"Eroare la construirea indexului: {e}", "retrieval": None, "messages": []}

    k = max(n * 3, n)
    retrieved = retrieve(intrebare, k=k)
    metas = (retrieved.get("metadatas") or [[]])[0]

    if not metas:
        metas = [{"title": b["title"], "genre": b["genre"], "themes": ", ".join(b["themes"])} for b in book_summaries]

    vazute = set()
    alese = []
    for m in metas:
        t = (m.get("title") or "").strip()
        if t and t not in vazute:
            vazute.add(t)
            alese.append(m)
        if len(alese) >= n:
            break

    linii = []
    linii.append(f"Iti recomand {len(alese)} titluri:")
    for i, m in enumerate(alese, 1):
        titlu = m.get("title", "Necunoscut")
        gen = m.get("genre", "n/a")
        teme = m.get("themes", "")
        motiv = f"{gen} · teme: {teme}" if teme else gen
        linii.append(f"{i}. {titlu} — {motiv}")

    linii.append("")
    linii.append("Rezumat(e) complete:")
    for i, m in enumerate(alese, 1):
        titlu = m.get("title", "Necunoscut")
        rez = get_summary_by_title(titlu)
        linii.append(f"{i}) {titlu}: {rez}")

    final_text = "\n".join(linii)
    return {"final": final_text, "retrieval": alese, "messages": []}

build_or_refresh_collection = construieste_sau_reimprospateaza
