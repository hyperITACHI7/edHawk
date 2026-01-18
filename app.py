from flask import Flask, request, jsonify
from extractor import extract_course_data

app = Flask(__name__)

@app.route("/extract", methods=["POST"])
def extract():
    payload = request.get_json()

    if not payload or "course_url" not in payload:
        return jsonify({"error": "course_url missing"}), 400

    try:
        result = extract_course_data(payload["course_url"])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
