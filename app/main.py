"""FastAPI application — QueueStorm Investigator.

Endpoints:
  GET  /health         → {"status": "ok"}
  POST /analyze-ticket → TicketResponse
"""

import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import TicketRequest, TicketResponse
from app.investigator import investigate

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("QueueStorm Investigator starting up")
    logger.info(f"Model: {settings.model_name}")
    logger.info(f"LLM enabled: {bool(settings.groq_api_key)}")
    yield
    logger.info("QueueStorm Investigator shutting down")


app = FastAPI(
    title="QueueStorm Investigator",
    description="AI-powered support ticket investigator for digital finance",
    version="1.0.0",
    lifespan=lifespan,
)


# --- Endpoints ---

@app.get("/health")
async def health():
    """Health check endpoint. Must return within 60s of service start."""
    return {"status": "ok"}


@app.post("/analyze-ticket", response_model=TicketResponse)
async def analyze_ticket(ticket: TicketRequest):
    """Analyze a support ticket and return a structured verdict."""
    start = time.time()

    # Validate complaint is non-empty
    if not ticket.complaint or not ticket.complaint.strip():
        return JSONResponse(
            status_code=422,
            content={"error": "Complaint cannot be empty"},
        )

    result = await investigate(ticket)

    elapsed = time.time() - start
    logger.info(f"Ticket {ticket.ticket_id} processed in {elapsed:.2f}s")

    return result


# --- Error handlers ---

@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors (malformed input) → 400."""
    return JSONResponse(
        status_code=400,
        content={
            "error": "Invalid request schema",
            "detail": str(exc),
        },
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    """Catch-all error handler → 500. Never expose stack traces."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"},
    )
