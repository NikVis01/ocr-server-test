# Use your base image (official PaddleOCR-VL image)
FROM paddlepaddle/paddleocr-vl:latest

# Set working dir
WORKDIR /app

# Copy your FastAPI server file
COPY ocr_server.py /app/ocr_server.py

# Install FastAPI and Uvicorn (if not already in base)
RUN pip install fastapi uvicorn[standard] numpy opencv-python

# Expose port for service
EXPOSE 8000

# Command to run when container starts
CMD ["uvicorn", "ocr_server:app", "--host", "0.0.0.0", "--port", "8000"]
