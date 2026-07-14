# Our Research & Contribution

> This is the place to record **what is genuinely ours** — the parts a reader
> could not get just by browsing a public database. Edit this file freely; it is
> served to the dashboard "Our Research" tab **and** indexed into the chatbot's
> knowledge base, so anything you write here becomes answerable by the assistant.

---

## Honest framing (read first)

The individual **materials** we surface (Li₃N, Li₉S₃N, LiLuF₄, LiS₄, LiAlB₁₄, …)
are **not new** — each is an already-catalogued Materials Project entry with an
`mp-xxxx` id, computed by others. Every metric is a **computed / DFT-theoretical**
value, not a lab-measured cell. So the novelty is **not** "we found a new element."

The novelty is the **system and the methodology**: an automated, honest,
literature-aware discovery loop that most single tools do not combine.

---

## What is actually ours (the contribution)

1. **Unified multi-spec screening in one pipeline.** Five "impossible" battery
   goals (charging speed, capacity, lifespan, form factor, durability) screened
   from the same database with one consistent, reproducible ranking method.

2. **A shippability-aware safety filter.** We auto-reject radioactive / toxic
   winners (thorium, arsenic, lead, cadmium, …). This is why our Lifespan
   champion is the *safe* LiLuF₄ instead of the naive top hit **LiThF₅ (thorium)**
   — a mistake a raw "best number" screen makes.

3. **A self-updating watcher.** A scheduled monitor re-screens as the databases
   grow and only crowns a new champion when a *strictly better, safe* material
   appears — so the "best known" list maintains itself over time.

4. **Literature grounding (RAG).** Every crowned champion is cross-checked
   against recent papers pulled from arXiv, semantically matched, and given a
   cautious LLM verdict + confidence — instead of trusting a lone DFT number.

5. **Honesty as a feature.** The dashboard explicitly separates the marketing
   "insane targets" from what was actually achieved (the "Reality Gap" table),
   and the assistant is instructed never to overstate DFT rank as proof.

---

## What would make it truly novel (roadmap)

To move from "screens known materials" to "proposes materials no one has":

- **Generate** candidate structures with MatterGen (already have the sandbox tab),
  then screen the *generated* structures — those can be genuinely new.
- **Train an ML surrogate** (CHGNet / MatterSim) to pre-rank millions cheaply.
- **Extract quantitative claims** from full papers (not just abstracts) and
  compare them head-to-head with our DFT champions.

---

## Our specific findings / notes

<!-- Write your own observations, hypotheses, and results below. This section is
     indexed for the chatbot, so future questions like "what did we conclude about
     LiLuF4?" will use whatever you record here. -->

- (add your notes here)
