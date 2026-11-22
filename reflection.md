# PROJECT REFLECTION: CLINIC VISIT SORTER
**Course:** CIT AI-Native Engineering Programme · Semester 1 · Assessment 5  
**Author:** First-Year Decision and Computing Science Student  
**Word Count:** ~400 words  

---

Developing the **Clinic Visit Sorter** has been a transformative experience in understanding what AI-native software engineering truly means. Prior to this project, I viewed artificial intelligence primarily as an autonomous problem-solver capable of replacing manual software routines. However, working within the high-stakes healthcare domain taught me that responsible AI engineering is not about delegating authority to a language model; it is about constructing a resilient, defensive software architecture around probabilistic systems.

The most critical insight I gained involves the concept of asymmetric risk in clinical triage. In computer science, we often treat false positives and false negatives with balanced mathematical metrics such as F1-scores. In a campus health clinic, however, an under-triage error—classifying a student with acute chest pain as routine—can lead to permanent disability or death. In contrast, an over-triage error merely causes a nurse to briefly assess a stable student before reprioritizing them. This taught me why deterministic code invariants are essential: Python must govern the LLM, not the other way around. By enforcing that priority can only be elevated and never lowered, we guarantee patient safety regardless of prompt variability or adversarial attempts to downplay symptoms.

Another major learning came from handling regional language nuances. In moments of acute physical distress, students express their symptoms naturally in their mother tongue—Tamil or Tanglish. A model or rule system trained purely on formal English medical terminology fails real patients. Building regex interceptors for phrases like *"nenju vali"* (chest pain) and *"moochu vida mudiyala"* (cannot breathe) demonstrated how localized context must be embedded into software specifications from day one.

Finally, navigating API failure modes reinforced the vital role of the human checkpoint. When designing the fallback mechanism, the principle that "unknown is never routine" forced me to think through operational continuity. If the network disconnects, the system does not crash; it safely defaults to `today`, flags red flags deterministically, and presents the entire queue to the registered nurse. The nurse remains the ultimate decision-maker, while the code acts as an organized assistant. This project has solidified my technical foundations in Python modular programming, JSON schema validation, and defensive system design, preparing me for real-world software engineering challenges.
