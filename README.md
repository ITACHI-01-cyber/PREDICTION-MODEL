# Model Run Guide

The application files and input data are organized under `model/`:

```text
model/
  data/       Extracted CSV data and source PDF reports
  models/     Trained model and sweep output
  src/        Training, prediction, and analysis scripts
  tests/      Automated tests
```

Run the following commands from the repository root.

Install:

```bash
python -m pip install -r requirements.txt
```

Train the model:

```bash
python model/src/train_model.py
```

Run a single prediction:

```bash
python model/src/predict.py --sector "Power" --original-cost 5000 --physical-progress 30 --time-delay 18
```

Run a batch of test cases:

```bash
python model/src/test_batch.py
```

Run the test file:

```bash
python -m unittest discover -s model/tests
```

This is a small project for training and testing the cost and time overrun prediction model.
