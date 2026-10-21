FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential cmake curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN CMAKE_ARGS="-DGGML_NATIVE=OFF" CMAKE_BUILD_PARALLEL_LEVEL=2 \
    pip install --no-cache-dir \
    --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu \
    llama-cpp-python==0.3.36

COPY software/ ./software/
COPY aries_math/ ./aries_math/
COPY software/deployment_corpus.txt ./data/training.txt

RUN mkdir -p models data /app/licenses \
    && curl --fail --location --retry 3 --retry-delay 2 \
       "https://huggingface.co/bartowski/SmolLM2-135M-Instruct-GGUF/resolve/09816acd5d99df7be770d85ea30822623dab342c/SmolLM2-135M-Instruct-Q4_K_M.gguf?download=true" \
       --output /app/models/SmolLM2-135M-Instruct-Q4_K_M.gguf \
    && echo "2e8040ceae7815abe0dcb3540b9995eaa1fa0d2ca9e797d0a635ae4433c68c2d  /app/models/SmolLM2-135M-Instruct-Q4_K_M.gguf" | sha256sum --check - \
    && curl --fail --location --retry 3 https://www.apache.org/licenses/LICENSE-2.0.txt --output /app/licenses/Apache-2.0.txt \
    && python software/native_runtime.py train --corpus ./data/training.txt --model ./models/aries-native-ngram.json

ENV ARIES_NATIVE_MODEL=/app/models/aries-native-ngram.json
ENV ARIES_GGUF_MODEL_PATH=/app/models/SmolLM2-135M-Instruct-Q4_K_M.gguf
ENV ARIES_LOCAL_MODEL_THREADS=1

EXPOSE 10000
CMD ["python", "software/public_native_server.py"]
