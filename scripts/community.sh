#!/bin/bash

# IntelliJ IDEA DevWorkspace Creation via API
# This script creates a fully functional IntelliJ workspace using OpenShift APIs

API_SERVER=$(oc whoami --show-server)
TOKEN=$(oc whoami -t)

if [ -z "$TOKEN" ]; then
    echo "ERROR: Not logged in to OpenShift"
    exit 1
fi

read -p "Namespace [admin-devspaces]: " NS
NS=${NS:-admin-devspaces}

WS_NAME="intellij-$(date +%s | tail -c 6)"
TEMPLATE_NAME="${WS_NAME}-ide"

echo "Creating IntelliJ workspace: $WS_NAME"

# Step 1: Create DevWorkspaceTemplate with IntelliJ IDE
curl -sk -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$API_SERVER/apis/workspace.devfile.io/v1alpha2/namespaces/$NS/devworkspacetemplates" \
  -d '{
    "apiVersion": "workspace.devfile.io/v1alpha2",
    "kind": "DevWorkspaceTemplate",
    "metadata": {
      "name": "'$TEMPLATE_NAME'",
      "namespace": "'$NS'"
    },
    "spec": {
      "components": [
        {
          "name": "che-idea-runtime",
          "container": {
            "image": "quay.io/che-incubator/che-idea:next",
            "memoryLimit": "8Gi",
            "memoryRequest": "2Gi",
            "cpuLimit": "2000m",
            "cpuRequest": "500m",
            "endpoints": [
              {
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
              }
            ]
          }
        }
      ]
    }
  }' | jq -r '.metadata.name // "FAILED"'

sleep 2

# Step 2: Create DevWorkspace
curl -sk -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$API_SERVER/apis/workspace.devfile.io/v1alpha2/namespaces/$NS/devworkspaces" \
  -d '{
    "apiVersion": "workspace.devfile.io/v1alpha2",
    "kind": "DevWorkspace",
    "metadata": {
      "name": "'$WS_NAME'",
      "namespace": "'$NS'"
    },
    "spec": {
      "routingClass": "che",
      "started": true,
      "contributions": [
        {
          "name": "ide",
          "kubernetes": {"name": "'$TEMPLATE_NAME'"}
        }
      ],
      "template": {
        "projects": [{
          "name": "petclinic",
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
  }' | jq -r '.metadata.name // "FAILED"'

echo
echo "Workspace created: $WS_NAME"
echo "Check Dev Spaces dashboard for URL"