docker build -t paddleocr-vl-service:latest .
docker run --rm -p 80:80 paddleocr-vl-service:latest