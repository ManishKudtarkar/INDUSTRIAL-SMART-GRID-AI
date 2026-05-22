# Model Documentation

## Live Models

The backend uses models that can train from synthetic operating ranges when no saved model exists. Saved models are stored under `ml_models/saved_models`.

## Isolation Forest

- File: `ml_models/anomaly_detection/isolation_forest.py`
- Purpose: point anomaly detection for one telemetry packet.
- Features: voltage, current, temperature, fifth harmonic, load percentage.
- Output: anomaly flag, normalized score, raw model score.

## Sequence Detector

- File: `ml_models/anomaly_detection/lstm_anomaly_detector.py`
- Purpose: trend anomaly detection over a rolling telemetry window.
- Implementation: lightweight numpy predictor with the same interface expected from an LSTM detector.
- Output: anomaly flag, score, prediction error, threshold.

## Optional TensorFlow Autoencoder

- File: `ml_models/anomaly_detection/advanced_lstm_autoencoder.py`
- Status: optional research implementation.
- Requirement: TensorFlow must be installed separately on a Python version supported by TensorFlow.
- It is not part of the default runtime dependencies.

## Health Score

- File: `ml/health_score.py`
- Purpose: deterministic score from `0` to `100`.
- Penalizes unsafe temperature, grid voltage, harmonics, load, and anomaly flags.
- Handles partial hardware packets by skipping missing fields.

## Overload Prediction

- File: `ml_models/prediction/overload_predictor.py`
- Purpose: estimate whether a substation will overload in the next few readings.
- Output includes overload probability and prediction horizon.

## Transformer Failure Prediction

- File: `ml_models/prediction/transformer_failure_predictor.py`
- Purpose: estimate 24-hour transformer failure probability from rolling history.

## Load Optimization

- Files: `ml_models/load_balancing/load_optimizer.py` and `redistribution_engine.py`
- Purpose: recommend and smooth load redistribution away from degraded substations.
