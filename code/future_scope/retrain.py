import os
import sys

# Ensure the parent directory (code/) is on the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.sequence import pad_sequences
from data_pipeline import DataPreprocessor
import pandas as pd
import numpy as np
import tensorflow as tf
import pickle
import shutil
from datetime import datetime

# --- CONFIGURATION (Phase 4 Retraining) ---
MODEL_PATH = "bilstm_model.h5"
TOKENIZER_PATH = "tokenizer.pickle"
FEEDBACK_CSV = "user_feedback_log.csv"
ARCHIVE_DIR = "feedback_archive"
MAX_LENGTH = 50
LEARNING_RATE = 1e-5
EPOCHS = 3
BATCH_SIZE = 4


def run_retraining():
    """
    [Phase 4 Continuous Learning] Fine-tunes the Bi-LSTM model on human-verified feedback.
    """
    if not os.path.exists(FEEDBACK_CSV):
        print(f"Error: {FEEDBACK_CSV} not found. No new data to retrain.")
        return

    # 1. Load Feedback Data
    df = pd.read_csv(FEEDBACK_CSV)
    if len(df) < 1:
        print("Error: FEEDBACK_CSV is empty.")
        return

    print(f"Found {len(df)} new feedback samples. Starting fine-tuning...")

    # 2. Load Production Artifacts
    if not os.path.exists(MODEL_PATH) or not os.path.exists(TOKENIZER_PATH):
        print("Error: Production artifacts (model/tokenizer) missing. Cannot retrain.")
        return

    model = tf.keras.models.load_model(MODEL_PATH)
    with open(TOKENIZER_PATH, 'rb') as handle:
        tokenizer = pickle.load(handle)

    preprocessor = DataPreprocessor(stem=False)

    # 3. Preprocess New Data
    print("Preprocessing new feedback samples...")
    df['text'] = df['text'].apply(lambda x: preprocessor.preprocess(x))

    # Tokenize and pad
    sequences = tokenizer.texts_to_sequences(df['text'])
    x_new = pad_sequences(sequences, maxlen=MAX_LENGTH, padding='post')
    y_new = np.array(df['Label'])

    # 4. Fine-Tune Model
    # Using a very low learning rate to prevent "catastrophic forgetting"
    print(
        f"Fine-tuning Bi-LSTM for {EPOCHS} epochs with lr={LEARNING_RATE}...")
    model.compile(optimizer=Adam(learning_rate=LEARNING_RATE),
                  loss='binary_crossentropy',
                  metrics=['accuracy'])

    model.fit(x_new, y_new, epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=1)

    # 5. Save and Archive
    print(f"Saving updated model to {MODEL_PATH}...")
    model.save(MODEL_PATH)

    # Archive the feedback data
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = os.path.join(ARCHIVE_DIR, f"feedback_{timestamp}.csv")
    shutil.move(FEEDBACK_CSV, archive_path)

    print(f"Success: Model updated. Feedback data archived to {archive_path}")


if __name__ == "__main__":
    run_retraining()
