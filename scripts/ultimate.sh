#!/bin/bash
#
# IntelliJ IDEA Ultimate Workspace with editorsDownloadUrls
#

set -e

API_SERVER=$(oc whoami --show-server)
TOKEN=$(oc whoami -t)

if [ -z "$TOKEN" ]; then
    echo "ERROR: Not logged in to OpenShift"
    exit 1
fi

DEVSPACES_NS="openshift-operators"
EDITOR_ID="che-incubator/che-idea-server/latest"
INTELLIJ_URL="https://download.jetbrains.com/idea/ideaIU-2025.2.2.tar.gz"

echo "=========================================="
echo "IntelliJ IDEA Ultimate Workspace Creator"
echo "=========================================="
echo ""

# Step 1: Configure editorsDownloadUrls
echo "=== Step 1: Configuring editorsDownloadUrls ==="
curl -sk -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/merge-patch+json" \
  "$API_SERVER/apis/org.eclipse.che/v2/namespaces/$DEVSPACES_NS/checlusters/devspaces" \
  -d '{
    "spec": {
      "devEnvironments": {
        "editorsDownloadUrls": [
          {
            "editor": "'"$EDITOR_ID"'",
            "url": "'"$INTELLIJ_URL"'"
          }
        ]
      }
    }
  }' | jq -r 'if .metadata.name then "✓ Configured" else "✗ FAILED" end'

sleep 5
echo ""

# Step 2: Get user input
read -p "User namespace [admin-devspaces]: " NS
NS=${NS:-admin-devspaces}

WS_NAME="intellij-ultimate-$(date +%s | tail -c 6)"

echo "Creating workspace: $WS_NAME"
echo ""

# Step 3: Create DevWorkspace using dashboard API for editor
echo "=== Step 2: Creating DevWorkspace ==="
curl -sk -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$API_SERVER/apis/workspace.devfile.io/v1alpha2/namespaces/$NS/devworkspaces" \
  -d '{
    "apiVersion": "workspace.devfile.io/v1alpha2",
    "kind": "DevWorkspace",
    "metadata": {
      "name": "'"$WS_NAME"'",
      "namespace": "'"$NS"'"
    },
    "spec": {
      "routingClass": "che",
      "started": true,
      "contributions": [{
        "name": "ide",
        "uri": "http://devspaces-dashboard.'"$DEVSPACES_NS"'.svc:8080/dashboard/api/editors/devfile?che-editor='"$EDITOR_ID"'"
      }],
      "template": {
        "projects": [{
          "name": "spring-petclinic",
          "git": {
            "remotes": {"origin": "https://github.com/spring-projects/spring-petclinic"}
          }
        }],
        "components": [{
          "name": "tools",
          "container": {
            "image": "quay.io/devfile/universal-developer-image:ubi8-latest",
            "memoryLimit": "4Gi",
            "memoryRequest": "1Gi"
          }
        }]
      }
    }
  }' | jq -r 'if .metadata.name then "✓ Created: " + .metadata.name else "✗ FAILED" end'

echo ""
echo "=========================================="
echo "Monitor: oc get devworkspace $WS_NAME -n $NS --watch"
echo "=========================================="