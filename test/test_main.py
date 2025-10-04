"""
Unit tests for DevSpaces Workspace API
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import Response
import main

# Test client
client = TestClient(main.app)

# Mock data
MOCK_WORKSPACE_RESPONSE = {
    "apiVersion": "workspace.devfile.io/v1alpha2",
    "kind": "DevWorkspace",
    "metadata": {
        "name": "test-workspace",
        "namespace": "admin-devspaces",
        "creationTimestamp": "2023-01-01T00:00:00Z"
    },
    "status": {
        "phase": "Running",
        "message": "Workspace is running",
        "mainUrl": "https://workspace.example.com"
    }
}

MOCK_WORKSPACE_LIST_RESPONSE = {
    "apiVersion": "v1",
    "kind": "DevWorkspaceList",
    "items": [MOCK_WORKSPACE_RESPONSE]
}

class TestHealthEndpoints:
    """Test health and root endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["message"] == "DevSpaces Workspace API"
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

class TestWorkspaceEndpoints:
    """Test workspace management endpoints"""
    
    @patch('main.make_openshift_request')
    def test_list_workspaces_success(self, mock_request):
        """Test successful workspace listing"""
        # Mock the OpenShift API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_WORKSPACE_LIST_RESPONSE
        mock_request.return_value = mock_response
        
        response = client.get(
            "/workspaces/admin-devspaces",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["workspaces"]) == 1
        assert data["workspaces"][0]["name"] == "test-workspace"
        assert data["workspaces"][0]["phase"] == "Running"
    
    @patch('main.make_openshift_request')
    def test_list_workspaces_failure(self, mock_request):
        """Test workspace listing failure"""
        # Mock the OpenShift API response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_request.return_value = mock_response
        
        response = client.get(
            "/workspaces/admin-devspaces",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 500
    
    @patch('main.make_openshift_request')
    def test_get_workspace_success(self, mock_request):
        """Test successful workspace retrieval"""
        # Mock the OpenShift API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_WORKSPACE_RESPONSE
        mock_request.return_value = mock_response
        
        response = client.get(
            "/workspaces/admin-devspaces/test-workspace",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "test-workspace"
        assert data["namespace"] == "admin-devspaces"
        assert data["phase"] == "Running"
        assert data["url"] == "https://workspace.example.com"
    
    @patch('main.make_openshift_request')
    def test_get_workspace_not_found(self, mock_request):
        """Test workspace not found"""
        # Mock the OpenShift API response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_request.return_value = mock_response
        
        response = client.get(
            "/workspaces/admin-devspaces/nonexistent",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 404
    
    @patch('main.make_openshift_request')
    def test_delete_workspace_success(self, mock_request):
        """Test successful workspace deletion"""
        # Mock the OpenShift API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response
        
        response = client.delete(
            "/workspaces/admin-devspaces/test-workspace",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "deleted"
        assert "deleted successfully" in data["message"]
    
    @patch('main.make_openshift_request')
    def test_delete_workspace_failure(self, mock_request):
        """Test workspace deletion failure"""
        # Mock the OpenShift API response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_request.return_value = mock_response
        
        response = client.delete(
            "/workspaces/admin-devspaces/test-workspace",
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200  # API returns 200 with failure status
        data = response.json()
        assert data["status"] == "failed"

class TestIntelliJWorkspaceCreation:
    """Test IntelliJ workspace creation"""
    
    @patch('main.make_openshift_request')
    @patch('main.generate_workspace_name')
    def test_create_intellij_workspace_success(self, mock_name, mock_request):
        """Test successful IntelliJ workspace creation"""
        # Mock workspace name generation
        mock_name.return_value = "intellij-12345"
        
        # Mock template creation response
        template_response = Mock()
        template_response.status_code = 201
        
        # Mock workspace creation response
        workspace_response = Mock()
        workspace_response.status_code = 201
        
        # Mock the OpenShift API calls
        mock_request.side_effect = [template_response, workspace_response]
        
        request_data = {
            "namespace": "admin-devspaces",
            "git_repo": "https://github.com/spring-projects/spring-petclinic",
            "memory_limit": "8Gi",
            "cpu_limit": "2000m"
        }
        
        response = client.post(
            "/workspaces/intellij",
            headers={"Authorization": "Bearer test-token"},
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "intellij-12345"
        assert data["namespace"] == "admin-devspaces"
        assert data["phase"] == "Starting"
        assert "IntelliJ workspace created successfully" in data["message"]
    
    @patch('main.make_openshift_request')
    def test_create_intellij_workspace_template_failure(self, mock_request):
        """Test IntelliJ workspace creation with template failure"""
        # Mock template creation failure
        template_response = Mock()
        template_response.status_code = 500
        template_response.text = "Template creation failed"
        mock_request.return_value = template_response
        
        request_data = {
            "namespace": "admin-devspaces",
            "git_repo": "https://github.com/spring-projects/spring-petclinic"
        }
        
        response = client.post(
            "/workspaces/intellij",
            headers={"Authorization": "Bearer test-token"},
            json=request_data
        )
        
        assert response.status_code == 500
        assert "Template creation failed" in response.json()["detail"]

class TestVSCodeWorkspaceCreation:
    """Test VS Code workspace creation"""
    
    @patch('main.make_openshift_request')
    @patch('main.generate_workspace_name')
    def test_create_vscode_workspace_success(self, mock_name, mock_request):
        """Test successful VS Code workspace creation"""
        # Mock workspace name generation
        mock_name.return_value = "vscode-12345"
        
        # Mock workspace creation response
        workspace_response = Mock()
        workspace_response.status_code = 201
        mock_request.return_value = workspace_response
        
        request_data = {
            "namespace": "admin-devspaces",
            "git_repo": "https://github.com/quarkusio/quarkus-quickstarts",
            "memory_limit": "4Gi",
            "cpu_limit": "2000m"
        }
        
        response = client.post(
            "/workspaces/vscode",
            headers={"Authorization": "Bearer test-token"},
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "vscode-12345"
        assert data["namespace"] == "admin-devspaces"
        assert data["phase"] == "Starting"
        assert "VS Code workspace created successfully" in data["message"]
    
    @patch('main.make_openshift_request')
    def test_create_vscode_workspace_failure(self, mock_request):
        """Test VS Code workspace creation failure"""
        # Mock workspace creation failure
        workspace_response = Mock()
        workspace_response.status_code = 500
        workspace_response.text = "Workspace creation failed"
        mock_request.return_value = workspace_response
        
        request_data = {
            "namespace": "admin-devspaces",
            "git_repo": "https://github.com/quarkusio/quarkus-quickstarts"
        }
        
        response = client.post(
            "/workspaces/vscode",
            headers={"Authorization": "Bearer test-token"},
            json=request_data
        )
        
        assert response.status_code == 500
        assert "Workspace creation failed" in response.json()["detail"]

class TestAuthentication:
    """Test authentication and authorization"""
    
    def test_missing_authorization_header(self):
        """Test missing authorization header"""
        response = client.get("/workspaces/admin-devspaces")
        assert response.status_code == 422  # Validation error
    
    def test_invalid_authorization_header(self):
        """Test invalid authorization header format"""
        response = client.get(
            "/workspaces/admin-devspaces",
            headers={"Authorization": "Invalid token"}
        )
        assert response.status_code == 401
    
    def test_valid_authorization_header(self):
        """Test valid authorization header format"""
        with patch('main.make_openshift_request') as mock_request:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"items": []}
            mock_request.return_value = mock_response
            
            response = client.get(
                "/workspaces/admin-devspaces",
                headers={"Authorization": "Bearer valid-token"}
            )
            assert response.status_code == 200

class TestConfiguration:
    """Test configuration loading"""
    
    def test_default_config_loading(self):
        """Test that default configuration is loaded when config.yaml is missing"""
        # This test ensures the app can start without config.yaml
        assert main.config is not None
        assert "openshift" in main.config
        assert "workspace" in main.config
        assert "api" in main.config
    
    def test_config_structure(self):
        """Test configuration structure"""
        config = main.config
        
        # Test OpenShift config
        assert "api_server" in config["openshift"]
        assert "console_url" in config["openshift"]
        assert "devspaces_url" in config["openshift"]
        
        # Test workspace config
        assert "default_namespace" in config["workspace"]
        assert "routing_class" in config["workspace"]
        assert "intellij" in config["workspace"]
        assert "vscode" in config["workspace"]
        
        # Test API config
        assert "title" in config["api"]
        assert "version" in config["api"]
        assert "host" in config["api"]
        assert "port" in config["api"]

class TestHelperFunctions:
    """Test helper functions"""
    
    def test_generate_workspace_name(self):
        """Test workspace name generation"""
        name1 = main.generate_workspace_name("test")
        name2 = main.generate_workspace_name("test")
        
        assert name1.startswith("test-")
        assert name2.startswith("test-")
        assert name1 != name2  # Should be unique
    
    def test_generate_workspace_name_default(self):
        """Test workspace name generation with default prefix"""
        name = main.generate_workspace_name()
        assert name.startswith("workspace-")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
