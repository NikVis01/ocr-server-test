# GPU base with Paddle 3.x
FROM paddlepaddle/paddle:3.2.0-gpu-cuda12.6-cudnn8

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app sources
COPY app/ /app/app/

# Pre-download PaddleOCR-VL models by running a tiny warm-up
RUN python - <<'PY'
import numpy as np
from paddleocr import PaddleOCRVL
pipe = PaddleOCRVL()
pipe.predict(np.zeros((10,10,3), dtype='uint8'))
print('PaddleOCR-VL warm-up complete')
PY

EXPOSE 80

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
