# Official PaddleOCR-VL base (CCR registry)
FROM ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddleocr-vl:latest

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Install Paddle (CPU by default). Override at build time for GPU wheels.
# Example GPU build: 
#   docker build --build-arg PADDLE_PACKAGE="paddlepaddle-gpu==2.6.1" \
#                --build-arg PADDLE_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple" \
#                -t paddleocr-vl-service:latest .
ARG PADDLE_PACKAGE=paddlepaddle==2.6.1
ARG PADDLE_INDEX=https://pypi.org/simple
RUN pip install --no-cache-dir ${PADDLE_PACKAGE} -i ${PADDLE_INDEX}

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
