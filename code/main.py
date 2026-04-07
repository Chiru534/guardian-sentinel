import pandas as pd
import numpy as np
import os
from sklearn.model_selection import train_test_split
from data_pipeline import DataPreprocessor, TextTokenizer
from models import ANNModel, RNNModel, LSTMModel, BiLSTMModel, load_glove_embeddings
from tensorflow.keras.callbacks import EarlyStopping
import pickle

class SpamDetectionSystem:
    """
    Controller class to manage the full pipeline: data cleaning, tokenization, training, and evaluation.
    """
    def __init__(self, vocab_size=10000, max_len=50):
        self.vocab_size = vocab_size
        self.max_len = max_len
        self.preprocessor = DataPreprocessor(stem=False)
        self.tokenizer = TextTokenizer(vocab_size=vocab_size)
        self.data = None
        self.x_train = None
        self.x_test = None
        self.y_train = None
        self.y_test = None

    def load_data(self, data1_path='spam_ham_dataset.csv', data2_path='BusinessEmail_train.csv', data3_path='BusinessEmail_test.csv'):
        """
        Loads and integrates multiple datasets into a single dataframe.
        """
        # Load first dataset
        df1 = pd.read_csv(data1_path)
        df1 = df1.drop(['Unnamed: 0', 'label'], axis=1)
        df1 = df1.rename(columns={"label_num": "Label"})

        # Load second dataset
        # The notebook used cp1252 for BusinessEmail_train.csv
        df2 = pd.read_csv(data2_path, encoding='cp1252')
        df2 = df2.drop(["S. No."], axis=1)
        df2 = df2.rename(columns={"Message_body": "text"})
        df2["Label"] = [1 if i == "Spam" else 0 for i in df2["Label"]]

        # Load third dataset (test)
        df3 = pd.read_csv(data3_path, encoding='cp1252')
        df3 = df3.drop(["S. No."], axis=1)
        df3 = df3.rename(columns={"Message_body": "text"})
        df3["Label"] = [1 if i == "Spam" else 0 for i in df3["Label"]]

        # Concatenate all
        self.data = pd.concat([df1, df2, df3])
        print(f"Total data size after merge: {len(self.data)}")

        # Clean text
        print("Preprocessing text...")
        self.data['text'] = self.data['text'].apply(lambda x: self.preprocessor.preprocess(x))

        # Split
        x = self.data['text']
        y = self.data['Label']
        self.x_train, self.x_test, self.y_train, self.y_test = train_test_split(x, y, test_size=0.2, random_state=7)
        
        # Tokenize and pad
        print("Tokenizing and padding sequences...")
        self.tokenizer.fit_on_texts(self.x_train)
        self.x_train = self.tokenizer.pad_sequences(self.tokenizer.texts_to_sequences(self.x_train), max_len=self.max_len)
        self.x_test = self.tokenizer.pad_sequences(self.tokenizer.texts_to_sequences(self.x_test), max_len=self.max_len)

    def train_model(self, model_type='LSTM', epochs=30, batch_size=32):
        """
        Instantiates and trains a specific model architecture.
        """
        if model_type == 'ANN':
            model = ANNModel(input_dim=self.max_len)
        elif model_type == 'RNN':
            model = RNNModel(input_dim=self.max_len)
        elif model_type == 'LSTM':
            model = LSTMModel(vocab_size=self.vocab_size, input_len=self.max_len)
        elif model_type == 'BiLSTM':
            # [GloVe Integration] Loading pre-trained embeddings for BiLSTM
            embedding_dim = 100
            glove_path = 'glove.6B.100d.txt'
            if os.path.exists(glove_path):
                print(f"Loading GloVe embeddings from {glove_path}...")
                embedding_matrix = load_glove_embeddings(
                    glove_path, 
                    self.tokenizer.tokenizer.word_index, 
                    self.vocab_size, 
                    embedding_dim
                )
            else:
                print("Warning: GloVe file not found. Initializing BiLSTM with random embeddings.")
                embedding_matrix = None
                
            model = BiLSTMModel(
                vocab_size=self.vocab_size, 
                embedding_dim=embedding_dim, 
                input_len=self.max_len, 
                embedding_matrix=embedding_matrix
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        model.compile()
        early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)
        
        print(f"Starting training for {model_type}...")
        history = model.fit(self.x_train, self.y_train, 
                            validation_data=(self.x_test, self.y_test), 
                            epochs=epochs, batch_size=batch_size, 
                            callbacks=[early_stop])
        
        return model, history

    def evaluate_model(self, model):
        """
        Runs evaluation on test data.
        """
        loss, accuracy = model.evaluate(self.x_test, self.y_test)
        print(f"Test Loss: {loss:.4f}")
        print(f"Test Accuracy: {accuracy*100:.2f}%")
        return accuracy

if __name__ == "__main__":
    system = SpamDetectionSystem()
    
    # Files must exist in the directory
    try:
        system.load_data()
        
        # Train and evaluate ANN
        ann_model, _ = system.train_model(model_type='ANN', epochs=1, batch_size=64)
        ann_model.model.save('ann_model.h5')

        # Train and evaluate RNN
        rnn_model, _ = system.train_model(model_type='RNN', epochs=1, batch_size=64)
        rnn_model.model.save('rnn_model.h5')

        # Train and evaluate BiLSTM
        bilstm_model, _ = system.train_model(model_type='BiLSTM', epochs=1, batch_size=64)
        bilstm_model.model.save('bilstm_model.h5')

        # [Phase 3 Deployment] Serialization of artifacts
        with open('tokenizer.pickle', 'wb') as handle:
            pickle.dump(system.tokenizer.tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print("Success: ANN, RNN, Bi-LSTM, and tokenizer saved.")
    except FileNotFoundError as e:
        print(f"Error: {e}. Please ensure data files are in the CWD.")
