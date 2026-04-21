import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Dropout, SimpleRNN, LSTM, Embedding, Reshape, Bidirectional
from model_base import ModelBase


class ANNModel(ModelBase):
    """
    Artificial Neural Network (Baseline) implementation.
    """

    def __init__(self, input_dim=50):
        self.input_dim = input_dim
        self.model = self.build_model()

    def build_model(self):
        model = Sequential()
        model.add(Dense(16, activation='relu', input_dim=self.input_dim))
        model.add(Dropout(0.2))  # Using 0.2 as per constraints
        model.add(Dense(1, activation='sigmoid'))
        return model

    def compile(self, optimizer='adam', loss='binary_crossentropy', metrics=['accuracy']):
        self.model.compile(optimizer=optimizer, loss=loss, metrics=metrics)

    def fit(self, x_train, y_train, validation_data=None, epochs=30, batch_size=32, callbacks=None):
        return self.model.fit(x_train, y_train, validation_data=validation_data,
                              epochs=epochs, batch_size=batch_size,
                              callbacks=callbacks, verbose=1)

    def predict(self, x):
        return (self.model.predict(x) > 0.5).astype("int32")

    def evaluate(self, x, y):
        return self.model.evaluate(x, y, verbose=0)


class RNNModel(ModelBase):
    """
    Recurrent Neural Network implementation.
    """

    def __init__(self, input_dim=50):
        self.input_dim = input_dim
        self.model = self.build_model()

    def build_model(self):
        model = Sequential()
        model.add(Reshape((1, self.input_dim), input_shape=(self.input_dim,)))
        model.add(SimpleRNN(128, activation='relu', return_sequences=True))
        model.add(SimpleRNN(64, activation='relu', return_sequences=False))
        model.add(Dense(1, activation='sigmoid'))
        return model

    def compile(self, optimizer='adam', loss='binary_crossentropy', metrics=['accuracy']):
        self.model.compile(optimizer=optimizer, loss=loss, metrics=metrics)

    def fit(self, x_train, y_train, validation_data=None, epochs=30, batch_size=32, callbacks=None):
        return self.model.fit(x_train, y_train, validation_data=validation_data,
                              epochs=epochs, batch_size=batch_size,
                              callbacks=callbacks, verbose=1)

    def predict(self, x):
        return (self.model.predict(x) > 0.5).astype("int32")

    def evaluate(self, x, y):
        return self.model.evaluate(x, y, verbose=0)


class LSTMModel(ModelBase):
    """
    Long Short-Term Memory Network implementation.
    """

    def __init__(self, vocab_size=10000, embedding_dim=16, input_len=50):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.input_len = input_len
        self.model = self.build_model()

    def build_model(self):
        # Hyperparameters based on notebook's LSTM implementation
        # VOCAB_SIZE=10000, EMBEDDING_DIM=16, N_LSTM=200, DROP_LSTM=0.2, N_DENSE=24, DROP_VALUE=0.2
        model = Sequential()
        model.add(Embedding(self.vocab_size, self.embedding_dim,
                  input_length=self.input_len))
        model.add(LSTM(200, dropout=0.2, return_sequences=True))
        model.add(LSTM(200, dropout=0.2, return_sequences=False))
        model.add(Dense(24, activation='relu'))
        model.add(Dropout(0.2))
        model.add(Dense(1, activation='sigmoid'))
        return model

    def compile(self, optimizer='adam', loss='binary_crossentropy', metrics=['accuracy']):
        self.model.compile(optimizer=optimizer, loss=loss, metrics=metrics)

    def fit(self, x_train, y_train, validation_data=None, epochs=30, batch_size=32, callbacks=None):
        return self.model.fit(x_train, y_train, validation_data=validation_data,
                              epochs=epochs, batch_size=batch_size,
                              callbacks=callbacks, verbose=1)

    def predict(self, x):
        return (self.model.predict(x) > 0.5).astype("int32")

    def evaluate(self, x, y):
        return self.model.evaluate(x, y, verbose=0)


class BiLSTMModel(ModelBase):
    """
    Bidirectional Long Short-Term Memory Network implementation.
    """

    def __init__(self, vocab_size=10000, embedding_dim=100, input_len=50, embedding_matrix=None):
        self.vocab_size = vocab_size
        self.embedding_dim = embedding_dim
        self.input_len = input_len
        self.embedding_matrix = embedding_matrix
        self.model = self.build_model()

    def build_model(self):
        """
        [GloVe Integration] Constructs the Bi-LSTM using pre-trained weights if available.
        """
        model = Sequential()
        if self.embedding_matrix is not None:
            # Use pre-trained GloVe weights
            model.add(Embedding(self.vocab_size, self.embedding_dim,
                                weights=[self.embedding_matrix],
                                input_length=self.input_len,
                                trainable=False))
        else:
            model.add(Embedding(self.vocab_size, self.embedding_dim,
                      input_length=self.input_len))

        model.add(Bidirectional(LSTM(200, dropout=0.2, return_sequences=True)))
        model.add(Bidirectional(LSTM(200, dropout=0.2, return_sequences=False)))
        model.add(Dense(24, activation='relu'))
        model.add(Dropout(0.2))
        model.add(Dense(1, activation='sigmoid'))
        return model

    def compile(self, optimizer='adam', loss='binary_crossentropy', metrics=['accuracy']):
        self.model.compile(optimizer=optimizer, loss=loss, metrics=metrics)

    def fit(self, x_train, y_train, validation_data=None, epochs=30, batch_size=32, callbacks=None):
        return self.model.fit(x_train, y_train, validation_data=validation_data,
                              epochs=epochs, batch_size=batch_size,
                              callbacks=callbacks, verbose=1)

    def predict(self, x):
        return (self.model.predict(x) > 0.5).astype("int32")

    def evaluate(self, x, y):
        return self.model.evaluate(x, y, verbose=0)


def load_glove_embeddings(file_path, word_index, vocab_size, embedding_dim=100):
    """
    [GloVe Integration] Utility to map GloVe vectors to our tokenizer's word index.
    """
    embeddings_index = {}
    with open(file_path, 'r', encoding='utf8') as f:
        for line in f:
            values = line.split()
            word = values[0]
            coefs = np.asarray(values[1:], dtype='float32')
            embeddings_index[word] = coefs

    embedding_matrix = np.zeros((vocab_size, embedding_dim))
    for word, i in word_index.items():
        if i < vocab_size:
            embedding_vector = embeddings_index.get(word)
            if embedding_vector is not None:
                embedding_matrix[i] = embedding_vector
    return embedding_matrix
