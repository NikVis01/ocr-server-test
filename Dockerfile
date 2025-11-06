# Official PaddleOCR-VL base (CCR registry)
FROM ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddleocr-vl:latest

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Ensure Paddle (GPU, CUDA 12.6+) is available in the runtime image
ARG PADDLE_GPU_VERSION=3.2.1
ENV PADDLE_PDX_MODEL_SOURCE=BOS
RUN pip install --no-cache-dir \
    paddlepaddle-gpu==${PADDLE_GPU_VERSION} \
    -i https://www.paddlepaddle.org.cn/packages/stable/cu126/

# Sanity check versions
RUN python - <<'PY'
import paddle
import paddlex
print('paddle', paddle.__version__)
print('paddlex', getattr(paddlex, '__version__', 'unknown'))
PY

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

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
