FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    CV_MANIFEST=/app/models/cv/manifest.json ORT_THREADS=2 MAX_INFLIGHT=2
WORKDIR /app
COPY requirements-cv.txt .
RUN python -m pip install --no-cache-dir -r requirements-cv.txt
COPY src ./src
COPY scripts/smoke_cv.py ./scripts/smoke_cv.py
# A release image must contain a pre-exported, validated model. No training at startup.
COPY models/cv ./models/cv
RUN python -c "from pathlib import Path; from src.cv.detector import Detector; detector=Detector(Path('models/cv/manifest.json')); assert set(detector.labels)=={'helmet','no_helmet','person'}, 'A trained helmet model is required'"
EXPOSE 8000
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
