#!/bin/bash
# Deploy Backend to AWS ECR + App Runner
# Run this script from the backend directory

# Configuration - UPDATE THESE VALUES
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="816902390376"  # From your ECR role ARN
ECR_REPO_NAME="eduecosystem-backend"  # Change if different

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t $ECR_REPO_NAME .

# Login to AWS ECR
echo "🔑 Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Tag the image
echo "🏷️ Tagging image..."
docker tag $ECR_REPO_NAME:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

# Push to ECR
echo "📤 Pushing to ECR..."
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME:latest

echo "✅ Done! App Runner will automatically deploy the new image."
echo "⏳ Wait 5-10 minutes for deployment to complete."
