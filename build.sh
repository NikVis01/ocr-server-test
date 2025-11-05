docker build -t paddleocr-vl-service:latest .
docker run --rm -p 8080:8080 paddleocr-vl-service:latest