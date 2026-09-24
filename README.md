# Model Run Guide

Simple setup and run steps.

Install:

```bash
python -m pip install -r requirements.txt
```

Train the model:

```bash
python src/train_model.py
```

Run a single prediction:

```bash
python src/predict.py --sector "Power" --original-cost 5000 --physical-progress 30 --time-delay 18
```

Run a batch of test cases:

```bash
python src/test_batch.py
```

Run the test file:

```bash
python tests/test_parameter_sweep.py
```

This is a small project for training and testing the cost and time overrun prediction model.
