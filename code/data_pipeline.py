import re
import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

# Ensure necessary NLTK data is downloaded
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class DataPreprocessor:
    """
    Handles cleaning and text processing for raw email data.
    """

    def __init__(self, stem=False):
        self.stop_words = set(stopwords.words('english'))
        self.stemmer = SnowballStemmer('english')
        self.text_cleaning_re = r"@\S+|https?:\S+|http?:\S+|[^A-Za-z0-9]:\S+|subject:\S+|nbsp"
        self.stem = stem

    def clean_text(self, text):
        """
        Removes noisy patterns and converts to lowercase.
        """
        text = re.sub(self.text_cleaning_re, ' ', str(text).lower()).strip()
        return text

    def remove_stopwords(self, text_list):
        """
        Filters out common English stopwords.
        """
        return [token for token in text_list if token not in self.stop_words]

    def stem_words(self, text_list):
        """
        Reduces words to their root form.
        """
        return [self.stemmer.stem(token) for token in text_list]

    def preprocess(self, text):
        """
        Full preprocessing pipeline: cleaning, tokenizing, filtering, and optional stemming.
        """
        text = self.clean_text(text)
        tokens = text.split()
        tokens = self.remove_stopwords(tokens)
        if self.stem:
            tokens = self.stem_words(tokens)
        return " ".join(tokens)

    def engineer_bec_features(self, text):
        """
        [BEC Logic] Engineers heuristic features to detect the 10-step BEC attack lifecycle.
        Identifies specific stages like Persona Building, Victim Isolation, and Bank Manipulation.
        """
        text = str(text).lower()
        bec_signals = {
            "persona_impersonation": r"\b(ceo|cfo|cto|founder|president|director|executive|lawyer|attorney|partner)\b",
            "victim_isolation": r"(do not discuss|keep this confidential|private enquiry|strictly confidential|don't tell anyone)",
            "urgency_engagement": r"\b(urgent|immediate|asap|attention|action required|quick task)\b",
            "bank_manipulation": r"\b(wire transfer|swift code|bic\b|routing number|bank account|account number|fund transfer)\b",
            "evasion_cleanup": r"(delete this email|do not reply to this|reply to my personal)",
            "credential_phishing": r"(password|login|verify account|sign in|access your account)"
        }

        results = {}
        for stage, pattern in bec_signals.items():
            results[stage] = 1 if re.search(pattern, text) else 0

        return results


class TextTokenizer:
    """
    Manages numerical conversion of text sequences using Keras Tokenizer.
    """

    def __init__(self, vocab_size=10000, oov_token="<OOV>"):
        self.tokenizer = Tokenizer(num_words=vocab_size, oov_token=oov_token)
        self.vocab_size = vocab_size

    def fit_on_texts(self, texts):
        """
        Learns the vocabulary from a set of texts.
        """
        self.tokenizer.fit_on_texts(texts)

    def texts_to_sequences(self, texts):
        """
        Converts text lists into integer sequences.
        """
        return self.tokenizer.texts_to_sequences(texts)

    def pad_sequences(self, sequences, max_len=50, padding='post'):
        """
        Ensures all sequences have a uniform length.
        """
        return pad_sequences(sequences, maxlen=max_len, padding=padding)
