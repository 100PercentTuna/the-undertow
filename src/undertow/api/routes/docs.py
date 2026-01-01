"""
Documentation API routes.

Provides enhanced API documentation and examples.
"""

from typing import Any
from fastapi import APIRouter

router = APIRouter(prefix="/docs-api", tags=["Documentation"])


@router.get("/examples")
async def get_api_examples() -> dict[str, Any]:
    """
    Get API usage examples.
    
    Returns example requests and responses for key endpoints.
    """
    return {
        "description": "The Undertow API Examples",
        "examples": {
            "create_story": {
                "endpoint": "POST /api/v1/stories",
                "description": "Create a new story for analysis",
                "request": {
                    "headline": "Israel Recognizes Somaliland Independence",
                    "summary": "Israel becomes second country to formally recognize Somaliland sovereignty, signaling Red Sea strategy shift",
                    "zones": ["horn_of_africa", "levant", "gulf_gcc"],
                    "themes": ["diplomacy", "security", "maritime"],
                    "sources": [
                        "https://example.com/israel-somaliland-recognition"
                    ],
                },
                "response": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "headline": "Israel Recognizes Somaliland Independence",
                    "status": "pending",
                    "created_at": "2024-01-05T10:00:00Z",
                },
            },
            "analyze_story": {
                "endpoint": "POST /api/v1/stories/{id}/analyze",
                "description": "Trigger full analysis pipeline for a story",
                "request": None,
                "response": {
                    "run_id": "660e8400-e29b-41d4-a716-446655440001",
                    "status": "running",
                    "started_at": "2024-01-05T10:01:00Z",
                },
            },
            "extract_claims": {
                "endpoint": "POST /api/v1/verification/extract",
                "description": "Extract verifiable claims from text",
                "request": {
                    "text": "Israel recognized Somaliland on January 5, 2024. This makes Israel the second country to formally recognize Somaliland's independence.",
                    "focus_areas": ["diplomacy"],
                },
                "response": {
                    "claims": [
                        {
                            "claim_id": "claim-001",
                            "text": "Israel recognized Somaliland on January 5, 2024",
                            "claim_type": "factual",
                            "confidence": 0.95,
                            "requires_verification": True,
                        }
                    ],
                    "total_claims": 1,
                    "verifiable_claims": 1,
                },
            },
            "resolve_escalation": {
                "endpoint": "POST /api/v1/escalations/{id}/resolve",
                "description": "Resolve a pending escalation",
                "request": {
                    "status": "approved",
                    "reviewer": "editor@example.com",
                    "notes": "Verified all claims, approved for publication",
                },
                "response": {
                    "escalation_id": "770e8400-e29b-41d4-a716-446655440002",
                    "status": "approved",
                    "resolved_at": "2024-01-05T11:00:00Z",
                },
            },
        },
    }


@router.get("/webhooks")
async def get_webhook_documentation() -> dict[str, Any]:
    """
    Get webhook event documentation.
    
    Returns all webhook event types and their payloads.
    """
    return {
        "description": "Webhook Events Documentation",
        "authentication": {
            "type": "HMAC-SHA256",
            "header": "X-Webhook-Signature",
            "format": "sha256=<signature>",
            "verification": "Compute HMAC-SHA256 of raw request body using your webhook secret",
        },
        "events": {
            "article.created": {
                "description": "Fired when a new article is generated",
                "payload": {
                    "event_type": "article.created",
                    "timestamp": "2024-01-05T10:00:00Z",
                    "data": {
                        "article_id": "uuid",
                        "headline": "string",
                        "story_id": "uuid",
                        "quality_score": 0.87,
                    },
                },
            },
            "article.published": {
                "description": "Fired when an article is published",
                "payload": {
                    "event_type": "article.published",
                    "timestamp": "2024-01-05T10:30:00Z",
                    "data": {
                        "article_id": "uuid",
                        "headline": "string",
                        "publish_url": "string",
                    },
                },
            },
            "pipeline.completed": {
                "description": "Fired when daily pipeline completes",
                "payload": {
                    "event_type": "pipeline.completed",
                    "timestamp": "2024-01-05T09:00:00Z",
                    "data": {
                        "run_id": "uuid",
                        "articles_generated": 5,
                        "total_cost": 12.50,
                        "duration_seconds": 3600,
                    },
                },
            },
            "pipeline.failed": {
                "description": "Fired when pipeline fails",
                "payload": {
                    "event_type": "pipeline.failed",
                    "timestamp": "2024-01-05T08:30:00Z",
                    "data": {
                        "run_id": "uuid",
                        "stage": "analysis",
                        "error": "string",
                    },
                },
            },
            "escalation.created": {
                "description": "Fired when content is escalated for review",
                "payload": {
                    "event_type": "escalation.created",
                    "timestamp": "2024-01-05T10:00:00Z",
                    "data": {
                        "escalation_id": "uuid",
                        "priority": "high",
                        "reason": "low_quality",
                        "story_headline": "string",
                        "quality_score": 0.65,
                    },
                },
            },
            "escalation.resolved": {
                "description": "Fired when escalation is resolved",
                "payload": {
                    "event_type": "escalation.resolved",
                    "timestamp": "2024-01-05T11:00:00Z",
                    "data": {
                        "escalation_id": "uuid",
                        "status": "approved",
                        "reviewer": "string",
                    },
                },
            },
            "newsletter.sent": {
                "description": "Fired when daily newsletter is sent",
                "payload": {
                    "event_type": "newsletter.sent",
                    "timestamp": "2024-01-05T10:00:00Z",
                    "data": {
                        "edition_date": "2024-01-05",
                        "recipients": 1500,
                        "articles_included": 5,
                    },
                },
            },
        },
        "retry_policy": {
            "max_retries": 5,
            "backoff": "exponential",
            "initial_delay_seconds": 30,
        },
    }


@router.get("/rate-limits")
async def get_rate_limit_documentation() -> dict[str, Any]:
    """
    Get rate limiting documentation.
    """
    return {
        "description": "API Rate Limits",
        "limits": {
            "default": {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
            },
            "pipeline": {
                "description": "Pipeline trigger endpoints",
                "requests_per_hour": 10,
            },
            "analysis": {
                "description": "Analysis endpoints (LLM-heavy)",
                "requests_per_minute": 10,
            },
            "verification": {
                "description": "Claim verification",
                "requests_per_minute": 30,
            },
        },
        "headers": {
            "X-RateLimit-Limit": "Maximum requests allowed",
            "X-RateLimit-Remaining": "Requests remaining in window",
            "X-RateLimit-Reset": "Unix timestamp when limit resets",
            "Retry-After": "Seconds to wait (on 429 response)",
        },
        "response_429": {
            "status": 429,
            "body": {
                "detail": "Rate limit exceeded",
                "retry_after": 30,
            },
        },
    }


@router.get("/errors")
async def get_error_documentation() -> dict[str, Any]:
    """
    Get error code documentation.
    """
    return {
        "description": "API Error Codes",
        "format": {
            "detail": "Human-readable error message",
            "code": "Machine-readable error code (optional)",
            "field": "Field that caused error (validation errors)",
        },
        "http_codes": {
            "400": {
                "name": "Bad Request",
                "causes": [
                    "Invalid JSON payload",
                    "Missing required fields",
                    "Invalid field values",
                ],
            },
            "401": {
                "name": "Unauthorized",
                "causes": [
                    "Missing X-API-Key header",
                    "Invalid API key",
                ],
            },
            "403": {
                "name": "Forbidden",
                "causes": [
                    "API key lacks required permissions",
                    "Resource access denied",
                ],
            },
            "404": {
                "name": "Not Found",
                "causes": [
                    "Resource does not exist",
                    "Invalid endpoint path",
                ],
            },
            "422": {
                "name": "Validation Error",
                "causes": [
                    "Field type mismatch",
                    "Value out of allowed range",
                    "Invalid enum value",
                ],
            },
            "429": {
                "name": "Too Many Requests",
                "causes": [
                    "Rate limit exceeded",
                ],
            },
            "500": {
                "name": "Internal Server Error",
                "causes": [
                    "Unexpected server error",
                    "Database connection failure",
                    "LLM provider error",
                ],
            },
            "503": {
                "name": "Service Unavailable",
                "causes": [
                    "Maintenance mode",
                    "Dependency unavailable",
                ],
            },
        },
        "custom_codes": {
            "BUDGET_EXCEEDED": "Daily cost budget has been reached",
            "PIPELINE_RUNNING": "A pipeline is already running",
            "QUALITY_GATE_FAILED": "Content did not pass quality gate",
            "ESCALATION_REQUIRED": "Content requires human review",
            "VERIFICATION_FAILED": "Claim could not be verified",
        },
    }


@router.get("/zones")
async def get_zone_documentation() -> dict[str, Any]:
    """
    Get zone system documentation.
    """
    return {
        "description": "42-Zone Global Coverage System",
        "regions": {
            "europe": {
                "zones": [
                    {"id": "western_europe", "name": "Western Europe (Core EU)", "countries": "France, Germany, Benelux, Austria, Switzerland"},
                    {"id": "southern_europe", "name": "Southern Europe", "countries": "Italy, Spain, Portugal, Greece, Cyprus, Malta"},
                    {"id": "nordic_baltic", "name": "Nordic-Baltic", "countries": "Sweden, Norway, Denmark, Finland, Iceland, Estonia, Latvia, Lithuania"},
                    {"id": "british_isles", "name": "British Isles", "countries": "UK, Ireland"},
                    {"id": "central_europe", "name": "Central Europe", "countries": "Poland, Czech Republic, Slovakia, Hungary, Slovenia"},
                    {"id": "western_balkans", "name": "Western Balkans", "countries": "Serbia, Kosovo, Bosnia, North Macedonia, Albania, Montenegro"},
                    {"id": "eastern_europe", "name": "Eastern Europe", "countries": "Ukraine, Moldova, Belarus"},
                    {"id": "south_caucasus", "name": "South Caucasus", "countries": "Georgia, Armenia, Azerbaijan"},
                ],
            },
            "russia_eurasia": {
                "zones": [
                    {"id": "russia_core", "name": "Russian Federation", "countries": "Russia, Siberia, Far East"},
                    {"id": "central_asia_west", "name": "Central Asia (Western)", "countries": "Kazakhstan, Uzbekistan, Turkmenistan"},
                    {"id": "central_asia_east", "name": "Central Asia (Eastern)", "countries": "Kyrgyzstan, Tajikistan"},
                ],
            },
            "middle_east_north_africa": {
                "zones": [
                    {"id": "levant", "name": "Levant", "countries": "Syria, Lebanon, Jordan, Palestinian Territories"},
                    {"id": "gulf_gcc", "name": "Gulf GCC", "countries": "Saudi Arabia, UAE, Qatar, Kuwait, Bahrain, Oman"},
                    {"id": "iraq", "name": "Iraq", "countries": "Federal Iraq, Kurdistan Region"},
                    {"id": "iran", "name": "Iran", "countries": "Islamic Republic of Iran"},
                    {"id": "turkey", "name": "Turkey", "countries": "Republic of Türkiye"},
                    {"id": "maghreb", "name": "Maghreb", "countries": "Morocco, Algeria, Tunisia, Libya"},
                    {"id": "egypt", "name": "Egypt", "countries": "Arab Republic of Egypt"},
                ],
            },
            # Additional regions would follow the same pattern
        },
        "usage": {
            "filtering": "Use zone IDs to filter stories, articles, and sources",
            "analysis": "Each zone has specialized sources and historical context",
            "interconnections": "Zones are connected through geopolitical relationships",
        },
    }

