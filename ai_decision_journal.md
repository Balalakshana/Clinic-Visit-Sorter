# AI DECISION JOURNAL: CLINIC VISIT SORTER
**Course:** CIT AI-Native Engineering Programme · Semester 1 · Assessment 5  
**Author:** First-Year Decision and Computing Science Student  

---

### Entry 1: Architecture Selection – Rule Engine vs. Pure LLM vs. Hybrid
- **Context:** Deciding how to classify student visit notes accurately while guaranteeing clinical safety.
- **Option A (Pure LLM):** Let the LLM do all parsing, sorting, and red-flag elevation.
  *Rejection Reason:* LLMs suffer from non-deterministic hallucinations and can be bypassed by prompt injection or conversational downplaying (e.g., student begging for "routine").
- **Option B (Pure Rule-Based Regex):** Classify solely via keywords in Python.
  *Rejection Reason:* Inflexible with informal slang, typos, and multi-lingual colloquialisms (e.g., Tanglish).
- **Decision (Option C - Hybrid):** Use the LLM for flexible classification and summarization, but wrap it in an immutable Python safety harness:
  1. Priority can *only* increase, never decrease.
  2. Red flags in English, Tamil script, and Tanglish force priority to `see_now`.
  3. Strict schema validation and fallback to `today`.

---

### Entry 2: Handling Failures – Safe Fallback Strategy
- **Context:** What should happen when the LLM API is unavailable, the user has no API key, or the network times out?
- **Alternative Considered:** Default unclassified records to `routine` so the nurse is not overwhelmed.
- **Safety Violation:** If an unclassified student actually had internal bleeding or cardiac distress, defaulting to `routine` could kill them.
- **Decision:** As mandated by the specification, "Unknown is never routine." Unclassified records are defaulted to priority `today`, while still passing through the deterministic red-flag regex filter. If a red flag is detected, priority is promoted to `see_now`.

---

### Entry 3: Multi-Lingual & Regional Health Expressions
- **Context:** College students in Tamil Nadu naturally express acute distress in Tamil or Tanglish when in pain (e.g., "Nenju vali irukku", "Moochu vida mudiyala", "நெஞ்சு வலி").
- **Decision:** Explicitly support bilingual detection in both the system prompt exemplar set and the deterministic Python red-flag regex patterns. Patterns were compiled with case-insensitivity and word boundaries to catch both scripts.

---

### Entry 4: The No-Diagnosis Constraint
- **Context:** The LLM prompt occasionally outputs diagnostic summaries (e.g., "Possible asthma", "Suspected migraine").
- **Decision:** Implemented `remove_diagnosis()` in Python as an active post-processing filter. If any clinical condition or speculative word (`possible`, `likely`, `suspected`, etc.) appears, the summary is programmatically replaced with a clean, neutral symptom extract from the patient note, preserving nurse autonomy.

---

### Entry 5: Segregation of Privacy in Reporting
- **Context:** Formatting the final outputs.
- **Decision:** Separate outputs into two files with clear access boundaries:
  - `nurse_queue.csv` includes the full raw student note for medical reference by the registered nurse.
  - `summary.txt` contains strictly high-level counts and hourly arrival metrics for the health centre director, keeping student medical notes confidential.
