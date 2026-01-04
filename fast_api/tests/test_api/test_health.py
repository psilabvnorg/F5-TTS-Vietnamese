"""
Tests for health check endpoints
"""

import pytest
from fastapi import status


class TestHealthEndpoints:
    """Test health check and monitoring endpoints"""
    
    def test_health_check(self, client, mock_model_handler):
        """Test main health check endpoint"""
        response = client.get("/api/v1/health/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "model" in data
        assert data["model"]["loaded"] is True
        assert data["model"]["model_name"] == "F5TTS_Base"
        assert "queue" in data
        assert "capacity" in data
    
    def test_liveness_probe(self, client):
        """Test Kubernetes liveness probe"""
        response = client.get("/api/v1/health/liveness")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["status"] == "alive"
    
    def test_readiness_probe(self, client, mock_model_handler):
        """Test Kubernetes readiness probe"""
        response = client.get("/api/v1/health/readiness")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["status"] == "ready"
    
    def test_metrics(self, client):
        """Test metrics endpoint"""
        response = client.get("/api/v1/health/metrics")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "queue" in data
        assert "total_requests" in data["queue"]
        assert "completed" in data["queue"]
        assert "failed" in data["queue"]
