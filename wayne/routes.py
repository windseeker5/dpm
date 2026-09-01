"""Flask routes for Wayne, the local-first minipass data assistant."""

import time
from datetime import datetime

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, session, url_for

from decorators import admin_required, rate_limit
from models import QueryLog, db
from wayne.client import OpenRouterConfigError, OpenRouterRequestError, configured_model
from wayne.router import route_question
from wayne.skills import SKILLS

wayne_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")


def _message(kind: str, language: str) -> str:
    messages = {
        "greeting": {
            "en": "Hello, I’m Wayne. Ask me about your minipass activities, participants, signups, passports, payments, bookings, attendance, surveys, or finances.",
            "fr": "Bonjour, je suis Wayne. Posez-moi vos questions sur les activités, participants, inscriptions, passeports, paiements, réservations, présences, sondages ou finances de minipass.",
        },
        "out_of_scope": {
            "en": "I’m Wayne, your minipass data assistant. I can only help with information stored in minipass.",
            "fr": "Je suis Wayne, votre assistant de données minipass. Je peux seulement vous aider avec les informations enregistrées dans minipass.",
        },
        "unsupported": {
            "en": "That concerns minipass data, but I don’t have the required skill yet. Ask an administrator to add it to Wayne’s skill library.",
            "fr": "Cette question concerne les données de minipass, mais je n’ai pas encore la compétence requise. Demandez à un administrateur de l’ajouter à la bibliothèque de Wayne.",
        },
    }
    return messages[kind][language]


def _log_query(question, decision, status, elapsed_ms, row_count=0, error=None, answer=None):
    try:
        entry = QueryLog(
            admin_email=session.get("admin", "unknown"),
            original_question=question,
            generated_sql=f"skill:{decision.skill or decision.status}",
            execution_status=status,
            execution_time_ms=elapsed_ms,
            rows_returned=row_count,
            error_message=error,
            ai_answer=answer,
            ai_provider=decision.source,
            ai_model=decision.model,
            tokens_used=decision.tokens_used,
            cost_cents=0,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Wayne query audit logging failed")


@wayne_bp.route("/")
def index():
    if "admin" not in session:
        flash("You must be logged in as admin to access Wayne.", "error")
        return redirect(url_for("login"))
    return render_template("analytics_chatbot_simple.html", model_name=configured_model())


@wayne_bp.route("/ask", methods=["POST"])
@admin_required
@rate_limit(max_requests=30, window=60)
def ask():
    started = time.monotonic()
    question = request.form.get("question", "").strip()
    if not question:
        return jsonify(success=False, error="Please enter a question."), 400
    if len(question) > 500:
        return jsonify(success=False, error="Your question must be 500 characters or fewer."), 400

    try:
        decision = route_question(question)
        if decision.status != "skill":
            answer = _message(decision.status, decision.language)
            elapsed = int((time.monotonic() - started) * 1000)
            _log_query(question, decision, "success", elapsed, answer=answer)
            return jsonify(success=True, answer=answer, rows=[], columns=[], skill=None)

        skill = SKILLS[decision.skill]
        result = skill.handler(decision.arguments, decision.language)
        elapsed = int((time.monotonic() - started) * 1000)
        _log_query(
            question,
            decision,
            "success",
            elapsed,
            row_count=len(result.rows),
            answer=result.answer,
        )
        return jsonify(
            success=True,
            answer=result.answer,
            columns=result.columns,
            rows=result.rows,
            row_count=len(result.rows),
            skill=decision.skill,
            routed_by=decision.source,
        )
    except OpenRouterConfigError:
        current_app.logger.warning("Wayne needs OpenRouter configuration for an unmatched question")
        return jsonify(
            success=False,
            error="Wayne could not match that question locally, and OpenRouter is not configured. Add OPENROUTER_API_KEY to .env.",
        ), 503
    except (OpenRouterRequestError, ValueError) as exc:
        current_app.logger.warning("Wayne routing failed: %s", exc)
        return jsonify(
            success=False,
            error="Wayne could not understand that question right now. Please try a more specific wording.",
        ), 503
    except Exception as exc:
        db.session.rollback()
        elapsed = int((time.monotonic() - started) * 1000)
        current_app.logger.exception("Wayne skill execution failed")
        return jsonify(
            success=False,
            error="Wayne could not retrieve that minipass data. Please try again.",
        ), 500
