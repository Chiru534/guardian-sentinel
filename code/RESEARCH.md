# Systematic Literature Review (SLR) - Chapter 3 System Analysis

## 3.1 Overview of Research Methodology
This research follows a rigorous Systematic Literature Review (SLR) to ensure that the detection framework is informed by state-of-the-art developments in NLP and Deep Learning for cybersecurity. 

### SLR Flow and Selection Process
1. **Initial Identification**: 950 academic articles were initially identified through digital libraries (IEEE Xplore, ScienceDirect, ACM Digital Library, and Google Scholar) using keywords: "Phishing Detection", "BEC Attacks", "Bi-LSTM in Cybersecurity", and "Natural Language Processing".
2. **First Filtering Phase**: Articles published outside the search window of **2012-2022** were excluded to focus on modern deep learning techniques (ANN, RNN, LSTM architectures).
3. **Second Filtering Phase**: Papers focusing exclusively on metadata (header-based) without text-body analysis were removed.
4. **Final Selection**: 38 articles were finalized for deep qualitative and quantitative synthesis, forming the bedrock of the 10-Step BEC Lifecycle detection framework.

---

## 3.2 The 10-Step Business Email Compromise (BEC) Attack Lifecycle
Based on the synthesized research, our heuristic engine (`data_pipeline.py`) targets the following 10 critical stages of a BEC attack used by sophisticated threat actors:

1. **Target Identification**: Identifying key personnel (CEO, CFO, HR) within an organization.
2. **Persona Building**: Crafting a digital identity that mimicks high-level executives or trusted partners.
3. **Reconnaissance**: Gathering organizational intel (active projects, travel schedules) to increase message credibility.
4. **Initial Contact**: Sending low-stakes emails to bypass spam filters and check recipient engagement.
5. **Grooming/Trust Building**: Establishing a rapport through repeated, non-malicious communication.
6. **Victim Isolation**: Instructing the victim to keep the transaction confidential or use private communication channels.
7. **Urgency Engagement**: Using psychological pressure (e.g., "Urgent action required") to override standard verification protocols.
8. **Call to Action (The Ask)**: The pivotal moment where the attacker requests sensitive data or a financial transaction.
9. **Bank Manipulation**: Providing specific, often overseas, bank account details for a wire transfer.
10. **Evasion and Cleanup**: Instructions to delete the original email thread or ignore follow-up queries to delay detection.

---

## 3.3 Comparative Architecture Justification
| Model Architecture | Academic Justification |
| :--- | :--- |
| **ANN** | Serves as the statistical baseline for word-frequency-based classification (Bag-of-Words). |
| **RNN** | Explores basic temporal dependencies, though constrained by the vanishing gradient problem. |
| **LSTM** | Addresses long-term dependencies in email bodies using gated memory units. |
| **Bi-LSTM** | **Optimal Academic Choice**: Captures semantic context by processing tokens from both past and future states simultaneously, providing superior accuracy for long-form phishing attempts. |
