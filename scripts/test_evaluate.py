from backend.ml.train import train_model
from backend.ml.evaluate import evaluate_model

# Jalankan training
training_result = train_model()

# Evaluasi hasil training
evaluate_model(training_result)