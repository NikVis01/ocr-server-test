# Build the service image (CCR base already includes CUDA stack)
docker build -t paddleocr-vl-service:latest .