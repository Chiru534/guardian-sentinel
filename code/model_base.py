from abc import ABC, abstractmethod


class ModelBase(ABC):
    """
    Abstract machine learning model base class defining the standard interface.
    """

    @abstractmethod
    def build_model(self):
        """
        Defines the Keras Sequential architecture.
        """
        pass

    @abstractmethod
    def compile(self, optimizer='adam', loss='binary_crossentropy', metrics=['accuracy']):
        """
        Configures the model for training.
        """
        pass

    @abstractmethod
    def fit(self, x_train, y_train, validation_data=None, epochs=30, batch_size=32, callbacks=None):
        """
        Executes the training loop.
        """
        pass

    @abstractmethod
    def predict(self, x):
        """
        Generates probability or class predictions.
        """
        pass

    @abstractmethod
    def evaluate(self, x, y):
        """
        Returns performance metrics for the model.
        """
        pass
