# COST AND LATENCY NOTE: CLINIC VISIT SORTER
**Course:** CIT AI-Native Engineering Programme · Semester 1 · Assessment 5  
**Author:** First-Year Decision and Computing Science Student  

---

### 1. Scope & Daily Operating Assumptions
This note provides an engineering estimate of API call volume, latency characteristics, and operational costs for deploying the **Clinic Visit Sorter** at the campus health centre.

#### Baseline Assumptions:
- **Daily Student Volume:** 30 students per morning triage window (09:00 - 12:00).
- **Target Model:** OpenAI `gpt-3.5-turbo` (or Google Gemini 1.5 Flash / compatible tier).
- **Pricing Basis (Standard LLM inference tier):**
  - Input tokens: \$0.50 per 1,000,000 tokens (\$0.0000005 per token).
  - Output tokens: \$1.50 per 1,000,000 tokens (\$0.0000015 per token).
- **Prompt Token Length:**
  - System prompt: ~350 tokens (rules, categories, 3 exemplars).
  - User note: ~25 tokens.
  - Total input per call: ~375 tokens.
- **Completion Token Length:**
  - JSON output: ~35 tokens (`category`, `priority`, `summary`).
- **Network Retry Rate:** 10% expected transient network retry or format invalidation.

---

### 2. API Call Volume Estimate

| Metric | Calculation | Daily Quantity |
| :--- | :--- | :--- |
| **Nominal Student Records** | 30 students | 30 calls |
| **Expected Retries (10% rate)** | 30 × 0.10 | 3 calls |
| **Total Estimated API Calls / Day** | 30 + 3 | **33 calls** |

If the network connection or API service is entirely down, the application makes 2 attempts per record before invoking the zero-cost local fallback engine.

---

### 3. Latency Estimates

- **Per-Call Response Time:** 
  - Median Latency ($P_{50}$): ~0.65 seconds.
  - 95th Percentile Latency ($P_{95}$): ~1.20 seconds.
- **Batch Processing Time (Sequential 30 Records):**
  - Nominal sequential run: 30 calls × 0.8s avg = **~24.0 seconds**.
  - With retries: ~26.4 seconds.
- **Local Fallback Mode:**
  - Deterministic Python regex and dictionary lookups execute in **< 0.05 seconds** for all 30 records combined.

*Engineering Recommendation:* In a production multi-worker deployment, concurrent asynchronous requests (`asyncio` / thread pool) can reduce total processing time to under 2.5 seconds. For this first-year console implementation, sequential processing is adopted for simplicity and transparent console logging.

---

### 4. Daily & Monthly Cost Estimation

#### Per-Call Cost:
- Input Cost: $375 \text{ tokens} \times \$0.0000005 = \$0.0001875$
- Output Cost: $35 \text{ tokens} \times \$0.0000015 = \$0.0000525$
- **Total Cost per API Call:** **\$0.000240** (approx. 0.024 cents)

#### Aggregated Operating Cost:
- **Daily Cost (33 calls):** $33 \times \$0.000240 \approx \mathbf{\$0.00792}$ (under 1 US cent per day)
- **Monthly Cost (22 college working days):** $22 \times \$0.00792 \approx \mathbf{\$0.174}$ (~17 US cents / month, or approx. ₹15 INR)

---

### 5. Conclusion & Viability
The operational cost of running this LLM-based triage sorter is negligible (< ₹20/month). The latency (~25 seconds for a full morning cohort of 30 students) fits comfortably within clinical workflow, as the batch is processed while the nurse prepares the examination station.
