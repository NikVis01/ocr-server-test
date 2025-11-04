yipppiii


CLIENT:
import requests

def send_image_for_ocr(server_url: str, image_path: str):
    with open(image_path, "rb") as f:
        files = {"file": (image_path, f, "image/jpeg")}
        response = requests.post(server_url + "/ocr/", files=files)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    SERVER_URL = "http://localhost:8000"
    IMAGE_PATH = "path/to/your/image.jpg"
    result = send_image_for_ocr(SERVER_URL, IMAGE_PATH)
    print("OCR result:", result)

