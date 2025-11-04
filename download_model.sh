docker run \
    -it \
    --gpus all \
    --network host \
    --user root \
    ccr-2vdh3abv-pub.cnc.bj.baidubce.com/paddlepaddle/paddleocr-vl:latest \
    /bin/bash
# 在容器中调用 PaddleOCR CLI 或 Python API