FROM python:3.11.1-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 1235

ENV AUTHENTICATION_HOST=nau_authentication
ENV ORCHESTRATION_HOST=nau_orchestation


CMD ["python", "app.py"]