from backend.ml.train import train_model
from backend.ml.evaluate import evaluate_model
from backend.ml.registry import save_model

# =====================================================
# Training
# =====================================================

training_result = train_model()

# =====================================================
# Evaluate
# =====================================================

evaluation_result = evaluate_model(training_result)

# =====================================================
# Registry
# =====================================================

save_model(evaluation_result)