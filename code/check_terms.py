import json
import re

terms = ["ANN", "RNN", "LSTM", "Bi-LSTM", "Word2Vec", "GloVe", "Enron", "SpamAssassin", "Kafka", "ModelBase"]
found_terms = {term: False for term in terms}

try:
    with open('phishing-e-mail-detection (1).ipynb', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    for cell in data.get('cells', []):
        source = "".join(cell.get('source', []))
        for term in terms:
            if re.search(term, source, re.IGNORECASE):
                found_terms[term] = True
                
    for cell in data.get('cells', []):
        if cell.get('cell_type') == 'markdown':
            source = "".join(cell.get('source', []))
            for term in terms:
                if re.search(term, source, re.IGNORECASE):
                    found_terms[term] = True
                    
    print("Term search results in source cells:")
    for term, found in found_terms.items():
        print(f"{term}: {found}")
except Exception as e:
    print(f"Error: {e}")
