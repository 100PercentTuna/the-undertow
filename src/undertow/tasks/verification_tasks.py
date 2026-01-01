"""
Celery tasks for verification operations.

Handles async claim extraction and verification.
"""

import structlog
from celery import shared_task
from typing import Any

from undertow.tasks.celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="undertow.verify_article_claims",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def verify_article_claims(
    self,
    article_id: str,
    zones: list[str] | None = None,
) -> dict[str, Any]:
    """
    Extract and verify all claims in an article.
    
    Args:
        article_id: UUID of the article to verify
        zones: Optional list of zones to search for evidence
        
    Returns:
        Verification summary with claim statuses
    """
    import asyncio
    from uuid import UUID
    
    async def _run() -> dict[str, Any]:
        from undertow.verification import get_claim_extractor, get_claim_verifier
        from undertow.verification.claim_extractor import ClaimExtractionInput
        from undertow.llm.router import get_router
        from undertow.repositories.article_repository import ArticleRepository
        from undertow.infrastructure.database import get_session
        
        async with get_session() as session:
            repo = ArticleRepository(session)
            article = await repo.get(UUID(article_id))
            
            if not article:
                return {"error": "Article not found", "article_id": article_id}
            
            # Extract claims
            router = get_router()
            extractor = get_claim_extractor(router)
            
            extraction_result = await extractor.run(
                ClaimExtractionInput(text=article.content)
            )
            
            if not extraction_result.success or not extraction_result.output:
                return {
                    "error": "Claim extraction failed",
                    "article_id": article_id,
                }
            
            # Verify claims
            verifier = get_claim_verifier()
            verified = await verifier.verify_claims_batch(
                extraction_result.output.claims,
                zones or [],
            )
            
            # Summarize results
            summary = {
                "article_id": article_id,
                "total_claims": extraction_result.output.total_claims,
                "verifiable_claims": extraction_result.output.verifiable_claims,
                "verified": sum(1 for v in verified if v.status.value == "verified"),
                "supported": sum(1 for v in verified if v.status.value == "supported"),
                "disputed": sum(1 for v in verified if v.status.value == "disputed"),
                "refuted": sum(1 for v in verified if v.status.value == "refuted"),
                "unverifiable": sum(1 for v in verified if v.status.value == "unverifiable"),
                "average_score": sum(v.verification_score for v in verified) / len(verified) if verified else 0,
            }
            
            logger.info(
                "article_claims_verified",
                article_id=article_id,
                **summary,
            )
            
            return summary
    
    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(
            "claim_verification_failed",
            article_id=article_id,
            error=str(exc),
        )
        raise self.retry(exc=exc)


@celery_app.task(
    name="undertow.batch_verify_claims",
    bind=True,
    max_retries=2,
)
def batch_verify_claims(
    self,
    claims: list[dict[str, Any]],
    zones: list[str] | None = None,
) -> dict[str, Any]:
    """
    Verify a batch of claims.
    
    Args:
        claims: List of claim dicts with text, claim_type, etc.
        zones: Optional zones to search
        
    Returns:
        Verification results
    """
    import asyncio
    
    async def _run() -> dict[str, Any]:
        from undertow.verification import get_claim_verifier
        from undertow.verification.claim_extractor import ExtractedClaim, ClaimType
        
        # Convert to ExtractedClaim objects
        extracted = [
            ExtractedClaim(
                claim_id=c.get("claim_id", f"batch-{i}"),
                text=c["text"],
                claim_type=ClaimType(c.get("claim_type", "factual")),
                confidence=c.get("confidence", 1.0),
                source_sentence=c.get("source_sentence", c["text"]),
                requires_verification=c.get("requires_verification", True),
            )
            for i, c in enumerate(claims)
        ]
        
        verifier = get_claim_verifier()
        results = await verifier.verify_claims_batch(extracted, zones or [])
        
        return {
            "total": len(results),
            "results": [
                {
                    "claim_id": r.claim.claim_id,
                    "status": r.status.value,
                    "score": r.verification_score,
                    "sources": r.independent_sources,
                }
                for r in results
            ],
        }
    
    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error("batch_verification_failed", error=str(exc))
        raise self.retry(exc=exc)


@celery_app.task(name="undertow.index_document")
def index_document(
    content: str,
    source_type: str,
    zones: list[str] | None = None,
    themes: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Index a document in the vector store for RAG.
    
    Args:
        content: Document content
        source_type: Type of source (article, news, report, etc.)
        zones: Associated zones
        themes: Associated themes
        metadata: Additional metadata
        
    Returns:
        Document ID and status
    """
    import asyncio
    
    async def _run() -> dict[str, Any]:
        from undertow.rag import get_vector_store
        
        store = await get_vector_store()
        
        doc_id = await store.add_document(
            content=content,
            source_type=source_type,
            zones=zones or [],
            themes=themes or [],
            metadata=metadata or {},
        )
        
        logger.info(
            "document_indexed",
            doc_id=str(doc_id),
            source_type=source_type,
            zones=zones,
        )
        
        return {
            "doc_id": str(doc_id),
            "source_type": source_type,
            "status": "indexed",
        }
    
    return asyncio.run(_run())


@celery_app.task(name="undertow.bulk_index_documents")
def bulk_index_documents(
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Bulk index multiple documents.
    
    Args:
        documents: List of document dicts with content, source_type, etc.
        
    Returns:
        Indexing summary
    """
    import asyncio
    
    async def _run() -> dict[str, Any]:
        from undertow.rag import get_vector_store
        
        store = await get_vector_store()
        
        indexed = 0
        failed = 0
        
        for doc in documents:
            try:
                await store.add_document(
                    content=doc["content"],
                    source_type=doc.get("source_type", "unknown"),
                    zones=doc.get("zones", []),
                    themes=doc.get("themes", []),
                    metadata=doc.get("metadata", {}),
                )
                indexed += 1
            except Exception as e:
                logger.error("document_index_failed", error=str(e))
                failed += 1
        
        return {
            "total": len(documents),
            "indexed": indexed,
            "failed": failed,
        }
    
    return asyncio.run(_run())

