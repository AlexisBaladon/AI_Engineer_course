FROM python:3.11.1-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 1232

ENV RETRIEVAL_HOST=nau_retrieval
ENV RANKING_HOST=nau_ranking
ENV GENERATION_HOST=nau_agent


CMD ["python", "app.py"]