FROM python:3.9-slim

WORKDIR /app

# Copy requirements.txt first (ensures better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Start the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "blockchain:app"]
