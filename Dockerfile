# Use a lightweight Python base image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /code

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app files into the container
COPY app.py .
COPY index.html .

# Expose the port your app runs on
EXPOSE 7860

# Start the FastAPI app using uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
