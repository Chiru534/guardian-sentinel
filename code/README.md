# Hybrid Deep Learning Framework for Phishing & BEC Detection

## Abstract
This project presents an end-to-end framework for detecting sophisticated phishing and Business Email Compromise (BEC) attacks. By leveraging a hybrid architecture that integrates Bidirectional Long Short-Term Memory (Bi-LSTM) networks with high-precision heuristic feature engineering, this study achieves a **98.2% detection accuracy**. The system addresses the 10-step BEC attack lifecycle, providing a robust defense against executive impersonation and wire-transfer fraud.

---

## 🏗️ Repository Architecture (Academic Alignment)

The repository is structured to map directly to our **Research Chapters (Ch 1-6)**. 

### 1. Preprocessing Layer (Chapter 4.1)
- **`data_pipeline.py`**: Encapsulates text cleaning, tokenization, padding, and heuristic BEC feature engineering.
- **`tokenizer.pickle`**: Serialized Keras Tokenizer used for sequence mapping.

### 2. Modeling Layer (Chapter 4.2)
- **`models.py`**: Implementation of ANN, RNN, LSTM, and Bi-LSTM architectures.
- **`model_base.py`**: Abstract base classes for standardized model compilation and evaluation.
- **`bilstm_model.h5`**: Production-ready serialized Bi-LSTM model.

### 3. Deployment Layer (Chapter 4.5)
- **`api.py`**: FastAPI-based REST server for real-time inference using the hybrid engine.

### 4. Results & Evaluation (Chapter 5)
- **`evaluate.py`**: Master evaluation script that generates Accuracy/Loss plots and confusion matrices across the test partition.
- **`RESEARCH.md`**: Detailed Systematic Literature Review (SLR) documenting the filtering of 950 initial articles down to 38 for the study.

### 5. Future Scope (Chapter 7)
The following advanced features are moved to the `/future_scope` directory for separation of concerns between core research and future deployment extensions:
- **`future_scope/frontend.py`**: Premium Streamlit UI for end-user interaction.
- **`future_scope/retrain.py`**: Continuous learning pipeline for model adaptation.

---

## ⚡ Quick Start (Evaluation Flow)

To reproduce the study results for **Chapter 5**, ensure you have installed the required dependencies from `requirements.txt` and execute the master evaluation script:

```bash
python evaluate.py
```

This will:
1. Load the stored models (`ann_model.h5`, `rnn_model.h5`, `bilstm_model.h5`).
2. Generate performance curves for the Bi-LSTM model (`performance_curves.png`).
3. Output classification reports and a heatmap confusion matrix (`confusion_matrix.png`).

---

## 📚 Academic References
All research criteria, data distributions, and architectural justifications are documented in **RESEARCH.md** and **project_context.md**.
