# Project Memory & Context Graph (MEMORY.md)

**AI INSTRUCTION**: If you are a new AI agent reading this, this is the persistent memory file for the `opti-battery` project. 
1. **READ THIS FILE** carefully to understand the context, goals, and current state of the project before assisting the user.
2. **UPDATE THIS FILE** after every significant new reply, development, or architectural change. Add an entry to the "Memory Graph" section below so the next AI knows exactly what happened.

---

## 🎯 The Ultimate Goal: The "Holy Grail" Battery
The user is building a Solid-State Battery Informatics & Simulation Dashboard. The goal is to mine and screen **already-catalogued** materials from public databases (Materials Project, GNoME, MatterGen) and rank them by metric against these aspirational "Insane Specifications". **IMPORTANT (do not overclaim):** this pipeline finds and ranks *existing* known entries — it does **not** discover a new element or new material, and every metric below is a *computed / DFT-theoretical* value, not a lab-measured battery cell.
- **Charging Speed**: 100% in < 60 Seconds (Graphene Super-highways)
- **Capacity**: 5 to 10 Days Runtime (Lithium-Sulfur Li-S)
- **Lifespan**: 10+ Years / Immortal (Self-Healing Polymers)
- **Form Factor**: Transparent & Credit-Card Thin (Structural Battery Composites)
- **Durability**: Bends, Flexes, & Bulletproof (Shear-Thickening Solid Electrolytes)
- **Passive Power**: Charges while walking/tapping (Piezoelectric Nanogenerators)

---

## 🏗️ Project Architecture
This is a modular Python package with a lightweight HTTP server dashboard.
- **`.env`**: Contains the `mp-api` key (`MP_API_KEY`).
- **`run.py`**: The main entrypoint. Run `python3 run.py` to start the web server on port 8085. It also supports CLI commands (e.g. `--mine`, `--screen`, `--piezo`).
- **`src/opti_battery/core/`**: The backend logic.
  - `client.py`: Connects to Materials Project API.
  - `analyzer.py`, `screener.py`, `performance.py`, `diffusion.py`, `voltage_window.py`, `custom_screener.py`, `piezo.py`: Specialized modules that simulate/query material properties. Caches are used for large datasets (`*_cache.json`).
- **`src/opti_battery/web/`**: The frontend.
  - `server.py`: Lightweight Python `http.server` handling API endpoints.
  - `templates/index.html`: The HTML/JS dashboard containing 8 tabs and a 3D WebGL crystal lattice visualizer (`3Dmol.js`).
- **`src/opti_battery/monitor/`**: Automated discovery watcher (registry, filters, store, scanner, notify, paper_miner, ml_surrogate). Run via `run_monitor.py` or `run.py --cli --scan`; cron in `.github/workflows/discovery.yml`.

---

## 📍 Current State
**Status**: ALL 5 STEPS of the blueprint's **software dashboard** are FULLY BUILT and operational. (This means the *tool* works — screening, visualizing, and generating synthesis paperwork. No physical battery has been built, synthesized, or measured. Outputs are candidate lists + RFQ documents, not a validated cell.)
- The user can view the dashboard, load sample CIFs, or paste custom AI-generated CIFs from Microsoft MatterGen.
- **Eight** specialized tabs are live: Interface Stability, Electrode Performance, Diffusion Pathways, Electrochemical Window, MatterGen Sandbox, Piezoelectric Power, Synthesis Prep, and **Auto-Discovery** (the automated monitor feed).
- The **Synthesis Prep** tab automates Step 5 (Physical Build): paste a CIF and instantly generate a professional CRO Request for Quotation (RFQ) and Technical Synthesis Dossier.
- Next actions belong to the user (the researcher) to begin generating/screening actual materials and contacting CROs.

---

## 🧠 Memory Graph (Development Log)
*Append new developments to the top of this list.*

- **[2026-07-13] Session (cont.): CHATBOT + RESEARCH SECTION + BROADER PAPER COVERAGE; PUSHED TO GITHUB**:
  - **Paper coverage**: `paper_miner` now has `QUERY_SET` (8 overlapping arXiv queries) + `fetch_broad()` (merge + dedup by id + pagination + 3s politeness). `mine_papers(per_query, pages)` replaces the single 10-result query — sweeps the field, misses less.
  - **RESEARCH.md** (new, root): honest "what is our research / contribution" doc. Framing: materials are public MP entries; novelty = the *system* (unified multi-spec screening + shippability/toxic filter + self-updating watcher + RAG literature grounding + honesty). Served + indexed for chatbot.
  - **Chatbot** (`monitor/chatbot.py`): RAG over a Chroma `knowledge` collection (champions + top research_results + RESEARCH.md chunks) plus the `papers` collection; Groq answers grounded ONLY in context, instructed never to overclaim. `reindex_knowledge()` rebuilds from live state.
  - **rag.py** += `index_knowledge()` / `related_knowledge()` (knowledge collection).
  - **Server**: `GET /api/research` (RESEARCH.md), `POST /api/chat` (chatbot).
  - **Dashboard**: 2 new tabs — 🔬 Our Research (marked.js render) + 💬 Chatbot (RAG chat UI). Now 10 tabs total.
  - **Verified live**: chatbot answers grounded + honest (Li3N low-confidence), 24 knowledge chunks indexed; broad arXiv fetch parses; all compile; HTML div-balanced.
  - **Pushed** to https://github.com/meetp06/Research---Lab-Battery-Material-.git (`.env` gitignored — keys NOT pushed; `.env.example` documents required keys).

- **[2026-07-13] Session (cont.): LLM + RAG LAYER ADDED (Groq + Chroma)**:
  - Stack: **Groq** (LLM, free key `GROQ_API_KEY`, default `llama-3.3-70b-versatile`) + **sentence-transformers** (all-MiniLM-L6-v2 embeddings, local/free) + **ChromaDB** (local persistent vector store at `chroma_db/`, gitignored). All optional — pipeline degrades gracefully if key/deps absent.
  - `monitor/llm.py` — 3 jobs: `is_relevant()` (drops off-topic papers, fails open), `extract_claim()` (abstract → {material,metric,value,unit}), `champion_verdict()` (RAG-grounded literature verdict + confidence).
  - `monitor/rag.py` — Chroma collections `papers` + `champions`; `add_papers()`, `add_champion()`, `related_papers()` semantic search.
  - Wired: `paper_miner.mine_papers()` now LLM-filters + extracts + embeds each kept paper; `scanner.scan_spec()` queries RAG + attaches `llm_verdict` to new champions. `run_monitor --papers` mines BEFORE scan so verdicts have context.
  - Dashboard Auto-Discovery feed shows 🧠 verdict (color by confidence) on champions and 🔬 extracted claim on papers.
  - **Verified live**: Groq relevance (supercap→drop, SSE→keep), claim extraction (Li6PS5Cl, 12 mS/cm), Chroma embed+semantic query (Li3N ranked top). All modules compile.
  - `requirements.txt` += groq, chromadb, sentence-transformers. `.env.example` documents `GROQ_API_KEY`/`GROQ_MODEL`/`NOTIFY_WEBHOOK`.
  - NOTE: LLM verdict = helpful summary layered on DFT numbers + cherry-picked papers. NOT experimental proof. Materials are still public MP entries — no new element.

- **[2026-07-13] Session (cont.): AUTOMATED DISCOVERY MONITOR BUILT**:
  - Goal: fully-automated system that periodically re-screens sources and records a new "champion" whenever a **better known** material appears (user's own idea; plays to their AI/ML background). It surfaces better *existing* materials — NOT new elements, NOT validated cells.
  - **Refactor**: moved the 5 screening functions into importable `src/opti_battery/core/research.py` (registry `RESEARCH_FUNCTIONS`); `run_research.py` is now a thin wrapper reusing it. No logic change.
  - **New package `src/opti_battery/monitor/`**:
    - `registry.py` — per-spec metric + direction; `BANNED_ELEMENTS` (radioactive + toxic heavy: Th, U, As, Pb, Cd, Hg, Be, …).
    - `filters.py` — `toxicity_check()` rejects unshippable candidates (this is why LiThF₅/thorium and NbAs/arsenic are auto-rejected now).
    - `store.py` — `discovery_state.json` (champions + last_scan) and append-only `discovery_history.json`.
    - `scanner.py` — `run_scan()`: re-screen → filter toxic → compare vs champion → crown + log + notify if strictly better.
    - `notify.py` — console + optional `NOTIFY_WEBHOOK` (Slack/Discord, stdlib urllib).
    - `paper_miner.py` — free arXiv poller (defusedxml) → literature signals; `extract_claim()` LLM hook stub.
    - `ml_surrogate.py` — scaffold for CHGNet/MatterSim fast pre-screen (roadmap; needs training + torch).
  - **Entrypoints**: `run_monitor.py` (cron: `--papers`, `--papers-only`), `run.py --cli --scan`.
  - **Automation**: `.github/workflows/discovery.yml` runs daily 06:00 UTC, commits state back. Secrets: `MP_API_KEY`, optional `NOTIFY_WEBHOOK`.
  - **Dashboard**: 8th tab **Auto-Discovery** + `GET /api/discovery` (champions + history feed).
  - **Verified offline** (mocked API): toxic candidate filtered, best safe one crowned, state+history written; comparator direction correct per spec; all modules byte-compile + import; defusedxml active.
  - `requirements.txt` += `defusedxml>=0.7.1`.

- **[2026-07-13] Session (cont.): HONESTY PASS — corrected overclaiming**:
  - Added a "📊 Target vs. What We Actually Achieved" table to `index.html` (Blueprint section): 4 columns — Insane Target, Achieved (screened candidate + computed metric), Reality Gap.
  - Corrected MEMORY.md wording to match. **Explicit for all future agents: NO new element was discovered, NO physical battery was built or measured, and ALL winning-candidate numbers are computed/DFT-theoretical values for existing `mp-xxxx` materials.**
  - Flagged real-world blockers now recorded inline: LiThF₅ contains thorium (radioactive), NbAs contains arsenic, LiAlB₁₄ high modulus = stiff (not flexible), Li₉S₃N capacity is a theoretical max. The pipeline's job = screen + rank a database, not invent or validate a cell.

- **[2026-07-13] Session 1 (cont.): Standard Baseline Requirements Added**:
  - Created `run_baseline.py` — validates all 6 winning candidates against 7 standard battery baseline checks (stability, formation energy, band gap, density, volume, symmetry, ion mobility).
  - **ALL 5 Li-based winners passed 7/7 baseline checks.** (These are database/DFT property gates — stability, formation energy, band gap, density, volume, symmetry, ion mobility — NOT physical/experimental validation.)
  - Updated dashboard Blueprint to show 3 sections: Layer 1 (Standard Requirements — 8 specs), Layer 2 (Insane Specifications — 6 specs), and Baseline Validation (green ✅ for all winners).
  - Results saved to `baseline_results.json`.

- **[2026-07-13] Session 1 (cont.): FULL RESEARCH PIPELINE EXECUTED — 94 Candidates Found**:
  - Created `run_research.py` — a comprehensive pipeline that queries Materials Project for all 5 remaining specs.
  - Results saved to `research_results.json` (94 total candidates).
  - **WINNING CANDIDATES** — all are *existing catalogued `mp-xxxx` materials*; every number below is a **computed / DFT-theoretical** value, NOT a lab-measured cell. See the "Target vs. Achieved" table in `index.html` for the honest Reality Gap on each:
    - ⚡ Charging Speed: **Li₃N** (mp-2251) — 2.08 Å Li-hop distance (fast-ion conductor). *Short hop ≠ full-pack charge in 60 s; MW-scale power + heat + Li plating still block that.*
    - 🔋 Capacity: **Li₉S₃N** (mp-557964) — 5,029 mAh/g **theoretical gravimetric max**. *Real cells fall far below (cathode, packaging, S shuttling losses).*
    - ♻️ Lifespan: **LiThF₅** (mp-1196169) — -4.12 eV/atom formation energy (thermodynamically stable). *Stability ≠ cycle life; and it contains **thorium (radioactive) → not shippable**.*
    - 📐 Form Factor: **LiS₄** (mp-995393) — 0.21 g/cm³ (low computed density only; thin/transparent needs a full device stack not modeled).
    - 🛡️ Durability: **LiAlB₁₄** (mp-8204) — 382 GPa stiffness/modulus score. *High modulus = **stiff, the opposite of flexible/bendable**.*
    - 🔌 Passive Power: **NbAs** (mp-2859) — 119 C/m² piezoelectric tensor (from prior session). *Piezo harvest = µW–mW trickle, won't meaningfully charge a phone; contains **arsenic**.*
  - Fixed a performance issue: `mpr.materials.elasticity.search()` downloads full dataset; switched to `mpr.materials.summary.search(has_props=["elasticity"])` for 100x speedup.

- **[2026-07-13] Session 1 (cont.): Synthesis Prep Feature Built**:
  - Created `src/opti_battery/core/synthesis.py` — parses CIF strings (via `CifParser` + `StringIO`) and auto-generates an email RFQ + technical dossier with crystallographic parameters, purity specs, and a CRO shortlist.
  - Added `POST /api/generate-rfq` endpoint in `server.py`.
  - Added 7th dashboard tab **"Synthesis Prep"** in `index.html`.
  - Fixed a `CifParser.from_string` bug (method doesn't exist; switched to `CifParser(StringIO(...))`).
  - Verified via `curl` — successfully generates RFQ for `Li2BeH4`.

- **[2026-07-13] Session 1: Foundation Built**: 
  - AI restructured the original monolithic scripts into a modular Python package.
  - Built the `run.py` CLI and web server.
  - Integrated the 3D WebGL Crystal visualizer.
  - Built the **MatterGen Sandbox** tab for custom `.cif` parsing.
  - Built the **Piezoelectric Power** tab to fetch top nanogenerator materials.
  - Created this `MEMORY.md` file and configured `.agents/AGENTS.md` to ensure future AI agents automatically inherit this context.
