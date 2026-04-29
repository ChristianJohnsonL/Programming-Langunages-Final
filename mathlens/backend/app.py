import os
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify

from normalizer import normalize
from parser import parse
from solver import solve
import ocr as ocr_module

app = Flask(__name__)


def _pipeline(raw_input: str) -> dict:
    normalized, corrections = normalize(raw_input)
    ast = parse(normalized)
    solution = solve(ast)
    return (
        {
            "raw_input": raw_input,
            "normalized": normalized,
            "corrections": corrections,
            "ast": ast,
            "solution": solution if "error" not in solution else None,
            "error": solution if "error" in solution else None,
        }
    )


@app.route("/solve/text", methods=["POST"])
def solve_text():
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Field 'text' is required"}), 400
    return jsonify(_pipeline(text))


@app.route("/solve/image", methods=["POST"])
def solve_image():
    data = request.get_json(force=True, silent=True) or {}
    image_b64 = data.get("image", "")
    if not image_b64:
        return jsonify({"error": "Field 'image' (base64) is required"}), 400
    try:
        raw = ocr_module.extract_text(image_b64)
    except Exception as exc:
        return jsonify({"error": f"OCR failed: {exc}"}), 500
    return jsonify(_pipeline(raw))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
