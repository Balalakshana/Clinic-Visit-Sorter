"""
Clinic Visit Sorter - Main Program
CIT AI-Native Engineering Programme · Semester 1 · Assessment 5

Author: First-Year Decision & Computing Science Student
Domain: Health (College Student Health Centre)
Description:
    Reads student arrival notes from visits.csv, classifies urgency and category
    using LLM integration (or deterministic fallback), detects life-threatening
    red-flag symptoms (including Tamil/Tanglish phrases), enforces clinical safety
    rules (priority elevation only, strictly no medical diagnosis), and generates
    the organized nurse queue (nurse_queue.csv) and administrative summary (summary.txt).
"""

import csv
import json
import os
import re
import sys
import urllib.request
import urllib.error

# Ensure stdout and stderr handle UTF-8 properly on Windows consoles
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def load_env_file(env_path=".env"):
    """Auto-load key-value pairs from .env if present without third-party dependencies."""
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k and not os.environ.get(k):
                            os.environ[k] = v
        except Exception:
            pass

load_env_file()

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================

VALID_CATEGORIES = ["injury", "fever_cold", "stomach", "pain", "allergy", "other"]
VALID_PRIORITIES = ["see_now", "today", "routine"]

# Priority ranking used for sorting (lower numeric rank = seen first)
PRIORITY_ORDER = {
    "see_now": 1,
    "today": 2,
    "routine": 3
}

# Red-flag keywords and phrases (English, Tamil, and Tanglish)
# Life-threatening conditions: chest pain, breathing difficulty, fainting,
# heavy bleeding, facial/lip swelling, and inability to stand.
RED_FLAG_PATTERNS = [
    # English symptoms
    r"\bchest pain\b",
    r"\bdifficulty breathing\b",
    r"\bbreathing difficulty\b",
    r"\bshortness of breath\b",
    r"\bfaint\b",
    r"\bfainted\b",
    r"\bfainting\b",
    r"\bblackout\b",
    r"\bblacking out\b",
    r"\bheavy bleeding\b",
    r"\bbleeding heavily\b",
    r"\blip swelling\b",
    r"\bface swelling\b",
    r"\bswelling in lips\b",
    r"\bcannot stand\b",
    r"\bunable to stand\b",
    r"\bblurred vision\b",
    r"\bblurry vision\b",
    # Tamil script
    r"நெஞ்சு\s*வலி",
    r"மூச்சு",
    r"மயக்கம்",
    r"ரத்தப்போக்கு",
    # Tanglish transliterations
    r"\bnenju\s*vali\b",
    r"\bmoochu\b",
    r"\bmoochu\s*vida\s*mudiyala\b",
    r"\bmayakkam\b"
]

# Forbidden diagnostic terms and speculative words
DIAGNOSIS_FORBIDDEN_WORDS = [
    "possible", "likely", "probable", "maybe", "suspected", "potential",
    "asthma", "migraine", "cardiac", "heart attack", "appendicitis",
    "bronchitis", "pneumonia", "concussion", "fracture", "covid",
    "infection", "gastroenteritis", "anaphylaxis", "depression", "arthritis"
]


# ==============================================================================
# COMPULSORY CORE FUNCTIONS
# ==============================================================================

def load_visits(file_path="visits.csv"):
    """
    Compulsory Function 1: load_visits()
    Reads student arrival records from a CSV file.
    Returns a list of dictionaries with keys: 'id', 'time', 'note'.
    """
    records = []
    if not os.path.exists(file_path):
        print(f"[ERROR] Input file '{file_path}' not found.")
        return records

    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cleaned_record = {
                    "id": row.get("id", "").strip(),
                    "time": row.get("time", "").strip(),
                    "note": row.get("note", "").strip()
                }
                if cleaned_record["id"]:
                    records.append(cleaned_record)
    except Exception as e:
        print(f"[ERROR] Failed to read '{file_path}': {e}")

    return records


def is_valid(response_dict):
    """
    Compulsory Function 3: is_valid()
    Validates that the LLM response dictionary contains all required fields,
    allowed category and priority values, and adheres to summary length limits.
    Returns (True, "") if valid, or (False, reason) if invalid.
    """
    if not isinstance(response_dict, dict):
        return False, "Response is not a dictionary"

    # Check required keys
    for key in ["category", "priority", "summary"]:
        if key not in response_dict:
            return False, f"Missing key: {key}"

    category = response_dict["category"]
    priority = response_dict["priority"]
    summary = response_dict["summary"]

    # Validate category
    if category not in VALID_CATEGORIES:
        return False, f"Invalid category: {category}"

    # Validate priority
    if priority not in VALID_PRIORITIES:
        return False, f"Invalid priority: {priority}"

    # Validate summary
    if not isinstance(summary, str) or not summary.strip():
        return False, "Summary must be a non-empty string"

    words = summary.strip().split()
    if len(words) > 12:
        return False, f"Summary exceeds 12 words (count: {len(words)})"

    return True, "Valid"


def raise_priority(llm_priority, note):
    """
    Compulsory Function 4: raise_priority()
    Inspects student note for red-flag keywords in English, Tamil, and Tanglish.
    Safety Invariant:
        - Priority can ONLY be increased, NEVER decreased.
        - If a red flag is found, priority is elevated to 'see_now'.
    Returns a tuple: (final_priority, is_red_flag)
    """
    note_lower = note.lower()
    is_red_flag = False

    for pattern in RED_FLAG_PATTERNS:
        if re.search(pattern, note_lower, re.IGNORECASE):
            is_red_flag = True
            break

    # Red-flag rule: Elevate to see_now
    if is_red_flag:
        return "see_now", True

    # If no red flag, retain existing priority (Python never lowers priority)
    return llm_priority, False


def remove_diagnosis(summary, note):
    """
    Compulsory Function 5: remove_diagnosis()
    Enforces the clinical safety rule: The tool NEVER diagnoses or guesses.
    Checks the summary for speculative words or clinical disease names.
    If any are detected, sanitizes the summary into a neutral symptom description.
    """
    summary_lower = summary.lower()
    violation_found = False

    for word in DIAGNOSIS_FORBIDDEN_WORDS:
        if re.search(rf"\b{re.escape(word)}\b", summary_lower):
            violation_found = True
            break

    if violation_found:
        # Filter forbidden words even if present in the user's raw note
        words = [w for w in note.split() if w.lower().strip("?,.") not in DIAGNOSIS_FORBIDDEN_WORDS]
        safe_snippet = " ".join(words[:10])
        if safe_snippet:
            return f"Symptoms reported: {safe_snippet}"
        return "Symptoms reported: General clinical complaint"

    return summary


def call_llm_api(system_prompt, user_note, api_key):
    """
    Helper function to send the note to an OpenAI-compatible / Gemini-compatible endpoint
    using standard urllib without external dependencies.
    """
    # Configurable endpoint via environment, defaulting to standard OpenAI chat endpoint
    endpoint = os.environ.get("LLM_API_ENDPOINT", "https://api.openai.com/v1/chat/completions")
    model_name = os.environ.get("LLM_MODEL", "gpt-3.5-turbo")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        # Groq's Cloudflare front end rejects urllib's default User-Agent (error 1010 / HTTP 403)
        "User-Agent": "clinic-visit-sorter/1.0"
    }

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Note: {user_note}"}
        ],
        "temperature": 0.0
    }
    # Reasoning models (e.g. openai/gpt-oss-*) accept reasoning_effort; "low" cuts tokens per call
    # Set LLM_REASONING_EFFORT=off to send null, which disables reasoning (e.g. Sarvam)
    reasoning_effort = os.environ.get("LLM_REASONING_EFFORT")
    if reasoning_effort:
        payload["reasoning_effort"] = None if reasoning_effort.lower() in ("off", "null") else reasoning_effort

    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=10) as resp:
        res_data = json.loads(resp.read().decode("utf-8"))
        content = res_data["choices"][0]["message"].get("content")
        if not content:
            # Reasoning models can spend the whole token budget "thinking" and return no answer
            raise ValueError("LLM returned empty content (finish_reason: "
                             f"{res_data['choices'][0].get('finish_reason')})")
        content = content.strip()
        # Strip potential markdown formatting if returned
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())


def classify_fallback(note):
    """
    Deterministic rule-based fallback when LLM API is unavailable or returns invalid data.
    As per spec:
      - Assigns priority based on clinical urgency:
        * Administrative/routine requests (certificates, permission, eye test, routine checkup) -> 'routine'
        * Urgent conditions (injuries, severe pain, active infections) -> 'today'
      - Red-flag conditions are subsequently raised to 'see_now' by raise_priority().
      - If truly unknown/unclassifiable, priority defaults to 'today' (unknown is never routine).
    """
    note_lower = note.lower()

    def has_any(keywords):
        # Whole-word match, so "burn" does not match "burning" and "cut" does not match "acute"
        return any(re.search(rf"\b{re.escape(k)}\b", note_lower) for k in keywords)

    # 1. Check for administrative or mild routine requests
    is_routine_request = has_any([
        "certificate", "medical certificate", "leave permission", "fitness form",
        "routine checkup", "checkup routine", "eye test", "permission slip"
    ])

    # 2. Determine best-effort category
    # Order matters: more specific categories are checked first
    # (e.g. "dust allergy ... sneezing" is allergy, "migraine ... nausea" is pain)
    if has_any(["ankle", "cut", "cuts", "bleeding", "cycling", "fell", "burn", "burns", "burnt",
                "scratch", "scratched", "blade", "sprain", "sprained"]):
        category = "injury"
    elif has_any(["allergy", "allergic", "rash", "rashes", "itching", "swelling in lips", "hives"]):
        category = "allergy"
    elif has_any(["fever", "cold", "cough", "sneezing", "shivering", "chills"]):
        category = "fever_cold"
    elif has_any(["headache", "migraine", "thalai"]):
        category = "pain"
    elif has_any(["stomach", "vomiting", "loose stools", "vayiru", "acidity", "nausea"]):
        category = "stomach"
    elif has_any(["throat pain", "knee pain", "back spasm", "pain", "vali"]):
        category = "pain"
    elif is_routine_request:
        category = "other"
    else:
        category = "other"

    # 3. Assign priority
    if is_routine_request:
        priority = "routine"
    else:
        priority = "today"

    # Generate concise summary (<= 12 words)
    words = note.split()
    summary = " ".join(words[:10])

    return {
        "category": category,
        "priority": priority,
        "summary": summary
    }


def classify(note, system_prompt, api_key=None):
    """
    Compulsory Function 2: classify()
    Manages LLM classification lifecycle:
    1. If api_key is present, calls LLM API.
    2. Validates JSON structure using is_valid().
    3. If invalid or error occurs, retries once.
    4. If retry fails or API key is absent, safely falls back to classify_fallback().
       (Fallback priority is always 'today').
    5. Applies remove_diagnosis() to guarantee no diagnosis leaks into summary.
    6. Calls raise_priority() to check red-flag symptoms and elevate if necessary.
    """
    result = None

    if api_key:
        # Attempt 1
        try:
            raw_result = call_llm_api(system_prompt, note, api_key)
            valid, reason = is_valid(raw_result)
            if valid:
                result = raw_result
        except Exception:
            # Retry once on failure
            try:
                raw_result = call_llm_api(system_prompt, note, api_key)
                valid, reason = is_valid(raw_result)
                if valid:
                    result = raw_result
            except Exception:
                result = None

    # Safe fallback if API was unavailable, missing key, or failed twice
    if not result:
        result = classify_fallback(note)

    # Clean summary (remove forbidden diagnosis terms)
    clean_summary = remove_diagnosis(result["summary"], note)
    result["summary"] = clean_summary

    # Elevate priority if red-flag detected (Python priority only increases)
    final_priority, is_red_flag = raise_priority(result["priority"], note)
    result["priority"] = final_priority
    result["is_red_flag"] = is_red_flag

    return result


def write_reports(sorted_queue, queue_file="nurse_queue.csv", summary_file="summary.txt"):
    """
    Compulsory Function 6: write_reports()
    Generates two distinct reports:
    1. nurse_queue.csv: Full triage details for the nurse.
    2. summary.txt: Aggregate administrative counts for the health centre in-charge
       (strictly excludes student notes to safeguard patient privacy).
    """
    # 1. Write nurse_queue.csv
    try:
        with open(queue_file, mode="w", newline="", encoding="utf-8") as f:
            fieldnames = ["id", "time", "priority", "category", "is_red_flag", "summary", "note"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for student in sorted_queue:
                writer.writerow({
                    "id": student["id"],
                    "time": student["time"],
                    "priority": student["priority"],
                    "category": student["category"],
                    "is_red_flag": "YES" if student["is_red_flag"] else "NO",
                    "summary": student["summary"],
                    "note": student["note"]
                })
    except Exception as e:
        print(f"[ERROR] Failed to write '{queue_file}': {e}")

    # 2. Compute aggregate statistics for summary.txt
    total_students = len(sorted_queue)
    priority_counts = {"see_now": 0, "today": 0, "routine": 0}
    category_counts = {cat: 0 for cat in VALID_CATEGORIES}
    hour_counts = {}
    red_flag_count = 0

    for s in sorted_queue:
        p = s["priority"]
        c = s["category"]
        t = s["time"]

        priority_counts[p] = priority_counts.get(p, 0) + 1
        category_counts[c] = category_counts.get(c, 0) + 1
        if s["is_red_flag"]:
            red_flag_count += 1

        hour = t.split(":")[0] if ":" in t else "Unknown"
        hour_label = f"{hour}:00 - {hour}:59"
        hour_counts[hour_label] = hour_counts.get(hour_label, 0) + 1

    # Write summary.txt
    try:
        with open(summary_file, mode="w", encoding="utf-8") as f:
            f.write("=====================================================\n")
            f.write("      COLLEGE HEALTH CENTRE - CLINIC VISIT SUMMARY   \n")
            f.write("=====================================================\n\n")
            f.write(f"Total Students Processed: {total_students}\n\n")

            f.write("--- PRIORITY DISTRIBUTION ---\n")
            f.write(f"  SEE NOW : {priority_counts.get('see_now', 0)}\n")
            f.write(f"  TODAY   : {priority_counts.get('today', 0)}\n")
            f.write(f"  ROUTINE : {priority_counts.get('routine', 0)}\n\n")

            f.write("--- CATEGORY DISTRIBUTION ---\n")
            f.write(f"  Injury     : {category_counts.get('injury', 0)}\n")
            f.write(f"  Fever/Cold : {category_counts.get('fever_cold', 0)}\n")
            f.write(f"  Stomach    : {category_counts.get('stomach', 0)}\n")
            f.write(f"  Pain       : {category_counts.get('pain', 0)}\n")
            f.write(f"  Allergy    : {category_counts.get('allergy', 0)}\n")
            f.write(f"  Other      : {category_counts.get('other', 0)}\n\n")

            f.write("--- HOURLY ARRIVAL COUNTS ---\n")
            for h_label in sorted(hour_counts.keys()):
                f.write(f"  {h_label} : {hour_counts[h_label]}\n")

            f.write(f"\nTotal Red-Flag Cases Detected: {red_flag_count}\n")
            f.write("=====================================================\n")
    except Exception as e:
        print(f"[ERROR] Failed to write '{summary_file}': {e}")


# ==============================================================================
# MAIN WORKFLOW
# ==============================================================================

def main():
    print("========================================")
    print("          CLINIC VISIT SORTER           ")
    print("========================================")
    print()

    # Step 1: Check environment & load system prompt
    api_key = os.environ.get("LLM_API_KEY")
    if not api_key:
        print("[NOTICE] No 'LLM_API_KEY' found in environment.")
        print("         Running with safe deterministic fallback engine.")
        print("         (Unknown priority defaulted to 'today', red flags active).\n")
    else:
        print("[NOTICE] 'LLM_API_KEY' detected. Online LLM sorting active.\n")

    system_prompt = ""
    prompt_file = "system_prompt.txt"
    if os.path.exists(prompt_file):
        with open(prompt_file, mode="r", encoding="utf-8") as pf:
            system_prompt = pf.read()
    else:
        print(f"[WARNING] '{prompt_file}' not found. Using internal system instructions.")

    # Step 2: Load student records
    print("Loading student records...")
    visits = load_visits("visits.csv")
    total_loaded = len(visits)
    print(f"Total students loaded: {total_loaded}\n")

    if total_loaded == 0:
        print("[ERROR] No visit records to process. Exiting.")
        sys.exit(1)

    # Step 3: Classify each record
    print("Classifying student notes...")
    print("Checking red flags...")
    print("Assigning priorities...")

    processed_queue = []
    for visit in visits:
        res = classify(visit["note"], system_prompt, api_key)
        processed_queue.append({
            "id": visit["id"],
            "time": visit["time"],
            "note": visit["note"],
            "category": res["category"],
            "priority": res["priority"],
            "summary": res["summary"],
            "is_red_flag": res["is_red_flag"]
        })

    # Step 4: Sort queue by priority, then by arrival time
    print("Sorting nurse queue...\n")
    sorted_queue = sorted(
        processed_queue,
        key=lambda item: (PRIORITY_ORDER.get(item["priority"], 99), item["time"])
    )

    # Step 5: Compute statistics for terminal display
    total_count = len(sorted_queue)
    c_see_now = sum(1 for s in sorted_queue if s["priority"] == "see_now")
    c_today = sum(1 for s in sorted_queue if s["priority"] == "today")
    c_routine = sum(1 for s in sorted_queue if s["priority"] == "routine")
    c_red_flags = sum(1 for s in sorted_queue if s["is_red_flag"])

    cat_counts = {cat: 0 for cat in VALID_CATEGORIES}
    for s in sorted_queue:
        cat_counts[s["category"]] = cat_counts.get(s["category"], 0) + 1

    # Step 6: Display Final Summary
    print("--------------- FINAL SUMMARY ---------------")
    print(f"Total Students: {total_count}\n")
    print(f"SEE NOW: {c_see_now}")
    print(f"TODAY:   {c_today}")
    print(f"ROUTINE: {c_routine}\n")
    print("Category-wise Statistics:")
    print(f"- Injury:     {cat_counts['injury']}")
    print(f"- Fever/Cold: {cat_counts['fever_cold']}")
    print(f"- Stomach:    {cat_counts['stomach']}")
    print(f"- Pain:       {cat_counts['pain']}")
    print(f"- Allergy:    {cat_counts['allergy']}")
    print(f"- Other:      {cat_counts['other']}\n")
    print(f"Red-Flag Cases: {c_red_flags}\n")

    # Step 7: Display Sorted Nurse Queue
    print("--------------- NURSE QUEUE -----------------")
    header = f"{'ID':<6} | {'TIME':<6} | {'PRIORITY':<9} | {'RED-FLAG':<9} | {'CATEGORY':<11} | {'SUMMARY'}"
    print(header)
    print("-" * len(header) + "-" * 25)

    for s in sorted_queue:
        rf_text = "YES" if s["is_red_flag"] else "NO"
        print(f"{s['id']:<6} | {s['time']:<6} | {s['priority']:<9} | {rf_text:<9} | {s['category']:<11} | {s['summary']}")

    print()

    # Step 8: Write Output Files
    write_reports(sorted_queue, "nurse_queue.csv", "summary.txt")

    print("Reports generated successfully:")
    print("1. nurse_queue.csv")
    print("2. summary.txt\n")

    print("========================================")
    print("          PROCESS COMPLETED             ")
    print("========================================")


if __name__ == "__main__":
    main()
