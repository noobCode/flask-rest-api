# Step 1: Choose base image (the foundation)
FROM python:3.12-slim

# Step 2: Set working directory inside container
WORKDIR /app

# Step 3: Copy requirements first (for better caching)
COPY requirements.txt .

# Step 4: Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 5: Copy your application code
COPY . .

# Step 6: Expose the port Flask runs on
EXPOSE 5000

# Step 7: Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Step 8: Define the command to run your app
CMD ["python", "app.py"]