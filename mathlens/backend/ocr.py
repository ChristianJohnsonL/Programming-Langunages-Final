import os
import requests

OCR_MOCK = os.environ.get("OCR_MOCK", "true").lower() in ("true", "1", "yes")
API_KEY = os.environ.get("GCP_VISION_API_KEY", "")

_VISION_URL = "https://vision.googleapis.com/v1/images:annotate"

_MOCK_RESPONSES = [
    "x² + 5x + 6",
    "2x + y = 5",
    "x - y = 1",
    "x^2 - 4",
    "3x + 2 = 11",
]
_mock_index = 0


def extract_text(image_b64: str) -> str:
    global _mock_index
    if OCR_MOCK:
        text = _MOCK_RESPONSES[_mock_index % len(_MOCK_RESPONSES)]
        _mock_index += 1
        return text

    if not API_KEY:
        raise RuntimeError("GCP_VISION_API_KEY is not set in environment.")

    payload = {
        "requests": [{
            "image": {"content": image_b64},
            "features": [{"type": "TEXT_DETECTION"}],
        }]
    }
    response = requests.post(_VISION_URL, params={"key": API_KEY}, json=payload, timeout=15)
    response.raise_for_status()

    data = response.json()
    annotations = data["responses"][0].get("textAnnotations")
    if not annotations:
        return ""
    return annotations[0]["description"].strip()
