# Use your base image (official PaddleOCR-VL image)
FROM paddlepaddle/paddleocr-vl:latest

# Set working dir
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy your FastAPI server file
COPY ocr_server.py /app/ocr_server.py

# (Dependencies installed from requirements.txt above)

# Expose port for service
EXPOSE 8000

# Command to run when container starts
CMD ["uvicorn", "ocr_server:app", "--host", "0.0.0.0", "--port", "8000"]
