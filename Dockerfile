# --- Base Image ---
# Use the official PaddlePaddle image compatible with your CUDA 12.7 driver.
# This image includes Python, PaddlePaddle-GPU, CUDA, and cuDNN.
FROM paddlepaddle/paddle:3.1.0-gpu-cuda12.6-cudnn9.5

# --- System Setup ---
# Set the working directory inside the container
WORKDIR /app

# --- THIS IS THE FIX ---
# Install missing system libraries required by OpenCV (cv2) and other common packages.
# `libgl1-mesa-glx` provides the `libGL.so.1` that was missing.
# We also install git, which paddlex can sometimes use.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*
# --- END OF FIX ---

# --- Python Dependencies ---
# Copy ONLY the requirements file first for Docker layer caching.
COPY requirements.txt .

# Install Python packages from requirements.txt.
# Then, install the specific paddlex[ocr] extras group.
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir "paddlex[ocr]"

# --- Application Code ---
# Now, copy the rest of your application code into the container.
COPY . .

# --- Port & Command ---
# Expose the port that your FastAPI application will run on.
EXPOSE 8001

# Define the command to run your application when the container starts.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]