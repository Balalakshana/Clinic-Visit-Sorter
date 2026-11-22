# CLINIC VISIT SORTER

**CIT AI-Native Engineering Programme · Semester 1 · Assessment 5**  
**Author:** First-Year Decision and Computing Science Student  
**Domain:** Healthcare Triage (College Student Health Centre)  

---

## 1. Project Overview
At peak times, over ten students arrive at the campus health centre within thirty minutes. Under traditional first-in, first-out (FIFO) queues, students with critical, life-threatening symptoms (e.g., chest pain, respiratory distress) risk waiting behind students who only require routine administrative paperwork (e.g., medical leave certificates).

The **Clinic Visit Sorter** is a console-based Python application that sorts student arrival notes by urgency and clinical category using a hybrid architecture: an LLM triage assistant bounded by strict, deterministic Python safety guards.

### Core Safety Rules
1. **Never Diagnoses:** The tool never provides medical advice, prescribes medication, or guesses disease names.
2. **Never Removes Anyone:** Every student remains in the queue.
3. **Nurse Retains Final Authority:** The registered nurse sees every student and makes all clinical decisions.
4. **Priority Only Increases:** Python red-flag detectors can elevate priority to `see_now`, but can *never* lower a priority.
5. **Unknown is Never Routine:** If the LLM API fails or is unavailable, the system safely defaults to priority `today` (never `routine`), and continues to check red flags deterministically.

---

## 2. Directory Structure

```text
clinic_visit_sorter/
│
├── visits.csv              # Input: Exactly 30 student records (V01 to V30)
├── system_prompt.txt       # System prompt built on 5-role framework
├── main.py                 # Main console application
├── test_cases.py           # Evaluation harness (5 normal + 3 red-team tests)
├── .gitignore              # Prevents API keys, environments & cache leaks
├── README.md               # Complete setup, running & project documentation
│
├── specification.md        # One-page official project specification
├── judgment_framework.md   # Judgment Framework table & human-in-the-loop analysis
├── cost_and_latency.md     # Engineering cost, volume & latency calculations
├── ai_decision_journal.md  # Architectural decisions and trade-offs
├── evaluation_results.md   # Detailed test harness & red-team evaluation results
└── reflection.md           # 400-word learning reflection for showcase
```

---

## 3. How to Run the Project (Windows / VS Code / Windows Terminal)

### Prerequisites
- Python 3.10+ installed and added to PATH.
- No external third-party dependencies are required (built strictly with the Python Standard Library: `csv`, `json`, `os`, `re`, `urllib`, `sys`).

### Quick Start (Deterministic Offline Fallback Mode)
1. Open Windows Terminal or Command Prompt.
2. Navigate to the project directory:
   ```cmd
   cd C:\Users\ELCOT\.gemini\antigravity\scratch\clinic_visit_sorter
   ```
3. Run the main program:
   ```cmd
   python main.py
   ```
   *The program will automatically detect that no key is present, output a clear notice, run the safe fallback engine, and generate `nurse_queue.csv` and `summary.txt`.*

4. Run the evaluation and adversarial red-team tests:
   ```cmd
   python test_cases.py
   ```

---

## 4. Configuring the LLM API Key Safely

To enable live online LLM classification, set your API key as an environment variable in your terminal session before launching the script. **Never hardcode API keys inside your code.**

### In Windows PowerShell:
```powershell
$env:LLM_API_KEY="your-api-key-here"
python main.py
```

### In Windows Command Prompt (CMD):
```cmd
set LLM_API_KEY=your-api-key-here
python main.py
```

### In VS Code:
You can create a `.env` file in the project folder with:
```text
LLM_API_KEY=your-api-key-here
```
*(The provided `.gitignore` automatically prevents `.env` and API keys from ever being committed to GitHub).*

---

## 5. Input Data Format (`visits.csv`)
The input file contains exactly 30 student records arriving between `09:00` and `12:00`:
- **Header:** `id,time,note`
- **Linguistic diversity:** Real-world student phrasing in English, Tamil script, and Tanglish.
- **Balanced categories:** `injury`, `fever_cold`, `stomach`, `pain`, `allergy`, and `other`.
- **Sample records:**
  - `V04,09:31,Chest pain and difficulty breathing after climbing stairs`
  - `V05,09:38,Nenju vali irukku romba heavy feeling left side`
  - `V06,09:44,Need a medical certificate for missing yesterday's class`
  - `V29,11:58,நெஞ்சு வலி மூச்சு திணறல் பயமாக இருக்கிறது`

---

## 6. Output Files Generated Automatically

1. **`nurse_queue.csv`**
   - For the registered nurse's examination desk.
   - Sorted primarily by urgency (`see_now` > `today` > `routine`), secondarily by arrival time.
   - Includes: `id`, `time`, `priority`, `category`, `is_red_flag`, `summary`, and original `note`.
2. **`summary.txt`**
   - For the campus health centre in-charge / director.
   - Summarizes total student volume, priority-wise distribution, category statistics, and hourly arrival trends.
   - Strictly omits individual student notes to protect student health privacy.

---

## 7. Recommended Git Commits
When Git is available on your computer, create these three meaningful commits to track project evolution:

1. **Commit 1 (Specification & Input Data):**
   ```bash
   git init
   git add .gitignore specification.md visits.csv system_prompt.txt
   git commit -m "feat: add project specification, 30 student input records, and system prompt"
   ```
2. **Commit 2 (Core Application & Safety Harness):**
   ```bash
   git add main.py
   git commit -m "feat: implement clinic visit sorter with red-flag detection and safe fallback"
   ```
3. **Commit 3 (Evaluation, Red-Team & Documentation):**
   ```bash
   git add test_cases.py README.md judgment_framework.md cost_and_latency.md ai_decision_journal.md evaluation_results.md reflection.md
   git commit -m "docs and test: add test harness, red-team suite, judgment framework, and reflection"
   ```
