FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
# ARIES-owned standard-library native inference; no external model API or secret required.
COPY software/ ./software/
COPY aries_math/ ./aries_math/
COPY software/deployment_corpus.txt ./data/training.txt
RUN mkdir -p models data && python software/native_runtime.py train --corpus ./data/training.txt --model ./models/aries-native-ngram.json
ENV ARIES_NATIVE_MODEL=/app/models/aries-native-ngram.json
EXPOSE 10000
CMD ["python", "software/public_native_server.py"]
