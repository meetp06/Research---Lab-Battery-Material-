# Opti-Battery Material Discovery Informatics Tool

Opti-Battery is a production-grade materials informatics toolkit designed to screen and discover lightweight lithium-based solid-state electrolyte and electrode candidates using the Materials Project database.

---

## Directory Structure

```text
opti-battery/
├── .env.example              # Template for configuring API keys securely
├── .gitignore                # Standard Python and IDE git exclusion rules
├── README.md                 # Project documentation
├── requirements.txt          # Defined dependencies
├── run.py                    # Application entrypoint
├── src/
│   └── opti_battery/
│       ├── __init__.py       # Version declaration
│       ├── config.py         # Configuration loader (API keys)
│       ├── core/
│       │   ├── __init__.py   # Sub-module imports
│       │   ├── client.py     # MPRester connection manager
│       │   ├── miner.py      # Database candidate querying logic
│       │   ├── screener.py   # SSE vs. Electrode partitioning logic
│       │   └── analyzer.py   # Interfacial reaction thermodynamics calculations
│       └── web/
│           ├── __init__.py   # Web server exports
│           ├── server.py     # HTTP API backend server
│           └── templates/
│               └── index.html # Clean white UI dashboard frontend
```

---

## Installation & Setup

1. **Clone or navigate to the workspace**:
   ```bash
   cd opti-battery
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your API Key**:
   - Register for a free API key at [next-gen.materialsproject.org](https://next-gen.materialsproject.org/).
   - Create a `.env` file in the root of the project:
     ```env
     MP_API_KEY=your_actual_api_key_here
     ```

---

## Usage

Opti-Battery supports both a CLI interface for quick scripting and a Web Dashboard for interactive manual testing.

### 1. Web Dashboard (Default)
To run the interactive white-screen web dashboard:
```bash
python3 run.py
```
Then open your browser to **[http://localhost:8085](http://localhost:8085)**.

### 2. Command Line Interface (CLI)
You can run automated queries and screens directly from your terminal:

* **Mine candidate Lithium materials** (sorted by density):
  ```bash
  python3 run.py --cli --mine
  ```

* **Screen and partition candidates** into Solid-State Electrolytes vs. Conductive Electrodes:
  ```bash
  python3 run.py --cli --screen
  ```

---

## Features

* **Candidate Mining**: Pulls active materials containing Lithium, excluding toxic elements, filtered under a density threshold (defaults to `< 3.0 g/cm³`).
* **Electrode vs. Electrolyte Screening**: Partitions compounds into electronic conductors (`is_metal=True` or `band_gap=0`) and electronic insulators (`band_gap > 2.0 eV`) suitable for solid-state separation.
* **Interfacial Thermodynamic Modeling**: Analyzes the decomposition reactions and driving force energy of solid-state electrolytes when placed in contact with active anode (Lithium metal) and cathode (Sulfur) compositions.
* **Automated Discovery Monitor**: A scheduled watcher (`src/opti_battery/monitor/`) that re-screens the Materials Project for all 5 specs, auto-rejects toxic/radioactive candidates, and crowns a new "champion" only when a better *known* material appears. Also mines recent arXiv papers as literature signals.

---

## Automated Discovery (Auto-Find "Better" Materials)

The monitor surfaces better **existing** materials as the databases grow. It does **not**
discover new elements and does **not** validate physical cells — every metric is a
computed / DFT-theoretical value.

**Run one scan manually:**
```bash
python3 run_monitor.py            # re-screen all 5 specs
python3 run_monitor.py --papers   # + mine recent arXiv papers
python3 run.py --cli --scan       # same scan via the main CLI
```

Results persist to `discovery_state.json` (current champions) and
`discovery_history.json` (append-only feed), both surfaced in the dashboard's
**Auto-Discovery** tab (`GET /api/discovery`).

**Run it on autopilot:** `.github/workflows/discovery.yml` runs a scan daily (06:00 UTC)
and commits any new champions/signals back. Add repo secrets:
* `MP_API_KEY` (required) — Materials Project key.
* `NOTIFY_WEBHOOK` (optional) — Slack/Discord/webhook URL for alerts.

**Safety filter:** candidates containing radioactive or acutely toxic elements
(thorium, arsenic, lead, cadmium, mercury, beryllium, …) are auto-rejected — this is why
the old "winners" LiThF₅ (thorium) and NbAs (arsenic) will not be crowned again.

**Fast pre-screen (roadmap):** `monitor/ml_surrogate.py` is a scaffold for an ML
surrogate (CHGNet / MatterSim) to pre-rank millions of candidates before the expensive
screening — the highest-leverage next step for an AI/ML developer.

### LLM + RAG layer (optional, free)

With a free **Groq** key (`GROQ_API_KEY`) the monitor gains three LLM abilities,
all degrading gracefully if the key/deps are absent:
* **Relevance filter** — drops off-topic papers before storing.
* **Claim extraction** — pulls `{material, metric, value}` from abstracts.
* **Champion verdict** — a cautious, literature-grounded confidence note per champion.

Papers are embedded (sentence-transformers) into a local **ChromaDB** vector store
(`chroma_db/`) for semantic retrieval. Paper coverage is broad: `paper_miner.QUERY_SET`
runs several overlapping arXiv queries per scan and de-duplicates, so a single scan
sweeps the field rather than one narrow phrase.

### Project chatbot & "Our Research"

* **Chatbot tab** (`POST /api/chat`) — ask questions about the project; answers are
  RAG-grounded in the champions, `research_results.json`, indexed papers, and
  `RESEARCH.md`, via Groq.
* **Our Research tab** (`GET /api/research`) — renders `RESEARCH.md`, the place to
  record the project's actual contribution/novelty. Editing it also updates what the
  chatbot knows.
