#!/bin/bash

# SAM deployment script
# Usage: ./deploy.sh <name>
# Example: ./deploy.sh create_profile

if [ $# -eq 0 ]; then
    echo "Usage: $0 <name>"
    echo "Example: $0 create_profile"
    exit 1
fi

NAME="$1"
STACK_NAME="$(echo "$NAME" | tr '_' '-')-stack"

# Check functions first, then layers
IS_LAYER=false
if [ -d "AWS/lambda/functions/$NAME" ]; then
    YAML_PATH="AWS/lambda/functions/$NAME/*.yaml"
    echo "Found function: $NAME"
elif [ -d "AWS/lambda/layers/$NAME" ]; then
    YAML_PATH="AWS/lambda/layers/$NAME/*.yaml"
    IS_LAYER=true
    echo "Found layer: $NAME"
else
    echo "Error: Neither AWS/lambda/functions/$NAME nor AWS/lambda/layers/$NAME exists"
    exit 1
fi

echo "Deploying: $YAML_PATH"
echo "Stack name: $STACK_NAME"

sam deploy \
  --template-file $YAML_PATH \
  --capabilities CAPABILITY_IAM \
  --stack-name "$STACK_NAME" \
  --region us-east-1 \
  --s3-bucket livewell-deployment-bucket \
  --profile account2 \
  --force-upload

# Check if deployment was successful
if [ $? -eq 0 ]; then
    echo "Deployment successful!"
    # Only update versions when deploying layers
    if [ "$IS_LAYER" = true ]; then
        echo "Layer deployed successfully. Updating versions..."
        python3 ./auto_update_versions.py
    else
        echo "Function deployed successfully. No version update needed."
    fi
else
    echo "Deployment failed. Skipping version update."
    exit 1
fi