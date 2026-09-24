# SIH Cost Prediction Model

This project implements the workflow described for extracting project-table data from a PDF, cleaning it, training a cost-overrun prediction model, and running new predictions from saved model artifacts.

## Project structure

- `src/extract_pdf.py` – extracts table data from a PDF and saves it as CSV.
- `src/train_model.py` – cleans the extracted data, trains an XGBoost regressor, and saves the model.
- `src/predict.py` – loads the saved model and predicts cost overrun for a new project.
- `requirements.txt` – required Python dependencies.

## Quick start

1. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

2. Extract tables from a PDF:

   ```bash
   python src/extract_pdf.py --pdf data/MoSPI_Flash_Report.pdf --output data/extracted_project_data.csv
   ```

3. Train the model:

   ```bash
   python src/train_model.py --input data/extracted_project_data.csv --output models/sih_cost_prediction_model.pkl
   ```

4. Predict new cost overrun:

   ```bash
   python src/predict.py --sector "Road Transport & Highways" --original-cost 1500.50 --physical-progress 45
   ```

## Notes

- The PDFs used by SIH infrastructure reports often contain data in tables with numbers formatted as currency strings. The cleaning step strips commas, currency symbols, and percentage signs before training.
- The model uses a `ColumnTransformer` with one-hot encoding for the `Sector` column and an XGBoost regressor for the target variable `Overrun_Amount`.
- The saved model is stored in pickle format for later reuse in a frontend/backend workflow.

## Example architecture

1. Frontend: React or HTML form for entering project details.
2. Backend: FastAPI/Flask service that loads the model and returns predictions.
3. ML core: trained model artifact built from PDF-extracted data.
