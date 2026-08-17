"""Fail-closed public onboarding API for Google Cloud Run."""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import os
from pathlib import Path

from flask import Flask, jsonify, request
from jsonschema import Draft202012Validator, FormatChecker

from intake_store import RateLimitExceeded, firestore_store_from_env


SCHEMA = json.loads((Path(__file__).parent / "schemas" / "onboarding-request.schema.json").read_text(encoding="utf-8"))
VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())


def _digest(secret, value):
    return hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()


def _canonical_payload(payload):
    normalized = dict(payload)
    normalized["email"] = normalized["email"].strip().lower()
    normalized["name"] = normalized["name"].strip()
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def create_app(config=None, store=None):
    app = Flask(__name__)
    app.config.update(
        ALLOWED_WEBSITE_ORIGIN=os.getenv("ALLOWED_WEBSITE_ORIGIN", ""),
        ONBOARDING_REQUEST_RATE_LIMIT_PER_HOUR=int(os.getenv("ONBOARDING_REQUEST_RATE_LIMIT_PER_HOUR", "5")),
        MAX_CONTENT_LENGTH=int(os.getenv("ONBOARDING_REQUEST_MAX_BODY_BYTES", "8192")),
        INTAKE_HASH_KEY=os.getenv("INTAKE_HASH_KEY", ""),
    )
    if config:
        app.config.update(config)
    intake_store = store

    def get_store():
        nonlocal intake_store
        if intake_store is None:
            intake_store = firestore_store_from_env()
        return intake_store

    @app.after_request
    def apply_headers(response):
        origin = request.headers.get("Origin", "")
        if origin and hmac.compare_digest(origin, app.config["ALLOWED_WEBSITE_ORIGIN"]):
            response.headers.update({
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
                "Access-Control-Max-Age": "600",
                "Vary": "Origin",
            })
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    @app.route("/v1/public/onboarding-requests", methods=["POST", "OPTIONS"])
    def onboarding_requests():
        allowed_origin = app.config["ALLOWED_WEBSITE_ORIGIN"]
        hash_key = app.config["INTAKE_HASH_KEY"]
        origin = request.headers.get("Origin", "")
        if not allowed_origin or not hash_key:
            return jsonify({"error": "Service is not configured."}), 503
        if not origin or not hmac.compare_digest(origin, allowed_origin):
            return jsonify({"error": "Origin is not allowed."}), 403
        if request.method == "OPTIONS":
            return "", 204
        if not request.is_json:
            return jsonify({"error": "A JSON request body is required."}), 415
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "Malformed request."}), 400
        if sorted(VALIDATOR.iter_errors(payload), key=lambda error: list(error.path)):
            return jsonify({"error": "Request validation failed."}), 400

        canonical = _canonical_payload(payload)
        request_id = _digest(hash_key, canonical)[:32]
        rate_keys = [
            _digest(hash_key, f"ip:{request.remote_addr or 'unknown'}"),
            _digest(hash_key, f"email:{payload['email'].strip().lower()}"),
        ]
        record = {
            "requestId": request_id,
            "status": "NEEDS_OWNER_REVIEW",
            "mode": "DRY_RUN",
            "source": payload["source"],
            "submittedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            "externalActionTaken": False,
            "nextStep": "Owner reviews intake request in Approval Queue",
            "queueState": "PRIVATE_INTAKE",
            "payload": payload,
        }
        try:
            stored, _created = get_store().create_request(record, rate_keys, app.config["ONBOARDING_REQUEST_RATE_LIMIT_PER_HOUR"])
        except RateLimitExceeded:
            return jsonify({"error": "Too many requests. Please try again later."}), 429
        except Exception:
            app.logger.exception("Onboarding intake persistence failed")
            return jsonify({"error": "Unable to accept the request right now."}), 503
        return jsonify({
            "requestId": stored["requestId"],
            "status": "NEEDS_OWNER_REVIEW",
            "message": "Your request has been received for owner review.",
        }), 202
    return app


app = create_app()


if __name__ == "__main__":
    if os.getenv("WORKFORCE_INTAKE_BACKEND") != "firestore":
        raise SystemExit("Set WORKFORCE_INTAKE_BACKEND=firestore before starting the API.")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
