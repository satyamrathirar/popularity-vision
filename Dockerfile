FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# The API will be run by Uvicorn, managed by docker-compose
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "80"]