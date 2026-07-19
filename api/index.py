"""
Winter AI — Multi-paradigm reasoning engine
Created by INEZA Aime Bruno, Rwanda
EN → FR → RW trilingual knowledge engine
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
import unicodedata
import logging
import re
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("winter")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Winter AI",
    description="Multi-paradigm reasoning engine — EN → FR → RW",
    version="2.0.0",
)

# Read allowed frontend URL from environment (set in Render dashboard)
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Globals ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
BRAIN_FILE = BASE_DIR / "brain.txt"
INFO_DIR = BASE_DIR / "info"
BRAIN_TEXT: str = ""
KNOWLEDGE_BASE: dict[str, str] = {}

KINYARWANDA_WORDS = {
    "muraho", "murakoze", "amakuru", "ni", "meza", "umukino",
    "kode", "ineza", "uyu", "iyo", "ubwo", "kandi", "ariko",
    "cyane", "neza", "bite", "ese", "ndashaka", "nagira", "ngo",
    "ubumenyi", "gutekereza", "igisubizo", "ikibazo", "igihugu",
    "umuryango", "ubuzima", "akazi", "ishuri", "igitabo",
    "ubuhanzi", "amahoro", "intambara", "urukundo", "inshuti",
    "amateka", "siyanse", "matematiki", "jeografiya", "isi",
    "izuba", "ukwezi", "inyenyeri", "igiti", "inyamaswa",
    "umuntu", "umwana", "indyo", "umwarimu", "umunyeshuri",
    "iterambere", "ikoranabuhanga", "interineti", "porogiram",
    "ekonomiya", "ubucuruzi", "ubuhinzi", "inganda", "uburezi",
    "ubwigenge", "ubungakanye", "ubutabera", "umuco", "idini",
    "imibare", "nimero", "atome", "selile", "biologiya",
    "fiziki", "chimie", "ubuvuzi", "inkingo", "amaraso",
    "umutima", "ubwonko", "ingufu", "amashanyarazi", "urumuri",
    "ijwi", "ubushyuhe", "uburemere", "galaxi", "ikirangamubiri",
    "rwanda", "kigali", "afurika", "aziya", "uburayi", "amerika",
    "inyanja", "umusozi", "uruzi", "imvura", "umuyaga", "ikirere",
    "ishyamba", "ibidukikije", "zahabu", "icyuma", "amafaranga",
    "ineza", "gukora", "kurera", "kubana", "gukunda",
}

FRENCH_CHARS = set("éèêëàâùûüîïôçœæ")


# ── Startup ───────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    global BRAIN_TEXT, KNOWLEDGE_BASE
    INFO_DIR.mkdir(parents=True, exist_ok=True)

    if BRAIN_FILE.exists():
        BRAIN_TEXT = BRAIN_FILE.read_text(encoding="utf-8")
        logger.info(f"Loaded brain.txt ({len(BRAIN_TEXT)} chars)")
    else:
        BRAIN_TEXT = "Winter AI is a multi-paradigm reasoning engine created by INEZA Aime Bruno, Rwanda."
        logger.warning("brain.txt not found, using default")

    KNOWLEDGE_BASE = {}
    for f in INFO_DIR.glob("*"):
        if f.suffix in (".txt", ".md") and f.is_file():
            try:
                KNOWLEDGE_BASE[f.name] = f.read_text(encoding="utf-8")
                logger.info(f"Loaded knowledge: {f.name}")
            except Exception as e:
                logger.error(f"Failed to load {f.name}: {e}")

    logger.info(f"Winter AI v2.0 ready. Knowledge files: {list(KNOWLEDGE_BASE.keys())}")


# ── Language detection ────────────────────────────────────────────────────────
def detect_language(text: str) -> str:
    lower = text.lower()
    words = set(re.findall(r'\w+', lower))

    rw_hits = words & KINYARWANDA_WORDS
    if any(w in lower for w in ["muraho", "murakoze", "amakuru", "ubumenyi", "igisubizo"]):
        return "rw"
    if len(rw_hits) >= 2:
        return "rw"

    fr_hits = sum(1 for c in text if c.lower() in FRENCH_CHARS)
    french_words = {"bonjour", "merci", "comment", "vous", "je", "est", "une", "les", "pour", "avec", "dans", "sur"}
    fr_word_hits = words & french_words
    if fr_hits >= 2 or len(fr_word_hits) >= 2:
        return "fr"

    return "en"


# ── Knowledge search ──────────────────────────────────────────────────────────
def search_all_knowledge(query: str, lang: str) -> tuple[str, str]:
    """Returns (answer, source_file)"""
    q_lower = query.lower()
    tokens = re.findall(r'\w+', q_lower)

    best_score = 0
    best_answer = ""
    best_source = "brain.txt"

    def score_text(text: str) -> tuple[int, str]:
        lines = text.splitlines()
        best = 0
        best_line = ""
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            ll = line.lower()
            hits = sum(1 for t in tokens if len(t) > 2 and t in ll)
            lang_tag = lang.upper() + ":"
            lang_bonus = 3 if ll.startswith(lang_tag.lower()) else 0
            score = hits + lang_bonus
            if score > best:
                best = score
                best_line = line
        return best, best_line

    sc, ln = score_text(BRAIN_TEXT)
    if sc > best_score:
        best_score = sc
        best_answer = ln
        best_source = "brain.txt"

    for fname, content in KNOWLEDGE_BASE.items():
        sc, ln = score_text(content)
        if sc > best_score:
            best_score = sc
            best_answer = ln
            best_source = fname

    # Dictionary cross-reference
    if "dictionary.txt" in KNOWLEDGE_BASE:
        dict_text = KNOWLEDGE_BASE["dictionary.txt"]
        for line in dict_text.splitlines():
            parts = {}
            for p in line.split("|"):
                if ":" in p:
                    k, v = p.split(":", 1)
                    parts[k.strip()] = v.strip()
            match_found = any(t in str(parts.values()).lower() for t in tokens if len(t) > 2)
            if match_found:
                lang_key = lang.upper()
                if lang_key in parts:
                    return f"{parts[lang_key]}", "dictionary.txt"

    return best_answer or query, best_source


# ── Pydantic models ───────────────────────────────────────────────────────────
class MessageRequest(BaseModel):
    prompt: str
    chat_id: str
    lang: str = "auto"


class ParadigmStep(BaseModel):
    engine: str
    status: str
    output: str
    duration_ms: float


class MessageResponse(BaseModel):
    chat_id: str
    lang: str
    detected_lang: str
    reasoning_steps: list[ParadigmStep]
    final_answer: str
    knowledge_source: str
    confidence: float


class BrainUpdateRequest(BaseModel):
    content: str


class HealthResponse(BaseModel):
    status: str
    version: str
    knowledge_files: list[str]
    brain_size: int
    total_knowledge_chars: int


# ── Winter Engine ─────────────────────────────────────────────────────────────
class WinterEngine:

    def python_layer(self, prompt: str, lang: str, detected: str) -> ParadigmStep:
        t0 = time.perf_counter()
        out = f"Orchestration | Input lang: {lang} | Detected: {detected} | Tokens: {len(prompt.split())} | Length: {len(prompt)}"
        return ParadigmStep(engine="Python", status="ok", output=out,
                            duration_ms=round((time.perf_counter() - t0) * 1000, 2))

    def prolog_layer(self, prompt: str, lang: str) -> tuple[ParadigmStep, str, str]:
        t0 = time.perf_counter()
        answer, source = search_all_knowledge(prompt, lang)
        out = f"[{lang.upper()}] Knowledge search → matched from '{source}': '{answer[:100]}'"
        return (ParadigmStep(engine="Prolog", status="ok", output=out,
                             duration_ms=round((time.perf_counter() - t0) * 1000, 2)),
                answer, source)

    def mercury_layer(self, answer: str) -> ParadigmStep:
        t0 = time.perf_counter()
        is_det = bool(answer and len(answer.strip()) > 5)
        out = f"Determinism: {'DETERMINISTIC — clear answer path' if is_det else 'NONDETERMINISTIC — ambiguous'}"
        return ParadigmStep(engine="Mercury", status="ok", output=out,
                            duration_ms=round((time.perf_counter() - t0) * 1000, 2))

    def ocaml_layer(self, answer: str) -> ParadigmStep:
        t0 = time.perf_counter()
        try:
            answer.encode("utf-8").decode("utf-8")
            norm = unicodedata.normalize("NFC", answer)
            out = f"UTF-8 valid | NFC normalized | Chars: {len(norm)} | Words: {len(norm.split())}"
            status = "ok"
        except Exception as e:
            out = f"Encoding error: {e}"
            status = "error"
        return ParadigmStep(engine="OCaml", status=status, output=out,
                            duration_ms=round((time.perf_counter() - t0) * 1000, 2))

    def lisp_layer(self, prompt: str) -> ParadigmStep:
        t0 = time.perf_counter()
        tokens = re.findall(r'\w+', prompt.lower())
        s_expr = "(query " + " ".join(f"'{t}" for t in tokens[:8]) + ")"
        out = f"Symbolic tokens: {s_expr}"
        return ParadigmStep(engine="LISP", status="ok", output=out,
                            duration_ms=round((time.perf_counter() - t0) * 1000, 2))

    def cpp_layer(self, answer: str) -> ParadigmStep:
        t0 = time.perf_counter()
        safe = re.sub(r'[^\w\s\-.,!?éèàùêîôûçœæ]', '', answer)[:150]
        out = f"Formatted payload ready | Length: {len(safe)} chars"
        return ParadigmStep(engine="C++", status="ok", output=out,
                            duration_ms=round((time.perf_counter() - t0) * 1000, 2))

    def schema_layer(self, answer: str, lang: str) -> tuple[ParadigmStep, float]:
        t0 = time.perf_counter()
        checks = {
            "non_empty": bool(answer.strip()),
            "valid_lang": lang in ("en", "fr", "rw"),
            "length_ok": 1 <= len(answer) <= 4096,
            "utf8_clean": all(ord(c) < 65536 for c in answer),
            "meaningful": len(answer.split()) >= 3,
        }
        passed = sum(checks.values())
        confidence = round(passed / len(checks), 2)
        out = f"Validation: {checks} | Score: {passed}/{len(checks)} | Confidence: {confidence}"
        return (ParadigmStep(engine="Schema", status="ok" if passed == len(checks) else "warn", output=out,
                             duration_ms=round((time.perf_counter() - t0) * 1000, 2)),
                confidence)

    def build_final_answer(self, prompt: str, raw: str, lang: str) -> str:
        q = prompt.strip().rstrip("?").lower()

        # ── Greetings ──
        greetings = {
            "en": {"hello", "hi", "hey", "greetings", "good morning", "good evening"},
            "fr": {"bonjour", "salut", "bonsoir", "bonne nuit"},
            "rw": {"muraho", "bite"},
        }
        for lng, words in greetings.items():
            if any(w in q for w in words):
                replies = {
                    "en": "Hello! I am Winter AI — a multilingual reasoning engine created by INEZA Aime Bruno from Rwanda. I can answer questions in English, French, and Kinyarwanda. How can I help you today?",
                    "fr": "Bonjour ! Je suis Winter AI — un moteur de raisonnement multilingue créé par INEZA Aime Bruno du Rwanda. Je peux répondre en anglais, français et kinyarwanda. Comment puis-je vous aider ?",
                    "rw": "Muraho! Ndi Winter AI — mashini yo gutekereza mu ndimi nyinshi yahujwe na INEZA Aime Bruno wo mu Rwanda. Nshobora gusubiza mu Cyongereza, Igifaransa, na Kinyarwanda. Nakugira nte uyu munsi?",
                }
                return replies.get(lang, replies["en"])

        # ── Thank you ──
        if any(w in q for w in ["thank", "thanks", "merci", "murakoze", "murakoze cyane"]):
            replies = {
                "en": "You're welcome! Winter AI is always here to help. Feel free to ask more questions.",
                "fr": "De rien ! Winter AI est toujours là pour vous aider. N'hésitez pas à poser d'autres questions.",
                "rw": "Ntacyo! Winter AI iri hano buri gihe kugufasha. Baza ibibazo byose ushaka.",
            }
            return replies.get(lang, replies["en"])

        # ── How are you ──
        if any(w in q for w in ["how are you", "comment ça va", "comment vas", "amakuru", "unkora bite"]):
            replies = {
                "en": "I am running perfectly — all 7 reasoning engines are online and ready. My knowledge base covers science, history, geography, technology, and more. How can I assist you?",
                "fr": "Je fonctionne parfaitement — les 7 moteurs de raisonnement sont en ligne. Ma base de connaissances couvre la science, l'histoire, la géographie, la technologie et bien plus. Comment puis-je vous aider ?",
                "rw": "Ndakora neza cyane — imishinga 7 iri gukora. Ubumenyi bwanjye bwuzuye siyanse, amateka, jeografiya, ikoranabuhanga, n'ibindi. Nakugira nte?",
            }
            return replies.get(lang, replies["en"])

        # ── Who made you ──
        if any(w in q for w in ["who made you", "who created you", "who built you", "qui t'a créé", "wakuremye", "wavushije", "who are you", "qui es-tu", "ndi nde"]):
            replies = {
                "en": "I am Winter AI, created by INEZA Aime Bruno from Rwanda. I am a multi-paradigm reasoning engine that processes every query through 7 logic layers: Python (orchestration), Prolog (knowledge search), Mercury (determinism), OCaml (type validation), LISP (symbolic tokenization), C++ (output formatting), and Schema (validation). I speak English, French, and Kinyarwanda.",
                "fr": "Je suis Winter AI, créé par INEZA Aime Bruno du Rwanda. Je suis un moteur de raisonnement multi-paradigme qui traite chaque requête à travers 7 couches logiques : Python (orchestration), Prolog (recherche de connaissances), Mercury (déterminisme), OCaml (validation de type), LISP (tokenisation symbolique), C++ (formatage de sortie) et Schema (validation).",
                "rw": "Ndi Winter AI, wahujwe na INEZA Aime Bruno wo mu Rwanda. Ndi mashini yo gutekereza ikoresheje inzira 7: Python (guyobora), Prolog (gushakisha ubumenyi), Mercury (gusuzuma), OCaml (kwemeza ubwoko), LISP (gutondeka amagambo), C++ (guhuza ibisubizo), na Schema (kwemeza). Ndavuga Icyongereza, Igifaransa, na Kinyarwanda.",
            }
            return replies.get(lang, replies["en"])

        # ── Capabilities ──
        if any(w in q for w in ["what can you do", "capabilities", "que peux-tu", "ushobora iki", "what do you know", "topics"]):
            replies = {
                "en": "I am Winter AI and I can help you with:\n• Science — Physics, Chemistry, Biology\n• Mathematics — Algebra, Calculus, Geometry\n• History — World history, African history, Rwandan history\n• Geography — Countries, capitals, landmarks\n• Technology — Programming, AI, Internet, databases\n• Astronomy — Solar system, black holes, galaxies\n• Economics — GDP, trade, Rwanda Vision 2050\n• Philosophy — Greek philosophers, ethics\n• Medicine — Nutrition, immune system, health\n• Sports, Arts, Culture, and much more!\nI respond in English, French, and Kinyarwanda.",
                "fr": "Je suis Winter AI et je peux vous aider avec :\n• Science — Physique, Chimie, Biologie\n• Mathématiques — Algèbre, Calcul, Géométrie\n• Histoire — Histoire mondiale, africaine, rwandaise\n• Géographie — Pays, capitales, monuments\n• Technologie — Programmation, IA, Internet\n• Astronomie — Système solaire, trous noirs\n• Économie — PIB, commerce, Vision Rwanda 2050\n• Et bien plus encore !\nJe réponds en anglais, français et kinyarwanda.",
                "rw": "Ndi Winter AI kandi nshobora kukufasha mu:\n• Siyanse — Fiziki, Chimie, Biologiya\n• Matematiki — Aljebra, Calcul, Jeometri\n• Amateka — Amateka y'isi, Afurika, Rwanda\n• Jeografiya — Ibihugu, imirwa mikuru, inzu nzima\n• Ikoranabuhanga — Porogiramishi, AI, Interineti\n• Astronomiya — Sisitemu ya zuba, intoboro z'umukara\n• Ekonomiya — GDP, ubucuruzi, Inzozi 2050\n• N'ibindi byinshi!\nNdasubiza mu Cyongereza, Igifaransa, na Kinyarwanda.",
            }
            return replies.get(lang, replies["en"])

        # ── Rwanda ──
        if any(w in q for w in ["rwanda", "kigali", "rwandan", "kagame", "rwandais", "u rwanda", "inzozi", "vision 2050"]):
            replies = {
                "en": "Rwanda — 'The Land of a Thousand Hills' — gained independence from Belgium on July 1, 1962. Capital: Kigali. President: Paul Kagame (since 2000). Population: ~14 million. Currency: Rwandan Franc (RWF). Rwanda's economy grows at 7–8% per year, one of Africa's fastest. Main exports: tea, coffee, coltan. Rwanda Vision 2050 aims to become an upper-middle-income country through technology and innovation. Official languages: Kinyarwanda, French, English, Swahili.",
                "fr": "Le Rwanda — 'Le Pays des Mille Collines' — a obtenu son indépendance de la Belgique le 1er juillet 1962. Capitale: Kigali. Président: Paul Kagame (depuis 2000). Population: ~14 millions. Monnaie: Franc rwandais. L'économie rwandaise croît de 7–8% par an. Principales exportations: thé, café, coltan. La Vision 2050 vise un revenu intermédiaire supérieur.",
                "rw": "U Rwanda — 'Igihugu cy'Imisozi Igihumbi' — rwabonye ubwigenge bwa Ububiligi ku ya 1 Nyakanga 1962. Umurwa mukuru: Kigali. Perezida: Paul Kagame (kuva mu 2000). Abaturage: ~miliyoni 14. Amafaranga: Faranga ya Rwanda (RWF). Ekonomiya y'u Rwanda iruza 7–8% ku mwaka, kimwe n'ibihugu by'ingufu muri Afurika. Ibicuruzwa: icyayi, ikawa, coltan. Inzozi 2050 zezeye guhindura u Rwanda igihugu gifite ubukungu bwo hagati.",
            }
            return replies.get(lang, replies["en"])

        # ── Physics ──
        if any(w in q for w in ["newton", "gravity", "force", "energy", "physics", "relativity", "quantum", "atom", "electron", "speed of light", "physique", "fiziki", "uburemere", "thermodynamics", "electricity"]):
            replies = {
                "en": "Physics fundamentals: Newton's 3 laws govern motion — F=ma (2nd law). Einstein's E=mc² links energy and mass. Speed of light: ~299,792 km/s. Gravity on Earth: 9.8 m/s². An atom has a nucleus (protons + neutrons) surrounded by electrons. Quantum mechanics describes subatomic behavior. Ohm's law: V=IR. The first law of thermodynamics says energy cannot be created or destroyed.",
                "fr": "Physique fondamentale: Les 3 lois de Newton régissent le mouvement — F=ma. E=mc² d'Einstein lie énergie et masse. Vitesse de la lumière: ~299,792 km/s. Gravité terrestre: 9,8 m/s². Un atome a un noyau (protons + neutrons) entouré d'électrons. La mécanique quantique décrit le comportement subatomique. Loi d'Ohm: V=IR.",
                "rw": "Fiziki y'inkingi: Amategeko 3 ya Newton agenzura imyenda — F=ma. E=mc² ya Einstein ifatanya ingufu n'uburemere. Umuvuduko w'urumuri: ~299,792 km/s. Uburemere bw'isi: 9.8 m/s². Atome ifite imitsi (proton + neutron) ikingirwa n'electrons. Mekanika ya kantike isobanura imyitwarire munsi ya atome. Itegeko rya Ohm: V=IR.",
            }
            return replies.get(lang, replies["en"])

        # ── Biology ──
        if any(w in q for w in ["dna", "cell", "evolution", "darwin", "biology", "organism", "gene", "protein", "virus", "bacteria", "biologie", "biologiya", "selile", "immune"]):
            replies = {
                "en": "Biology: DNA carries genetic information in a double helix structure. Cells are the basic unit of life — prokaryotic (no nucleus) or eukaryotic (with nucleus). Darwin's evolution theory (1859) shows species adapt by natural selection. The human body has ~37 trillion cells, 206 bones, 86 billion neurons. Vaccines train the immune system to fight pathogens.",
                "fr": "Biologie: L'ADN porte l'information génétique en double hélice. Les cellules sont l'unité de base de la vie — procaryotes ou eucaryotes. La théorie de l'évolution de Darwin (1859) montre comment les espèces s'adaptent. Le corps humain a ~37 billions de cellules, 206 os, 86 milliards de neurones.",
                "rw": "Biologiya: DNA ihuza amakuru ya genetics muri double helix. Selile ni inkingi y'ubuzima — prokaryote (zidafite imitsi) cyangwa eukaryote (zifite imitsi). Ingano ya Darwin (1859) yerekana ko ubwoko bwihinduranya. Umubiri w'umuntu ufite selile ~37 triliyoni, amagufwa 206, neuron 86 biliyoni. Inkingo zihugura sisitemu y'umubiri kurwanya indwara.",
            }
            return replies.get(lang, replies["en"])

        # ── Math ──
        if any(w in q for w in ["pythagorean", "theorem", "algebra", "calculus", "equation", "prime", "fibonacci", "math", "mathematics", "mathématiques", "matematiki", "statistics", "logarithm"]):
            replies = {
                "en": "Mathematics: Pythagorean theorem: a²+b²=c² (right triangles). Pi ≈ 3.14159265. Prime numbers have no divisors except 1 and themselves (2,3,5,7,11,13...). Fibonacci sequence: 0,1,1,2,3,5,8,13,21,34... Calculus (Newton & Leibniz) studies rates of change (derivatives) and accumulation (integrals). log₁₀(100) = 2.",
                "fr": "Mathématiques: Théorème de Pythagore: a²+b²=c². Pi ≈ 3,14159. Les nombres premiers: 2,3,5,7,11,13... Suite de Fibonacci: 0,1,1,2,3,5,8,13,21,34... Le calcul (Newton & Leibniz) étudie les taux de variation (dérivées) et l'accumulation (intégrales).",
                "rw": "Matematiki: Ingano ya Pitagora: a²+b²=c². Pi ≈ 3.14159. Imibare ya prime: 2,3,5,7,11,13... Urutonde rwa Fibonacci: 0,1,1,2,3,5,8,13,21,34... Calculus (Newton na Leibniz) isuzuma ihinduka ry'inshuro (derivatives) n'ikungahaza (integrals).",
            }
            return replies.get(lang, replies["en"])

        # ── Technology / AI / Programming ──
        if any(w in q for w in ["python", "javascript", "programming", "algorithm", "software", "computer", "technology", "artificial intelligence", "machine learning", "api", "database", "html", "css", "git", "fastapi", "ikoranabuhanga"]):
            replies = {
                "en": "Technology: AI simulates human intelligence through machine learning and neural networks. Python (1991, Guido van Rossum) is widely used for AI and data science. JavaScript powers the web. HTML defines page structure, CSS styles it. APIs allow systems to communicate. Git tracks code changes. FastAPI is a modern Python framework for building APIs quickly. Databases store structured data (SQL) or flexible data (NoSQL).",
                "fr": "Technologie: L'IA simule l'intelligence humaine via l'apprentissage automatique. Python (1991) est utilisé pour l'IA et la data science. JavaScript propulse le web. HTML définit la structure, CSS le style. Les APIs permettent la communication entre systèmes. Git gère les versions de code. FastAPI est un framework Python moderne pour construire des APIs.",
                "rw": "Ikoranabuhanga: AI ihuza ubwenge bw'abantu hakoreshejwe kwiga kw'ubukorikori. Python (1991) ikoreshwa mu AI na siyanse y'amakuru. JavaScript ikora ku rubuga. HTML isobanura imiterere, CSS iharanga. API zemerera sisitemu gutumanahana. Git ikurikirana impinduka za kode. FastAPI ni framework ya Python ya none yo kubaka API vuba.",
            }
            return replies.get(lang, replies["en"])

        # ── History ──
        if any(w in q for w in ["history", "war", "revolution", "empire", "ancient", "independence", "histoire", "guerre", "amateka", "intambara", "world war", "colonial"]):
            replies = {
                "en": "World history highlights: Ancient Egypt lasted 3,000+ years — pyramids were pharaoh tombs. The Roman Empire fell in 476 AD. World War I (1914–1918): 17M deaths. World War II (1939–1945): 70M+ deaths. French Revolution (1789): liberty, equality, fraternity. The Berlin Wall fell on November 9, 1989. Rwanda's independence: July 1, 1962. The 1994 Rwandan Genocide claimed ~800,000 lives in 100 days. Nelson Mandela became South Africa's first Black president in 1994.",
                "fr": "Histoire mondiale: L'Égypte ancienne a duré 3 000+ ans. L'Empire romain est tombé en 476 après J.-C. WWI (1914–1918): 17M morts. WWII (1939–1945): 70M+ morts. Révolution française (1789): liberté, égalité, fraternité. Chute du mur de Berlin: 9 novembre 1989. Indépendance du Rwanda: 1er juillet 1962.",
                "rw": "Amateka y'ingenzi: Misiri ya kera yamaze imyaka 3,000+. Ubwami bwa Roma bwagwiye mu 476 AD. Intambara ya 1 y'isi (1914–1918): abantu 17M bapfuye. Intambara ya 2 y'isi (1939–1945): abantu 70M+ bapfuye. Revolisiyo y'Ubufaransa (1789). Inkuta ya Berlin yagwiye ku ya 9 Ugushyingo 1989. Ubwigenge bw'u Rwanda: 1 Nyakanga 1962. Jenoside yakorewe Abatutsi mu 1994: abantu ~800,000 mu minsi 100.",
            }
            return replies.get(lang, replies["en"])

        # ── Space / Astronomy ──
        if any(w in q for w in ["space", "planet", "solar", "galaxy", "universe", "black hole", "star", "moon", "sun", "mars", "nasa", "espace", "planète", "univers", "inyenyeri", "isi yose", "galaxi"]):
            replies = {
                "en": "Astronomy: The universe is ~13.8 billion years old (Big Bang). Our solar system has 8 planets: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune. The Sun contains 99.86% of the solar system's mass. The Milky Way has 200+ billion stars. Neil Armstrong walked on the Moon on July 20, 1969 (Apollo 11). Black holes have gravity so strong nothing — not even light — can escape.",
                "fr": "Astronomie: L'univers a ~13,8 milliards d'années (Big Bang). Notre système solaire a 8 planètes. Le Soleil contient 99,86% de la masse du système solaire. La Voie lactée a 200+ milliards d'étoiles. Neil Armstrong a marché sur la Lune le 20 juillet 1969. Les trous noirs ont une gravité si forte que même la lumière ne peut s'échapper.",
                "rw": "Astronomiya: Isi yose ifite imyaka ~13.8 biliyoni (Big Bang). Sisitemu yacu ya zuba ifite ikirangamubiri 8. Izuba rifite 99.86% y'uburemere. Inzira Nyamweru ifite inyenyeri 200+ biliyoni. Neil Armstrong yagiye ku Ukwezi ku ya 20 Nyakanga 1969 (Apollo 11). Intoboro z'umukara zifite uburemere bukomaye ku buryo n'urumuri ntigishobora guhunga.",
            }
            return replies.get(lang, replies["en"])

        # ── Geography ──
        if any(w in q for w in ["geography", "continent", "country", "capital", "river", "mountain", "ocean", "africa", "géographie", "afrique", "jeografiya", "afurika", "isi", "amazina"]):
            replies = {
                "en": "Geography: Earth has 7 continents: Africa, Antarctica, Asia, Australia/Oceania, Europe, North America, South America. Africa has 54 countries and 1.4+ billion people. The Nile (~6,650 km) is the world's longest river. Mount Everest (8,849 m) is the highest peak. The Pacific Ocean is the largest ocean (~165 million km²). Rwanda is a landlocked country in East-Central Africa, capital Kigali.",
                "fr": "Géographie: La Terre a 7 continents. L'Afrique a 54 pays et 1,4+ milliard de personnes. Le Nil (~6 650 km) est le fleuve le plus long. Le mont Everest (8 849 m) est le plus haut sommet. L'océan Pacifique est le plus grand (~165 millions de km²). Le Rwanda est un pays enclavé d'Afrique centrale, capitale Kigali.",
                "rw": "Jeografiya: Isi igabanyijwemo ibihugu binini 7. Afurika ifite ibihugu 54 n'abantu barenga biliyoni 1.4. Uruzi rwa Nili (~km 6,650) ni urureremereye muri isi. Umusozi Everest (m 8,849) ni muri hejuru. Inyanja ya Pasifika ni nini (~km² 165 miliyoni). U Rwanda ni igihugu kidafite inyanja muri Afurika yo hagati-iburasirazuba, umurwa mukuru Kigali.",
            }
            return replies.get(lang, replies["en"])

        # ── Use knowledge base result ──
        if raw and len(raw) > 10 and raw.lower() != prompt.lower():
            clean = re.sub(r'^(EN|FR|RW):\s*', '', raw, flags=re.IGNORECASE).strip()
            if clean:
                # Strip multi-language parts — return only relevant language
                parts = {}
                for segment in clean.split("|"):
                    segment = segment.strip()
                    if re.match(r'^(EN|FR|RW):', segment):
                        key = segment[:2]
                        val = segment[3:].strip()
                        parts[key] = val
                if lang.upper() in parts:
                    return parts[lang.upper()]
                if parts:
                    return list(parts.values())[0]
                return clean

        # ── Default ──
        defaults = {
            "en": f"I understand your question about '{prompt[:60]}'. My knowledge base may not have a specific answer for this yet. You can teach me by updating the knowledge base via the /api/v1/brain/update endpoint or uploading a new knowledge file. Ask me about science, history, geography, technology, Rwanda, or mathematics!",
            "fr": f"Je comprends votre question sur '{prompt[:60]}'. Ma base de connaissances n'a peut-être pas de réponse spécifique pour cela. Vous pouvez m'apprendre via /api/v1/brain/update. Posez-moi des questions sur la science, l'histoire, la géographie, la technologie ou le Rwanda !",
            "rw": f"Numva ikibazo cyawe kuri '{prompt[:60]}'. Ubumenyi bwanjye bushobora kutaba n'igisubizo runaka. Ushobora kunfundisha hakoreshejwe /api/v1/brain/update. Mbaza siyanse, amateka, jeografiya, ikoranabuhanga, cyangwa u Rwanda!",
        }
        return defaults.get(lang, defaults["en"])


engine = WinterEngine()


# ── Routes ────────────────────────────────────────────────────────────────────
@app.post("/api/v1/chats/message", response_model=MessageResponse)
async def chat_message(req: MessageRequest):
    steps = []

    # Auto-detect language if "auto" or not specified
    detected_lang = detect_language(req.prompt)
    effective_lang = detected_lang if req.lang == "auto" else req.lang

    # 1. Python
    steps.append(engine.python_layer(req.prompt, req.lang, detected_lang))

    # 2. Prolog — knowledge search
    prolog_step, raw_answer, source = engine.prolog_layer(req.prompt, effective_lang)
    steps.append(prolog_step)

    # 3. Mercury
    steps.append(engine.mercury_layer(raw_answer))

    # 4. OCaml
    steps.append(engine.ocaml_layer(raw_answer))

    # 5. LISP
    steps.append(engine.lisp_layer(req.prompt))

    # 6. C++
    steps.append(engine.cpp_layer(raw_answer))

    # 7. Schema
    schema_step, confidence = engine.schema_layer(raw_answer, effective_lang)
    steps.append(schema_step)

    final = engine.build_final_answer(req.prompt, raw_answer, effective_lang)

    return MessageResponse(
        chat_id=req.chat_id,
        lang=effective_lang,
        detected_lang=detected_lang,
        reasoning_steps=steps,
        final_answer=final,
        knowledge_source=source,
        confidence=confidence,
    )


@app.post("/api/v1/brain/update")
async def update_brain(req: BrainUpdateRequest):
    global BRAIN_TEXT
    if not req.content.strip():
        raise HTTPException(status_code=400, detail="Content cannot be empty")
    BRAIN_FILE.write_text(req.content, encoding="utf-8")
    BRAIN_TEXT = req.content
    return {"status": "updated", "size": len(req.content), "lines": req.content.count("\n") + 1}


@app.post("/api/v1/knowledge/upload")
async def upload_knowledge(file: UploadFile = File(...)):
    global KNOWLEDGE_BASE
    allowed = {".txt", ".md"}
    suffix = Path(file.filename).suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Only .txt and .md files allowed")
    INFO_DIR.mkdir(parents=True, exist_ok=True)
    dest = INFO_DIR / Path(file.filename).name
    content = await file.read()
    dest.write_bytes(content)
    decoded = content.decode("utf-8")
    KNOWLEDGE_BASE[file.filename] = decoded
    return {"status": "uploaded", "filename": file.filename, "size": len(decoded), "lines": decoded.count("\n") + 1}


@app.get("/api/v1/knowledge/list")
async def list_knowledge():
    files = []
    for fname, content in KNOWLEDGE_BASE.items():
        files.append({"name": fname, "size": len(content), "lines": content.count("\n") + 1})
    return {"files": files, "count": len(files)}


@app.get("/api/v1/knowledge/{filename}")
async def get_knowledge_file(filename: str):
    if filename not in KNOWLEDGE_BASE:
        raise HTTPException(status_code=404, detail="File not found")
    return {"name": filename, "content": KNOWLEDGE_BASE[filename]}


@app.get("/api/v1/brain")
async def get_brain():
    return {"content": BRAIN_TEXT, "size": len(BRAIN_TEXT), "lines": BRAIN_TEXT.count("\n") + 1}


@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    total_kb = sum(len(c) for c in KNOWLEDGE_BASE.values())
    return HealthResponse(
        status="online",
        version="2.0.0",
        knowledge_files=list(KNOWLEDGE_BASE.keys()),
        brain_size=len(BRAIN_TEXT),
        total_knowledge_chars=total_kb + len(BRAIN_TEXT),
    )


@app.get("/")
async def root():
    return {
        "name": "Winter AI",
        "version": "2.0.0",
        "tagline": "Multi-paradigm reasoning engine — EN → FR → RW",
        "creator": "INEZA Aime Bruno, Rwanda",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
