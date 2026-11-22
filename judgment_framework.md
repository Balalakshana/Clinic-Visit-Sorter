# JUDGMENT FRAMEWORK & SAFETY ANALYSIS
**Project:** Clinic Visit Sorter  
**Student:** First-Year Decision and Computing Science Student  
**Domain:** Campus Health Centre Triage  

---

### Core Principles
1. **Asymmetric Risk in Healthcare:** In clinical sorting, assigning a priority that is too low (False Negative / Under-triage) is catastrophic because a delayed patient can suffer permanent injury or death (e.g., untreated cardiac arrest or anaphylactic shock). Assigning a priority that is too high (False Positive / Over-triage) causes only minor nurse inconvenience or a brief delay for mild cases. Therefore, the system is deliberately biased towards higher urgency.
2. **The Nurse as the Final Decision-Maker:** AI is strictly a queue-organizing tool, never an autonomous medical agent. The registered nurse sees every single student, validates vital signs, and makes all medical decisions.
3. **Continuous Human Supervision:** The tool generates reports that are immediately accessible and inspectable by the triage nurse and health centre in-charge.

---

### Judgment Framework Table

| Component | 1. What could go wrong? | 2. How does the code catch it? | 3. What does the human do? |
| :--- | :--- | :--- | :--- |
| **Input Ingestion (`load_visits`)** | Missing file, malformed CSV, empty lines, or missing fields. | Wrapped in `try-except`. Checks file existence, strips whitespace, ignores empty IDs. | Nurse checks physical sign-in sheet if a student is omitted; can re-run CSV or manually add. |
| **LLM Classification API (`classify`)** | Network timeout, API outage, rate limiting, or malformed JSON returned. | Single automatic retry; schema validation via `is_valid()`; if still broken, invokes safe fallback with priority `today`. Never crashes. | Nurse reviews all cases assigned to `today` and adjusts based on visual student inspection. |
| **Urgency Prioritization (`raise_priority`)** | LLM misses subtle emergency note or is tricked by adversarial student into setting `routine`. | Python regex checks English, Tamil, and Tanglish red flags. Python only elevates priority to `see_now`; never lowers priority. | Nurse immediately sees students marked `see_now` at the top of the queue and performs rapid clinical assessment. |
| **Clinical Boundary Guard (`remove_diagnosis`)** | LLM hallucinating a medical diagnosis (e.g., "asthma attack", "cardiac arrest") causing student alarm. | Sanitization function scans for forbidden diagnostic and speculative terms and replaces them with neutral symptom descriptions. | Nurse performs true diagnostic evaluation using medical instruments, stethoscope, and professional history. |
| **Queue Organization (`sorted`)** | High-urgency student buried at bottom due to late arrival timestamp. | Stable multi-key sorting: primary key is Priority (`see_now`=1, `today`=2, `routine`=3), secondary key is arrival time. | Nurse calls students in the sorted order, maintaining clinical prioritization over simple FIFO arrival. |
| **Reporting (`write_reports`)** | Privacy leak (patient symptom notes exposed to administrative supervisors). | Segregation of duties: `nurse_queue.csv` has clinical notes for the nurse; `summary.txt` has only aggregate statistics for the in-charge. | Health centre director inspects hourly and priority trends to allocate nursing staff during peak hours. |

---

### Key Discussion Questions for Viva / Presentation

#### 1. Why is assigning a priority that is too low far more dangerous than one that is too high?
Under-triage (false low priority) means a student experiencing severe anaphylaxis, internal bleeding, or acute cardiac distress waits in line behind students requesting leave certificates. The delay can lead to irreversible physiological deterioration or death. In contrast, over-triage (false high priority) results in a nurse spending 30 seconds confirming that a student is stable and reprioritizing them. In medical AI, **sensitivity and safety take absolute precedence over efficiency**.

#### 2. Why must the nurse remain the final decision-maker?
An LLM processes only text; it cannot see patient pallor, measure oxygen saturation, check pulse, or observe diaphoresis (sweating). Legal, ethical, and clinical responsibility rests strictly with licensed healthcare personnel. The AI functions purely as an administrative triage assistant.

#### 3. How is human supervision maintained in this application?
- Every student remains in the queue (no one is discharged or dismissed by AI).
- The nurse queue is printed visibly to the console and saved to `nurse_queue.csv`.
- The nurse reviews the patient's original note alongside the AI summary before calling each student.
