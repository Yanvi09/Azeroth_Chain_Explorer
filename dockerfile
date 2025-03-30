FROM python:3.9-slim

WORKDIR /app

# 🛠️ Fix: Copy requirements.txt from parent folder
COPY ../requirements.txt .  
RUN pip install --no-cache-dir -r requirements.txt  

# 🛠️ Fix: Copy entire project (move up one level)
COPY .. .  

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "blockchain:app"]
