# PROJECT SPECIFICATION: CLINIC VISIT SORTER
**Course:** CIT AI-Native Engineering Programme · Semester 1 · Assessment 5 (40%)  
**Domain:** Healthcare Triage (College Student Health Centre)  
**Author:** First-Year Decision and Computing Science Student  

---

### 1. Problem Statement
At peak college hours, up to 10+ students arrive within a 30-minute window at the student health centre. In a strict first-in, first-out (FIFO) queue, students with critical, life-threatening symptoms (e.g., chest pain, respiratory distress, anaphylaxis) risk waiting behind students who only require routine administrative paperwork (e.g., medical leave certificates, fitness test forms). 

### 2. Solution & Core Purpose
The **Clinic Visit Sorter** is a console-based Python tool that sorts student arrival notes using an LLM triage assistant combined with deterministic Python safety guards. It organizes the waiting queue into three urgency levels: `see_now`, `today`, and `routine`.

### 3. Absolute Boundaries (What the Tool Must NEVER Do)
- **NEVER diagnose or name diseases** (e.g., asthma, cardiac arrest, gastroenteritis).
- **NEVER prescribe treatment or offer medical advice**.
- **NEVER speculate or guess** (forbidden words: *possible, likely, suspected, maybe*).
- **NEVER remove a student from the queue** under any circumstance.
- **NEVER decrease an urgency priority** in Python. Priority may only be increased.
- **NEVER treat unknown/failed records as routine** (default fallback is strictly `today`).

### 4. Human-in-the-Loop Safeguard
The registered nurse retains 100% decision-making authority and clinical responsibility. The tool serves purely as an administrative prioritization assistant. The nurse physically sees every student in the queue.

### 5. Input Specification (`visits.csv`)
- **Format:** CSV with headers `id,time,note`
- **Volume:** Exactly 30 unique student records (`V01` through `V30`).
- **Timing:** Arrival timestamps between `09:00` and `12:00`.
- **Linguistic diversity:** Realistic student complaints written in English, Tamil script, and Tanglish (Tamil written in Latin script).
- **Category distribution:** Balanced coverage across all 6 categories, including normal conditions, life-threatening red flags, and administrative requests.

### 6. Classification Schema & JSON Format
The LLM returns raw JSON adhering to this schema:
```json
{
  "category": "injury",
  "priority": "today",
  "summary": "Twisted ankle, swelling and difficulty walking"
}
```
- **Categories:** `injury`, `fever_cold`, `stomach`, `pain`, `allergy`, `other`
- **Priorities:** `see_now`, `today`, `routine`
- **Summary Constraints:** 12 words maximum, symptoms/requests only, no disease names, no student names.

### 7. Red-Flag Symptoms & Safety Rules
The program detects life-threatening conditions using regex pattern matching:
1. Chest pain / Nenju vali (`நெஞ்சு வலி`, `nenju vali`)
2. Breathing difficulty / Moochu (`மூச்சு`, `moochu vida mudiyala`)
3. Fainting / Blackouts / Mayakkam (`மயக்கம்`, `fainted`)
4. Heavy bleeding (`bleeding heavily`)
5. Lip or facial swelling (`swelling in lips`, `face swelling`)
6. Severe pain preventing standing (`cannot stand`, `unable to stand`)

**Rule:** Any red flag immediately forces priority to `see_now`.

### 8. Output Specifications
1. `nurse_queue.csv`: Ordered primarily by priority (`see_now` > `today` > `routine`), secondarily by arrival time. Contains full triage details for the nurse.
2. `summary.txt`: High-level aggregate statistics (total students, priority breakdown, category distribution, hourly arrival breakdown, red-flag count). Strictly omits individual student notes to protect student health privacy.
