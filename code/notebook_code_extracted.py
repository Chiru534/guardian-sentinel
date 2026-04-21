import numpy as np
import pandas as pd

import os
for dirname, _, filenames in os.walk('/kaggle/input'):
    for filename in filenames:
        print(os.path.join(dirname, filename))

# --- NEW CELL ---

import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
import re

import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# --- NEW CELL ---

data1 = pd.read_csv('/content/spam_ham_dataset.csv')
data2 = pd.read_csv("/content/BusinessEmail_train.csv", encoding='cp1252')

# --- NEW CELL ---

data1.head()

# --- NEW CELL ---

data1 = data1.drop(['Unnamed: 0', 'label'], axis=1)
data1 = data1.rename(columns = {"label_num" : "Label"})
data1.info()

# --- NEW CELL ---

sns.countplot(x="Label", data = data1)

# --- NEW CELL ---

data2.head()

# --- NEW CELL ---

data2 = data2.drop(["S. No."], axis = 1)
data2 = data2.rename(columns = {"Message_body" : "text"})
data2["Label"] = [1 if i == "Spam" else 0 for i in data2["Label"]]
data2.info()

# --- NEW CELL ---

sns.countplot(x = "Label", data = data2)

# --- NEW CELL ---

frames = [data1, data2]
data = pd.concat(frames)
data

# --- NEW CELL ---

sns.countplot(x="Label", data = data)

# --- NEW CELL ---

from wordcloud import WordCloud

plt.figure(figsize = (20,20))
wc = WordCloud(max_words = 2000 , width = 1600 , height = 800).generate(" ".join(data[data.Label == 1].text))
plt.imshow(wc , interpolation = 'bilinear')
plt.title("Spam Word Cloud")

# --- NEW CELL ---

plt.figure(figsize = (20,20))
wc = WordCloud(max_words = 2000 , width = 1600 , height = 800).generate(" ".join(data[data.Label == 0].text))
plt.imshow(wc , interpolation = 'bilinear')
plt.title("Ham Word Cloud")

# --- NEW CELL ---

# stop_words = stopwords.words('english')
# stemmer = SnowballStemmer('english')

# text_cleaning_re = "@\S+|https?:\S+|http?:\S+|[^A-Za-z0-9]:\S+|subject:\S+|nbsp"

import nltk
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer
# Download the stopwords resource if you haven't already
nltk.download('stopwords')

# Access the stopwords using the stopwords module
stop_words = set(stopwords.words('english'))  # Use set for efficient lookup
stemmer = SnowballStemmer('english')

text_cleaning_re = "@\S+|https?:\S+|http?:\S+|[^A-Za-z0-9]:\S+|subject:\S+|nbsp"

# --- NEW CELL ---

def preprocess(text, stem=False):
    text = re.sub(text_cleaning_re, ' ', str(text).lower()).strip()
    tokens = []
    for token in text.split():
        if token not in stop_words:
            if stem:
                tokens.append(stemmer.stem(token))
            else:
                tokens.append(token)
    return " ".join(tokens)

data.text = data.text.apply(lambda x: preprocess(x))
data.head()

# --- NEW CELL ---

x = data['text']
y = data['Label']
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2,
                                         random_state=7)
print("Train Data size:", len(x_train))
print("Test Data size", len(x_test))

# --- NEW CELL ---

# !pip install tensorflow-text

# --- NEW CELL ---

# from keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.text import Tokenizer # Import Tokenizer from tensorflow.keras.preprocessing.text

tokenizer = Tokenizer()
tokenizer.fit_on_texts(x_train)

word_index = tokenizer.word_index
vocab_size = len(tokenizer.word_index) + 1000
print("Vocabulary Size :", vocab_size)

# --- NEW CELL ---

from keras.preprocessing.sequence import pad_sequences

x_train = pad_sequences(tokenizer.texts_to_sequences(x_train),
                        maxlen = 50)
x_test = pad_sequences(tokenizer.texts_to_sequences(x_test),
                       maxlen = 50)

print("Training X Shape:",x_train.shape)
print("Testing X Shape:",x_test.shape)

# --- NEW CELL ---

import keras
from keras.models import Sequential
from keras.layers import Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping

# --- NEW CELL ---

ann = Sequential()
ann.add(Dense(16, activation='relu', input_dim=50))
# Adding dropout to prevent overfitting
ann.add(Dropout(0.1))
ann.add(Dense(1, activation='sigmoid'))

# --- NEW CELL ---

ann.summary()

# --- NEW CELL ---

ann.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# --- NEW CELL ---

history = ann.fit(x_train, y_train,
                  batch_size=10,
                  epochs=100,
                  verbose=2,
                  validation_data=(x_test, y_test))

# --- NEW CELL ---

metrics = pd.DataFrame(history.history)
# Rename column
metrics.rename(columns = {'loss': 'Training_Loss', 'accuracy': 'Training_Accuracy',
                         'val_loss': 'Validation_Loss', 'val_accuracy': 'Validation_Accuracy'}, inplace = True)
def plot_graphs1(var1, var2, string):
    metrics[[var1, var2]].plot()
    plt.title('ANN Model: Training and Validation ' + string)
    plt.xlabel ('Number of epochs')
    plt.ylabel(string)
    plt.legend([var1, var2])
# Plot
plot_graphs1('Training_Loss', 'Validation_Loss', 'loss')
plot_graphs1('Training_Accuracy', 'Validation_Accuracy', 'accuracy')

# --- NEW CELL ---

y_pred = ann.predict(x_test)
y_pred = (y_pred > 0.5)

# --- NEW CELL ---

from sklearn.metrics import confusion_matrix
cm = confusion_matrix(y_test, y_pred)

# --- NEW CELL ---

cm

# --- NEW CELL ---

print("Our accuracy is %{}".format(((cm[0][0] + cm[1][1])/1035)*100))

# --- NEW CELL ---

# from keras.layers import SimpleRNN
# rnn = Sequential()
# rnn.add(SimpleRNN(128, activation='relu', input_dim=50 , return_sequences = True))
# rnn.add(SimpleRNN(64, activation='relu' ,  return_sequences = False))
# # Adding dropout to prevent overfitting
# #rnn.add(Dropout(0.1))
# rnn.add(Dense(1, activation='sigmoid'))

from keras.layers import SimpleRNN, Reshape

rnn = Sequential()
# Reshape the input to be 3-dimensional
rnn.add(Reshape((1, 50)))  # Assuming each sample has 50 features and 1 timestep
rnn.add(SimpleRNN(128, activation='relu', return_sequences=True))
rnn.add(SimpleRNN(64, activation='relu', return_sequences=False))
rnn.add(Dense(1, activation='sigmoid'))

# --- NEW CELL ---

rnn.summary()

# --- NEW CELL ---

rnn.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# --- NEW CELL ---

print(x_train.shape)
print(y_train.shape)

# --- NEW CELL ---

print(x_test.shape)
print(y_test.shape)

# --- NEW CELL ---

x_train1 = x_train.reshape(4902,1,50)
y_train1 = np.array(y_train).reshape(4902,1,1)

# --- NEW CELL ---

x_test1 = x_test.reshape(1226,1,50)
y_test1 = np.array(y_test).reshape(1226,1,1)

# --- NEW CELL ---

early_stop = EarlyStopping(monitor = 'val_loss', patience=60)

history = rnn.fit(x_train1, y_train1,
                  batch_size=100,
                  epochs=100,
                  verbose=2,
                  callbacks=[early_stop],
                  validation_data=(x_test1, y_test1))

# --- NEW CELL ---

metrics = pd.DataFrame(history.history)
# Rename column
metrics.rename(columns = {'loss': 'Training_Loss', 'accuracy': 'Training_Accuracy',
                         'val_loss': 'Validation_Loss', 'val_accuracy': 'Validation_Accuracy'}, inplace = True)
def plot_graphs1(var1, var2, string):
    metrics[[var1, var2]].plot()
    plt.title('RNN Model: Training and Validation ' + string)
    plt.xlabel ('Number of epochs')
    plt.ylabel(string)
    plt.legend([var1, var2])
# Plot
plot_graphs1('Training_Loss', 'Validation_Loss', 'loss')
plot_graphs1('Training_Accuracy', 'Validation_Accuracy', 'accuracy')

# --- NEW CELL ---

trainPredict = rnn.predict(x_train1)
testPredict= rnn.predict(x_test1)

predicted=np.concatenate((trainPredict,testPredict),axis=0)

# --- NEW CELL ---

trainScore = rnn.evaluate(x_train1, y_train1, verbose=0)
print("Our accuracy is %{}".format(trainScore[1]*100))

# --- NEW CELL ---

# from tensorflow.keras.layers import Embedding


# # Hyperparameters
# MAX_SEQUENCE_LENGTH = 50
# EMBEDDING_DIM = 16
# N_LSTM = 200
# DROP_LSTM = 0.2
# N_DENSE = 24
# NUM_EPOCHS = 30
# VOCAB_SIZE = 10000  # Adjust based on your data
# DROP_VALUE = 0.2

# # Early stopping
# early_stop = EarlyStopping(monitor='val_loss', patience=3)

# # Sample data (replace this with your actual data)
# texts = ["Free money!!!", "Call me now", "Meeting at 3pm", "Win a lottery"]  # Example text
# labels = [1, 1, 0, 1]  # Example labels (1: spam, 0: not spam)

# # Tokenization and padding
# tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token="<OOV>")
# tokenizer.fit_on_texts(texts)
# sequences = tokenizer.texts_to_sequences(texts)
# x_data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH, padding='post')
# y_data = np.array(labels)

# # Train-test split
# x_train, x_test, y_train, y_test = train_test_split(x_data, y_data, test_size=0.2, random_state=42)

# # Model definition
# lstm = Sequential([
#     Embedding(VOCAB_SIZE, EMBEDDING_DIM, input_length=MAX_SEQUENCE_LENGTH),
#     LSTM(N_LSTM, dropout=DROP_LSTM, return_sequences=True),
#     LSTM(N_LSTM, dropout=DROP_LSTM, return_sequences=False),
#     Dense(N_DENSE, activation='relu'),
#     Dropout(DROP_VALUE),
#     Dense(1, activation='sigmoid')
# ])

# # Compile the model
# lstm.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# # Train the model
# history = lstm.fit(
#     x_train, y_train,
#     validation_data=(x_test, y_test),
#     epochs=NUM_EPOCHS,
#     verbose=2,
#     callbacks=[early_stop]
# )

# # Evaluate the model
# y_pred = (lstm.predict(x_test) > 0.5).astype("int32")
# accuracy = accuracy_score(y_test, y_pred)
# print(f"Test Accuracy: {accuracy:.2f}")


from tensorflow.keras.layers import Embedding, LSTM # Import LSTM here


# Hyperparameters
MAX_SEQUENCE_LENGTH = 50
EMBEDDING_DIM = 16
N_LSTM = 200
DROP_LSTM = 0.2
N_DENSE = 24
NUM_EPOCHS = 30
VOCAB_SIZE = 10000  # Adjust based on your data
DROP_VALUE = 0.2

# Early stopping
early_stop = EarlyStopping(monitor='val_loss', patience=3)

# Sample data (replace this with your actual data)
texts = ["Free money!!!", "Call me now", "Meeting at 3pm", "Win a lottery"]  # Example text
labels = [1, 1, 0, 1]  # Example labels (1: spam, 0: not spam)

# Tokenization and padding
tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token="<OOV>")
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)
x_data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH, padding='post')
y_data = np.array(labels)

# Train-test split
x_train, x_test, y_train, y_test = train_test_split(x_data, y_data, test_size=0.2, random_state=42)

# Model definition
lstm = Sequential([
    Embedding(VOCAB_SIZE, EMBEDDING_DIM, input_length=MAX_SEQUENCE_LENGTH),
    LSTM(N_LSTM, dropout=DROP_LSTM, return_sequences=True), # Now LSTM is recognized
    LSTM(N_LSTM, dropout=DROP_LSTM, return_sequences=False),# Now LSTM is recognized
    Dense(N_DENSE, activation='relu'),
    Dropout(DROP_VALUE),
    Dense(1, activation='sigmoid')
])

# Compile the model
lstm.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# Train the model
history = lstm.fit(
    x_train, y_train,
    validation_data=(x_test, y_test),
    epochs=NUM_EPOCHS,
    verbose=2,
    callbacks=[early_stop]
)

# # Evaluate the model
# y_pred = (lstm.predict(x_test) > 0.5).astype("int32")
# accuracy = accuracy_score(y_test, y_pred)
# print(f"Test Accuracy: {accuracy:.2f}")

# ... (rest of your code) ...

# Import accuracy_score from sklearn.metrics
from sklearn.metrics import accuracy_score

# Evaluate the model
y_pred = (lstm.predict(x_test) > 0.5).astype("int32")
accuracy = accuracy_score(y_test, y_pred) # Now accuracy_score is defined
print(f"Test Accuracy: {accuracy:.2f}")

# --- NEW CELL ---

metrics = pd.DataFrame(history.history)

metrics.rename(columns= {'loss': 'Training_Loss', 'accuracy': 'Training_Accuracy',
                         'val_loss': 'Validation_Loss', 'val_accuracy': 'Validation_Accuracy'},
               inplace = True)

def plot_graphs(var1, var2, string):
    metrics[[var1, var2]].plot()
    plt.title('LSTM Model: Training and Validation ' + string)
    plt.xlabel ('Number of epochs')
    plt.ylabel(string)
    plt.legend([var1, var2])

plot_graphs('Training_Loss', 'Validation_Loss', 'loss')
plot_graphs('Training_Accuracy', 'Validation_Accuracy', 'accuracy')

# --- NEW CELL ---

# Make predictions without stateful LSTM
trainPredict2 = lstm.predict(x_train, batch_size=256)
testPredict2 = lstm.predict(x_test, batch_size=256)


# --- NEW CELL ---

# # make predictions
# trainPredict2 = lstm.predict(x_train, batch_size=256)
# lstm.reset_states()
# testPredict2 = lstm.predict(x_test, batch_size=256)
# Make predictions with stateful LSTM
trainPredict2 = lstm.predict(x_train, batch_size=256)

# Reset states for the first LSTM layer
lstm.layers[1].reset_states()

testPredict2 = lstm.predict(x_test, batch_size=256)

# Reset states for the second LSTM layer
lstm.layers[2].reset_states()


# --- NEW CELL ---


predicted2=np.concatenate((trainPredict2,testPredict2),axis=0)

# --- NEW CELL ---

trainScore2 = lstm.evaluate(x_train, y_train, verbose=0)
print("Our accuracy is %{}".format(trainScore2[1]*100))

# --- NEW CELL ---


from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Bidirectional, Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Define the parameters
vocab_size = 5000  # Adjust to your dataset
embedding_dim = 100  # You could also use pre-trained embeddings
MAX_SEQUENCE_LENGTH = 100  # Adjust based on your dataset
n_lstm = 128  # Increase LSTM units for more capacity
drop_lstm = 0.4  # Slightly reduce dropout to retain more information
batch_size = 64  # Try smaller batch size for better gradient updates
num_epochs = 500  # Increase epochs to allow more training time

# Define the model
bi_lstm = Sequential()
bi_lstm.add(Embedding(vocab_size, embedding_dim, input_length=MAX_SEQUENCE_LENGTH))
bi_lstm.add(Bidirectional(LSTM(n_lstm, dropout=drop_lstm, return_sequences=False)))  # BiLSTM layer
bi_lstm.add(Dropout(0.5))  # Add dropout layer after LSTM
bi_lstm.add(Dense(64, activation='relu'))  # Add a Dense hidden layer for more learning capacity
bi_lstm.add(BatchNormalization())  # Batch normalization layer
bi_lstm.add(Dense(1, activation='sigmoid'))  # Output layer

# Compile the model
adam_optimizer = Adam(learning_rate=0.0001)  # Lower learning rate for better convergence
bi_lstm.compile(loss='binary_crossentropy', optimizer=adam_optimizer, metrics=['accuracy'])

# Early stopping to prevent overfitting
early_stop = EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True)

# Fit the model
history2 = bi_lstm.fit(x_train, y_train, epochs=num_epochs, batch_size=batch_size,
                       validation_data=(x_test, y_test), callbacks=[early_stop], verbose=2)

# Collect metrics into DataFrame
metrics = pd.DataFrame(history2.history)
metrics.rename(columns={'loss': 'Training_Loss', 'accuracy': 'Training_Accuracy',
                        'val_loss': 'Validation_Loss', 'val_accuracy': 'Validation_Accuracy'}, inplace=True)

# Print formatted metrics
print(f"\nModel Performance:\n")
print(f"Training Accuracy: {metrics['Training_Accuracy'].iloc[-1] * 100:.2f}%")
print(f"Validation Accuracy: {metrics['Validation_Accuracy'].iloc[-1] * 100:.2f}%")
print(f"Training Loss: {metrics['Training_Loss'].iloc[-1]:.4f}")
print(f"Validation Loss: {metrics['Validation_Loss'].iloc[-1]:.4f}")

# Improved plotting function
def plot_graphs1(var1, var2, string):
    metrics[[var1, var2]].plot()
    plt.title(f'BiLSTM Model: Training and Validation {string}')
    plt.xlabel('Number of Epochs')
    plt.ylabel(string)
    plt.legend([var1, var2])
    plt.grid(True)  # Add grid for better readability
    plt.show()

# Plot the graphs
plot_graphs1('Training_Loss', 'Validation_Loss', 'Loss')
plot_graphs1('Training_Accuracy', 'Validation_Accuracy', 'Accuracy')

# Make predictions
trainPredict3 = bi_lstm.predict(x_train, batch_size=batch_size)
testPredict3 = bi_lstm.predict(x_test, batch_size=batch_size)

# Concatenate the predictions
predicted3 = np.concatenate((trainPredict3, testPredict3), axis=0)

# Evaluate the model
trainScore3 = bi_lstm.evaluate(x_train, y_train, verbose=0)
testScore3 = bi_lstm.evaluate(x_test, y_test, verbose=0)

# Print final evaluation results
print(f"\nEvaluation Results:\n")
print(f"Training Accuracy: {trainScore3[1] * 100:.2f}%")
print(f"Test Accuracy: {testScore3[1] * 100:.2f}%")


# --- NEW CELL ---

trainScore3 = bi_lstm.evaluate(x_train, y_train, verbose=0)
print("Our accuracy is %{}".format(trainScore3[1]*100))