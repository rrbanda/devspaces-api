# DevSpaces DevWorkspace API

This repository provides comprehensive tools and documentation for the OpenShift DevSpaces DevWorkspace API. It includes both shell scripts and a Python FastAPI implementation for managing IntelliJ DevSpaces workspaces.
<img width="1489" height="840" alt="Screenshot 2025-10-06 at 2 14 22 PM" src="https://github.com/user-attachments/assets/4a238a22-ccae-403f-ad47-ee417799213f" />

<img width="1639" height="723" alt="Screenshot 2025-10-06 at 2 40 51 PM" src="https://github.com/user-attachments/assets/81d689ff-ebea-4312-8076-226c0f035b4d" />


## 📁 Repository Structure

```
devspaces-api/
├── docs/                          # Documentation
│   ├── devspaces-devworkspace-openapi.yaml  # OpenAPI specification
│   ├── openapi.json              # Generated OpenAPI spec
│   └── DevSpaces-Workspace-API.postman_collection.json  # Postman collection
├── img/                           # Screenshots and images
│   ├── api-testing.png            # API testing screenshots
│   ├── workspace-creation.png     # Workspace creation process
│   └── final-result.png           # Final workspace result
├── scripts/                       # Shell script tests
│   └── intellij.sh               # IntelliJ workspace creation script
├── test/                          # Python unit tests
│   └── test_main.py              # FastAPI application tests
├── main.py                        # FastAPI application
├── config.yaml.example           # Python API configuration template
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
└── LICENSE                        # MIT License
```

## 🚀 Quick Start

### Prerequisites

- OpenShift cluster with DevSpaces installed
- OpenShift CLI (`oc`) installed and logged in
- Access to a DevSpaces user namespace (e.g., `admin-devspaces`)

### Option 1: Shell Script (Quick Test)

The simplest way to create an IntelliJ workspace:

```bash
cd scripts
chmod +x intellij.sh
./intellij.sh
```

This script will:
- Auto-detect your OpenShift login and token
- Prompt for namespace (defaults to `admin-devspaces`)
- Create an IntelliJ DevWorkspace with JetBrains Gateway support
- Start the workspace
- Report the status

### Option 2: Python FastAPI Application (Full API)

For a complete REST API with all workspace management features:

```bash
# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure and run
cp config.yaml.example config.yaml
# Edit config.yaml with your cluster details
python main.py
```

## 📋 Available Scripts

### IntelliJ Workspace Creation Script
**File:** `scripts/intellij.sh`

**Features:**
-  **Secure authentication** - Uses OpenShift tokens for authentication
-  **Auto-detects cluster** - Gets API server from current OpenShift context
-  **Interactive prompts** - Only asks for namespace (defaults to `admin-devspaces`)
-  **JetBrains Gateway ready** - Creates workspace compatible with IntelliJ Gateway
-  **Full IDE template** - Creates proper DevWorkspaceTemplate with IntelliJ runtime

**Usage:**
```bash
cd scripts
chmod +x intellij.sh
./intellij.sh
```

**What it creates:**
- DevWorkspaceTemplate with IntelliJ IDE runtime
- DevWorkspace with Spring Petclinic project
- Proper endpoint configuration for JetBrains Gateway
- Universal Developer Image for development tools

## 🐍 Python FastAPI Application

The repository includes a complete FastAPI application that provides a REST API for managing IntelliJ DevSpaces workspaces.

### Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. **Copy configuration template:**
   ```bash
   cp config.yaml.example config.yaml
   ```

2. **Edit `config.yaml` with your cluster details:**
   ```yaml
   openshift:
     api_server: "https://api.<your-cluster-domain>:6443"
     console_url: "https://console-openshift-console.apps.<your-cluster-domain>"
     devspaces_url: "https://devspaces.apps.<your-cluster-domain>"
   
   workspace:
     default_namespace: "admin-devspaces"
   ```

   **Note:** Replace `<your-cluster-domain>` with your actual OpenShift cluster domain.

### Running the API

```bash
# Start the FastAPI server
source venv/bin/activate
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json

![API Documentation](img/api-testing.png)
*FastAPI interactive documentation and API testing*

### Using Swagger UI

The interactive documentation at `/docs` provides a user-friendly interface to test the API:

1. **Open Swagger UI**: Navigate to `http://localhost:8000/docs`
2. **Authorize**: Click the 🔒 "Authorize" button at the top right
3. **Enter Token**: Input your OpenShift Bearer token (e.g., `sha256~...`)
4. **Test Endpoints**: All workspace endpoints will automatically include your token

> **Note**: The authorization field shown in individual endpoint parameters is automatically handled once you authorize at the top level.

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| GET | `/health` | Health check |
| GET | `/workspaces/{namespace}` | List workspaces |
| GET | `/workspaces/{namespace}/{name}` | Get workspace details |
| POST | `/workspaces/intellij` | Create IntelliJ workspace |
| DELETE | `/workspaces/{namespace}/{name}` | Delete workspace |

### Authentication

All workspace endpoints require a Bearer token in the Authorization header. The API uses standard HTTP Bearer authentication.

**Important**: If you're not logged in to OpenShift, you can use a valid token directly. Test your token first:

> **Security Note**: Never commit real tokens to version control. Use environment variables or secure token management.

#### Testing Your Token

```bash
# Test token directly against OpenShift API (with SSL bypass for self-signed certs)
curl -k -H "Authorization: Bearer YOUR_OPENSHIFT_TOKEN" \
     "https://api.cluster-k2ds9.k2ds9.sandbox2151.opentlc.com:6443/apis/user.openshift.io/v1/users/~"

# If successful, you'll get user info. Then use the token with our API:
export OPENSHIFT_TOKEN="YOUR_OPENSHIFT_TOKEN"

# Use the token in API calls
curl -H "Authorization: Bearer $OPENSHIFT_TOKEN" \
     http://localhost:8000/workspaces/admin-devspaces
```

#### Swagger UI Authentication

For testing via the interactive documentation:

1. **Open**: `http://localhost:8000/docs`
2. **Click**: 🔒 "Authorize" button (top right)
3. **Enter**: Your Bearer token (e.g., `sha256~...`)
4. **Click**: "Authorize"
5. **Test**: All endpoints will automatically include your token

### Example Usage

**Create IntelliJ Workspace:**
```bash
# Get your token first (if logged in)
TOKEN=$(oc whoami -t)

# OR use a valid token directly
export OPENSHIFT_TOKEN="YOUR_OPENSHIFT_TOKEN"

curl -X POST "http://localhost:8000/workspaces/intellij" \
     -H "Authorization: Bearer $OPENSHIFT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "namespace": "admin-devspaces",
       "git_repo": "https://github.com/spring-projects/spring-petclinic",
       "memory_limit": "8Gi",
       "cpu_limit": "2000m"
     }'
```

### Testing

```bash
# Run unit tests
source venv/bin/activate
python -m pytest test/ -v

# Run with coverage
python -m pytest test/ --cov=main --cov-report=html
```

### Postman Collection

Import the Postman collection from `docs/DevSpaces-Workspace-API.postman_collection.json` to test the API endpoints interactively.

## 📚 API Endpoints Tested

### DevWorkspace CRUD Operations

| Operation | Method | Endpoint | Status |
|-----------|--------|----------|--------|
| List Workspaces | GET | `/apis/workspace.devfile.io/v1alpha2/namespaces/{namespace}/devworkspaces` |  |
| Create Workspace | POST | `/apis/workspace.devfile.io/v1alpha2/namespaces/{namespace}/devworkspaces` |  |
| Get Workspace | GET | `/apis/workspace.devfile.io/v1alpha2/namespaces/{namespace}/devworkspaces/{name}` |  |
| Start/Stop Workspace | PATCH | `/apis/workspace.devfile.io/v1alpha2/namespaces/{namespace}/devworkspaces/{name}` |  |
| Delete Workspace | DELETE | `/apis/workspace.devfile.io/v1alpha2/namespaces/{namespace}/devworkspaces/{name}` |  |

### Chapter 8 Methodology

This repository implements the official Red Hat methodology from **Chapter 8: Integrating with OpenShift**:

- **DevWorkspace Custom Resources**: Each workspace is a Kubernetes custom resource
- **User Namespaces**: Workspaces created in user-specific namespaces (e.g., `admin-devspaces`)
- **Lifecycle Management**: Full CRUD operations using OpenShift APIs
- **Token Injection**: Automatic OpenShift user token injection into containers

### IDE Integration Approaches

**Full IDE Workspaces** (with IDE contributions):
- Creates `tools` + `che-gateway` containers
- Provides web-based IDE access

**JetBrains Gateway Workspaces** (template-based):
- Creates DevWorkspaceTemplate with IDE runtime
- Compatible with JetBrains Gateway desktop app
- Used by IntelliJ workspaces

## 🎯 IntelliJ Integration

### JetBrains Gateway Approach

IntelliJ integration works through **JetBrains Gateway**:

1. **Create DevWorkspace** using our script or API
2. **Download JetBrains Gateway** from [jetbrains.com/gateway](https://www.jetbrains.com/gateway/)
3. **Connect to workspace** using the workspace URL
4. **Gateway downloads and runs IntelliJ** in the cloud environment

### Workspace Requirements

Our IntelliJ workspaces include:
- **DevWorkspaceTemplate** with IntelliJ IDE runtime
- **Proper endpoint configuration** (port 8887, HTTPS)
- **Spring Petclinic project** pre-cloned
- **Universal Developer Image** for development tools

## 🔍 Troubleshooting

### Common Issues

1. **"Not logged in to OpenShift" or "Unauthorized" errors**
   - **Solution**: Use a valid token directly instead of `oc whoami -t`
   - **Test first**: `curl -k -H "Authorization: Bearer YOUR_OPENSHIFT_TOKEN" "https://api.cluster-k2ds9.k2ds9.sandbox2151.opentlc.com:6443/apis/user.openshift.io/v1/users/~"`
   - **If that works**: Use the same token with our API

2. **"IDE URL not received"**
   - **Scenario**: Workspace runs but no IDE URL generated
   - **Solution**: Use JetBrains Gateway for IntelliJ connection

3. **"Authentication failed"**
   - **Scenario**: Invalid credentials or expired token
   - **Solution**: Re-login to OpenShift cluster with `oc login`

4. **"Workspace creation failed"**
   - **Scenario**: API returns error during workspace creation
   - **Solution**: Check cluster resources and namespace permissions

### Getting Help

1. Check the logs in the DevSpaces UI
2. Verify cluster configuration with cluster administrator
3. Ensure you have proper permissions in the target namespace

## 🧪 Testing Results

![Workspace Creation](img/workspace-creation.png)
*IntelliJ workspace creation in progress*

![Final Result](img/final-result.png)
*Successful IntelliJ workspace creation and running workspace*

Our testing confirmed:

-  **API Endpoints Work**: All CRUD operations function correctly
-  **Workspace Creation**: DevWorkspaces are created successfully  
-  **Container Startup**: Workspace containers start and run
-  **Git Integration**: Repositories are cloned correctly
-  **IntelliJ Integration**: Workspaces compatible with JetBrains Gateway
-  **UI Integration**: Workspaces created via API appear in DevSpaces UI
-  **Multi-Container Support**: Complex workspaces with multiple containers work
-  **Persistent Storage**: PVCs and volume mounts function properly


## 📄 License

MIT License - see `LICENSE` file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Note**: This repository is for testing and educational purposes. Always follow your organization's security policies when working with OpenShift clusters.
