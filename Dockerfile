# Use a more modern and stable base image (Debian Bullseye)
FROM python:3.11.4-slim-bullseye

# Install necessary tools for adding a new repository
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Add Google's official software signing key using the modern method
RUN curl -sS -o - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor | tee /usr/share/keyrings/google-chrome.gpg >/dev/null

# Add the official Google Chrome repository to the system's software sources
RUN echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Update package lists and install the latest stable version of Google Chrome
RUN apt-get update && apt-get install -y google-chrome-stable --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory for the application
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Set the command that will run when the container starts
CMD ["python", "bo.py"]
