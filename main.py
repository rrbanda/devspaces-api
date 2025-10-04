"""
DevSpaces Workspace API
FastAPI application for managing DevSpaces workspaces (IntelliJ)
"""

import yaml
import os
import time
import asyncio
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
def load_config():
    """Load configuration from config.yaml or use defaults"""
    config_path = "config.yaml"
    if not os.path.exists(config_path):
        logger.warning(f"Config file {config_path} not found. Using defaults.")
        return get_default_config()
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info("Configuration loaded successfully")
        return config
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return get_default_config()

def get_default_config():
    """Default configuration if config.yaml is not available"""
    return {
        "openshift": {
            "api_server": "https://api.<your-cluster-domain>:6443",
            "console_url": "https://console-openshift-console.apps.<your-cluster-domain>",
            "devspaces_url": "https://devspaces.apps.<your-cluster-domain>"
        },
        "workspace": {
            "default_namespace": "admin-devspaces",
            "routing_class": "che",
            "intellij": {
                "memory_limit": "8Gi",
                "memory_request": "2Gi",
                "cpu_limit": "2000m",
                "cpu_request": "500m",
                "container_image": "quay.io/devfile/universal-developer-image:ubi8-latest",
                "default_repo": "https://github.com/spring-projects/spring-petclinic"
            },
        },
        "api": {
            "title": "DevSpaces Workspace API",
            "description": "API for managing DevSpaces workspaces (IntelliJ)",
            "version": "1.0.0",
            "host": "0.0.0.0",
            "port": 8000,
            "debug": False
        }
    }

# Load configuration
config = load_config()

# Initialize FastAPI app
app = FastAPI(
    title=config["api"]["title"],
    description=config["api"]["description"],
    version=config["api"]["version"]
)

# Pydantic models
class WorkspaceRequest(BaseModel):
    namespace: str = Field(default=config["workspace"]["default_namespace"], description="OpenShift namespace")
    git_repo: str = Field(default="", description="Git repository URL")
    memory_limit: Optional[str] = Field(default=None, description="Memory limit for workspace")
    cpu_limit: Optional[str] = Field(default=None, description="CPU limit for workspace")

class IntelliJWorkspaceRequest(WorkspaceRequest):
    git_repo: str = Field(default=config["workspace"]["intellij"]["default_repo"], description="Git repository URL")
    memory_limit: str = Field(default=config["workspace"]["intellij"]["memory_limit"], description="Memory limit")
    cpu_limit: str = Field(default=config["workspace"]["intellij"]["cpu_limit"], description="CPU limit")


class WorkspaceResponse(BaseModel):
    name: str
    namespace: str
    phase: str
    message: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[str] = None

class WorkspaceListResponse(BaseModel):
    workspaces: List[WorkspaceResponse]
    total: int

class DeleteResponse(BaseModel):
    status: str
    message: str

# Dependency to get token from Authorization header
def get_token(authorization: str = Header(...)) -> str:
    """Extract token from Authorization header"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    return authorization.replace("Bearer ", "")

# HTTP client dependency
async def get_http_client():
    """Get async HTTP client"""
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        yield client

# Helper functions
def generate_workspace_name(prefix: str = "workspace") -> str:
    """Generate unique workspace name"""
    timestamp = int(time.time()) % 100000
    import random
    random_suffix = random.randint(1000, 9999)
    return f"{prefix}-{timestamp}-{random_suffix}"

async def make_openshift_request(
    client: httpx.AsyncClient,
    method: str,
    endpoint: str,
    token: str,
    data: Optional[Dict] = None
) -> httpx.Response:
    """Make authenticated request to OpenShift API"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = f"{config['openshift']['api_server']}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = await client.get(url, headers=headers)
        elif method.upper() == "POST":
            response = await client.post(url, headers=headers, json=data)
        elif method.upper() == "PATCH":
            headers["Content-Type"] = "application/merge-patch+json"
            response = await client.patch(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported HTTP method: {method}")
        
        return response
    except httpx.RequestError as e:
        logger.error(f"Request error: {e}")
        raise HTTPException(status_code=500, detail=f"Request failed: {str(e)}")

# API Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "DevSpaces Workspace API",
        "version": config["api"]["version"],
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/workspaces/{namespace}", response_model=WorkspaceListResponse)
async def list_workspaces(
    namespace: str,
    token: str = Depends(get_token),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """List all DevWorkspaces in a namespace"""
    try:
        response = await make_openshift_request(
            client, "GET", 
            f"/apis/workspace.devfile.io/v1alpha2/namespaces/{namespace}/devworkspaces",
            token
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Failed to list workspaces")
        
        data = response.json()
        workspaces = []
        
        for item in data.get("items", []):
            workspace = WorkspaceResponse(
                name=item["metadata"]["name"],
                namespace=item["metadata"]["namespace"],
                phase=item.get("status", {}).get("phase", "Unknown"),
                message=item.get("status", {}).get("message"),
                url=item.get("status", {}).get("mainUrl"),
                created_at=item["metadata"].get("creationTimestamp")
            )
            workspaces.append(workspace)
        
        return WorkspaceListResponse(workspaces=workspaces, total=len(workspaces))
        
    except Exception as e:
        logger.error(f"Error listing workspaces: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workspaces/intellij", response_model=WorkspaceResponse)
async def create_intellij_workspace(
    request: IntelliJWorkspaceRequest,
    token: str = Depends(get_token),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Create an IntelliJ DevWorkspace"""
    try:
        ws_name = generate_workspace_name("intellij")
        template_name = f"{ws_name}-ide"
        
        logger.info(f"Creating IntelliJ workspace: {ws_name}")
        
        # Create IDE template
        template_data = {
            "apiVersion": "workspace.devfile.io/v1alpha2",
            "kind": "DevWorkspaceTemplate",
            "metadata": {
                "name": template_name,
                "namespace": request.namespace
            },
            "spec": {
                "components": [{
                    "name": "che-idea-runtime",
                    "container": {
                        "image": "quay.io/che-incubator/che-idea:next",
                        "memoryLimit": request.memory_limit,
                        "memoryRequest": config["workspace"]["intellij"]["memory_request"],
                        "cpuLimit": request.cpu_limit,
                        "cpuRequest": config["workspace"]["intellij"]["cpu_request"],
                        "endpoints": [{
                            "name": "intellij",
                            "exposure": "public",
                            "targetPort": 8887,
                            "protocol": "https",
                            "attributes": {
                                "type": "main",
                                "cookiesAuthEnabled": "true",
                                "discoverable": "false",
                                "urlRewriteSupported": "true"
                            }
                        }]
                    }
                }]
            }
        }
        
        template_response = await make_openshift_request(
            client, "POST",
            f"/apis/workspace.devfile.io/v1alpha2/namespaces/{request.namespace}/devworkspacetemplates",
            token, template_data
        )
        
        if template_response.status_code != 201:
            logger.error(f"Template creation failed: {template_response.text}")
            raise HTTPException(status_code=template_response.status_code, detail="IDE template creation failed")
        
        logger.info(f"IDE template created: {template_name}")
        await asyncio.sleep(2)  # Wait for template to be ready
        
        # Create workspace
        workspace_data = {
            "apiVersion": "workspace.devfile.io/v1alpha2",
            "kind": "DevWorkspace",
            "metadata": {
                "name": ws_name,
                "namespace": request.namespace
            },
            "spec": {
                "routingClass": config["workspace"]["routing_class"],
                "started": True,
                "contributions": [{
                    "name": "ide",
                    "kubernetes": {"name": template_name}
                }],
                "template": {
                    "projects": [{
                        "name": "project",
                        "git": {"remotes": {"origin": request.git_repo}}
                    }],
                    "components": [{
                        "name": "tools",
                        "container": {
                            "image": config["workspace"]["intellij"]["container_image"],
                            "memoryLimit": request.memory_limit,
                            "memoryRequest": config["workspace"]["intellij"]["memory_request"],
                            "cpuLimit": request.cpu_limit,
                            "cpuRequest": config["workspace"]["intellij"]["cpu_request"]
                        }
                    }]
                }
            }
        }
        
        workspace_response = await make_openshift_request(
            client, "POST",
            f"/apis/workspace.devfile.io/v1alpha2/namespaces/{request.namespace}/devworkspaces",
            token, workspace_data
        )
        
        if workspace_response.status_code != 201:
            logger.error(f"Workspace creation failed: {workspace_response.text}")
            raise HTTPException(status_code=workspace_response.status_code, detail="Workspace creation failed")
        
        logger.info(f"IntelliJ workspace created successfully: {ws_name}")
        
        return WorkspaceResponse(
            name=ws_name,
            namespace=request.namespace,
            phase="Starting",
            message="IntelliJ workspace created successfully",
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        )
        
    except Exception as e:
        logger.error(f"Error creating IntelliJ workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/workspaces/{namespace}/{name}", response_model=WorkspaceResponse)
async def get_workspace(
    namespace: str,
    name: str,
    token: str = Depends(get_token),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Get a specific DevWorkspace"""
    try:
        response = await make_openshift_request(
            client, "GET",
            f"/apis/workspace.devfile.io/v1alpha2/namespaces/{namespace}/devworkspaces/{name}",
            token
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Workspace not found")
        
        data = response.json()
        
        return WorkspaceResponse(
            name=name,
            namespace=namespace,
            phase=data.get("status", {}).get("phase", "Unknown"),
            message=data.get("status", {}).get("message"),
            url=data.get("status", {}).get("mainUrl"),
            created_at=data["metadata"].get("creationTimestamp")
        )
        
    except Exception as e:
        logger.error(f"Error getting workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/workspaces/{namespace}/{name}", response_model=DeleteResponse)
async def delete_workspace(
    namespace: str,
    name: str,
    token: str = Depends(get_token),
    client: httpx.AsyncClient = Depends(get_http_client)
):
    """Delete a DevWorkspace"""
    try:
        response = await make_openshift_request(
            client, "DELETE",
            f"/apis/workspace.devfile.io/v1alpha2/namespaces/{namespace}/devworkspaces/{name}",
            token
        )
        
        if response.status_code == 200:
            logger.info(f"Workspace deleted successfully: {name}")
            return DeleteResponse(status="deleted", message=f"Workspace {name} deleted successfully")
        else:
            logger.error(f"Workspace deletion failed: {response.text}")
            return DeleteResponse(status="failed", message=f"Failed to delete workspace {name}")
        
    except Exception as e:
        logger.error(f"Error deleting workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config["api"]["host"],
        port=config["api"]["port"],
        reload=config["api"]["debug"]
    )
