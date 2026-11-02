FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt api_requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r api_requirements.txt

COPY src/ ./src/
COPY api.py ./

ENV MODEL_PATH=/app/models/sih_cost_prediction_model.pkl

EXPOSE 8000

CMD ["python", "api.py"]

