import numpy as np
from sklearn.naive_bayes import CategoricalNB, GaussianNB
from sklearn.base import BaseEstimator, ClassifierMixin


class HybridNaiveBayes(BaseEstimator, ClassifierMixin):
    """
    Hybrid Naive Bayes classifier combining CategoricalNB and GaussianNB.
    
    Uses log-probability combination: combined_log_proba = w_cat * log_proba_cat + w_gauss * log_proba_gauss
    then applies softmax to get probabilities.
    """
    
    def __init__(self, weight_cat=0.1, weight_gauss=0.9):
        self.weight_cat = weight_cat
        self.weight_gauss = weight_gauss
        self.categorical_model = CategoricalNB()
        self.gaussian_model = GaussianNB()
        self.classes_ = np.array([0, 1])

    def fit(self, X_cat, X_num, y):
        self.categorical_model.fit(X_cat, y)
        self.gaussian_model.fit(X_num, y)
        return self

    def predict_proba(self, X_cat, X_num):
        cat_log_proba = self.categorical_model.predict_log_proba(X_cat)
        gauss_log_proba = self.gaussian_model.predict_log_proba(X_num)

        combined_log_proba = (
            self.weight_cat * cat_log_proba +
            self.weight_gauss * gauss_log_proba
        )

        max_log = np.max(combined_log_proba, axis=1, keepdims=True)
        exp_proba = np.exp(combined_log_proba - max_log)
        probabilities = exp_proba / exp_proba.sum(axis=1, keepdims=True)

        return probabilities

    def predict(self, X_cat, X_num):
        probabilities = self.predict_proba(X_cat, X_num)
        return self.classes_[np.argmax(probabilities, axis=1)]

    def get_params(self, deep=True):
        return {"weight_cat": self.weight_cat, "weight_gauss": self.weight_gauss}

    def set_params(self, **params):
        for k, v in params.items():
            setattr(self, k, v)
        return self