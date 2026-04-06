#!/bin/bash

# Exit on error
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Load environment variables from .env in the root
if [ -f ../.env ]; then
  # Read .env file, ignore comments, and export variables
  export $(grep -v '^#' ../.env | xargs)
fi

PROJECT_ID=${PROJECT_ID:-your-project-id}
GCP_REGION=${GCP_REGION:-us-central1}
GCP_REPOSITORY=${GCP_REPOSITORY:-daystar-repo}
IMAGE_NAME=${IMAGE_NAME:-daystar-test-app}
TAG=${TAG:-latest}

FULL_IMAGE_NAME="${GCP_REGION}-docker.pkg.dev/${PROJECT_ID}/${GCP_REPOSITORY}/${IMAGE_NAME}"

echo "Building Docker image for test app..."
docker build -t $IMAGE_NAME:$TAG .
docker tag $IMAGE_NAME:$TAG $FULL_IMAGE_NAME:$TAG

echo "Pushing image to Artifact Registry..."
docker push $FULL_IMAGE_NAME:$TAG

echo "Build and push complete."
