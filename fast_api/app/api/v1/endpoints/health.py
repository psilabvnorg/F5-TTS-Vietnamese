"""
Health check and monitoring endpoints
"""

from fastapi import APIRouter, Response
from app.models.health import HealthResponse, QueueMetrics, ModelInfo
from app.api.v1.endpoints.tts import queue_manager
from app.api.deps import ModelHandlerDep
from app.core.config import settings
from app.core.logging import logger


router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health_check(handler: ModelHandlerDep):
    """
    Health check endpoint with detailed system status
    
    Returns:
    - Service status
    - Model information
    - Queue metrics
    - System capacity
    """
    try:
        # Get model info from handler
        model_info_dict = handler.get_model_info()
        
        model_info = ModelInfo(
            loaded=True,
            model_name=model_info_dict["model_name"],
            vocoder_name=model_info_dict["vocoder_name"],
            vocab_file=model_info_dict.get("vocab_file"),
            device="cuda",  # Could be improved to get actual device
            sample_rate=settings.SAMPLE_RATE
        )
        
        queue_metrics = QueueMetrics(
            current_size=queue_manager.in_queue,
            max_size=settings.MAX_QUEUE_SIZE,
            total_requests=queue_manager.total_requests,
            completed=queue_manager.completed_requests,
            failed=queue_manager.failed_requests
        )
        
        capacity = {
            "max_concurrent": settings.MAX_CONCURRENT_INFERENCE,
            "available": settings.MAX_CONCURRENT_INFERENCE - queue_manager.in_queue
        }
        
        return HealthResponse(
            status="healthy",
            version=settings.VERSION,
            model=model_info,
            queue=queue_metrics,
            cache=None,  # TODO: Add cache info if Redis enabled
            capacity=capacity
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        # Return degraded status but don't fail
        return HealthResponse(
            status="degraded",
            version=settings.VERSION,
            model=ModelInfo(
                loaded=False,
                model_name="unknown",
                vocoder_name="unknown"
            ),
            queue=QueueMetrics(
                current_size=0,
                max_size=settings.MAX_QUEUE_SIZE,
                total_requests=0,
                completed=0,
                failed=0
            ),
            capacity={"max_concurrent": 0, "available": 0}
        )


@router.get("/liveness")
async def liveness_probe():
    """
    Kubernetes liveness probe
    
    Returns 200 if service is alive
    """
    return {"status": "alive"}


@router.get("/readiness")
async def readiness_probe(handler: ModelHandlerDep):
    """
    Kubernetes readiness probe
    
    Returns 200 if service is ready to accept traffic
    """
    try:
        # Check if model is loaded
        handler.get_model_info()
        return {"status": "ready"}
    except Exception as e:
        logger.warning(f"Readiness check failed: {e}")
        return Response(
            content='{"status": "not_ready"}',
            status_code=503,
            media_type="application/json"
        )


@router.get("/metrics")
async def get_metrics():
    """
    Get basic metrics
    
    TODO: Integrate Prometheus metrics if needed
    """
    return {
        "queue": {
            "current": queue_manager.in_queue,
            "total_requests": queue_manager.total_requests,
            "completed": queue_manager.completed_requests,
            "failed": queue_manager.failed_requests,
            "success_rate": (
                queue_manager.completed_requests / queue_manager.total_requests * 100
                if queue_manager.total_requests > 0
                else 0.0
            )
        }
    }
