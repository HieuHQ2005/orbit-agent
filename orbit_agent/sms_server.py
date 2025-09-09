from __future__ import annotations

import os
import logging
from flask import Flask, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator

from .config import configure_lm
from .advisor import HighOrbitAdvisor, log_advice

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address, default_limits=["10 per minute"])
limiter.init_app(app)

# Preload LM and advisor
configure_lm()
advisor = HighOrbitAdvisor()

PLAYBOOK_PATH = os.getenv("ORBIT_PLAYBOOK", "playbooks/high_orbit.yaml")
playbook = ""
if os.path.exists(PLAYBOOK_PATH):
    try:
        with open(PLAYBOOK_PATH) as f:
            playbook = f.read()
    except Exception as e:
        logger.error(f"Failed to load playbook: {e}")

# Twilio configuration
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
validator = RequestValidator(TWILIO_AUTH_TOKEN) if TWILIO_AUTH_TOKEN else None
ALLOW_INSECURE = os.getenv("ORBIT_ALLOW_INSECURE_TWILIO", "false").lower() == "true"
PERSONAL_NUMBER = os.getenv("PERSONAL_NUMBER")
RESTRICT_FROM = os.getenv("ORBIT_RESTRICT_FROM", "true").lower() == "true"


def validate_twilio_request():
    """Validate that the request came from Twilio"""
    if not validator:
        if ALLOW_INSECURE:
            logger.warning("Twilio validation disabled (insecure mode enabled)")
            return True
        logger.error("Twilio auth token not configured and insecure mode disabled")
        return False

    signature = request.headers.get("X-Twilio-Signature", "")
    url = request.url
    params = request.form.to_dict()

    return validator.validate(url, params, signature)


@app.route("/sms", methods=["POST"])
@limiter.limit("5 per minute")  # Stricter limit for SMS endpoint
def sms():
    try:
        # Validate Twilio signature
        if not validate_twilio_request():
            logger.warning(f"Invalid Twilio signature from {request.remote_addr}")
            return "Unauthorized", 401

        body = request.values.get("Body", "").strip()
        from_number = request.values.get("From", "unknown")
        # Optional: restrict to a single allowed sender (owner's phone)
        if RESTRICT_FROM and PERSONAL_NUMBER and from_number != PERSONAL_NUMBER:
            logger.warning(f"SMS rejected: unauthorized From={from_number}")
            return "Forbidden", 403

        logger.info(f"SMS received from {from_number}: {body[:50]}...")

        resp = MessagingResponse()

        if not body:
            resp.message(
                "Send a question. Try: 'Focus: 10 paid design partner calls in 7 days'"
            )
            return str(resp)

        # Limit input length to prevent abuse
        if len(body) > 1000:
            resp.message(
                "Message too long. Please keep questions under 1000 characters."
            )
            return str(resp)

        # Light command routing
        if body.lower().startswith("focus:"):
            q = body
        else:
            q = body

        # Format as proper history for advisor
        history = [{"role": "user", "content": q}]
        result = advisor(history=history, playbook=playbook)
        log_advice(history, result)

        # Parse actions from string format for SMS
        actions_text = ""
        if isinstance(result.actions_48h, str):
            actions = [
                line.strip()
                for line in result.actions_48h.split("\n")
                if line.strip() and not line.strip().startswith("**")
            ]
            actions_text = "\n- " + "\n- ".join(
                [action.lstrip("123456789. -•") for action in actions[:3]]
            )
        else:
            actions_text = "\n- " + "\n- ".join(result.actions_48h[:3])

        reply = (
            f"Advice:\n{result.advice}\n\n"
            f"48h:{actions_text}\n\n"
            f"Metric: {result.metric_to_watch}\n"
            f"Score: {result.score}/10"
        )

        # SMS length is constrained; keep it short
        if len(reply) > 1400:
            reply = reply[:1395] + "..."

        resp.message(reply)
        logger.info(f"Response sent to {from_number}, score: {result.score}")
        return str(resp)

    except Exception as e:
        logger.error(f"Error processing SMS: {e}")
        resp = MessagingResponse()
        resp.message("Sorry, I encountered an error. Please try again.")
        return str(resp)


@app.route("/health", methods=["GET"])
def health():
    return {"status": "healthy", "service": "orbit-agent-sms"}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug_mode = os.environ.get("FLASK_ENV") == "development"

    if debug_mode:
        logger.warning("Running in debug mode")

    app.run(host="0.0.0.0", port=port, debug=debug_mode)
