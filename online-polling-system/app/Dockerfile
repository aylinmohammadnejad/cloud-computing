FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn pydantic[email]
CMD ["python", "main.py"]
