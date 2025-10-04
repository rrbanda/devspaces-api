# DevSpaces Examples

This directory contains example configurations and templates for testing DevSpaces DevWorkspace API.

## Files

### `sample-devworkspace.yaml`
A sample DevWorkspace YAML configuration that can be used with `oc apply` or as a reference for API calls.

### `config.example`
Environment variable template for configuring test scripts. Copy to `.env` and fill in your values.

### `get_token.sh`
Helper script to retrieve OAuth tokens from OpenShift clusters.

## Usage

### Using the Sample DevWorkspace

```bash
# Apply directly with oc
oc apply -f sample-devworkspace.yaml

# Or use as template for API calls
curl -X POST -H "Content-Type: application/json" \
  -d @sample-devworkspace.yaml \
  "$API_SERVER/apis/workspace.devfile.io/v1alpha2/namespaces/$NAMESPACE/devworkspaces"
```

### Using Configuration Template

```bash
# Copy the template
cp config.example .env

# Edit with your values
nano .env

# Use in scripts
source .env
```

### Getting OAuth Token

```bash
# Make executable
chmod +x get_token.sh

# Run with your cluster details
./get_token.sh
```

## Customization

All examples can be customized for your specific needs:

- **Namespace**: Change to your DevSpaces user namespace
- **Projects**: Modify Git repositories and project names
- **Components**: Adjust container images and resource limits
- **Environment Variables**: Add or modify environment variables

## Security Notes

- Never commit `.env` files with real credentials
- Use environment variables instead of hardcoded values
- Rotate tokens regularly
- Follow your organization's security policies
