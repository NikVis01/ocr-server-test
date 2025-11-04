# Use your base image (official PaddleOCR-VL image)
FROM ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddleocr-vl:latest

# Set working dir
WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy your FastAPI server file
COPY ocr_server.py /app/ocr_server.py

# Pre-download PaddleOCR models by running a tiny warm-up
RUN python - <<'PY'
import numpy as np
from paddleocr import PaddleOCR
ocr = PaddleOCR(use_angle_cls=True, lang='en')
ocr.ocr(np.zeros((10,10,3), dtype='uint8'), cls=True)
print('Model warm-up complete')
PY

# Expose port for service
EXPOSE 8080

# Command to run when container starts
CMD ["uvicorn", "ocr_server:app", "--host", "0.0.0.0", "--port", "80"]
