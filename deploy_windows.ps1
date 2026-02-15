$AWS_REGION="us-east-1"
$AWS_ACCOUNT_ID="816902390376"
$ECR_REPO_NAME="eduecosystem-backend"
$ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

Write-Host "Building Docker image..."
docker build -f Dockerfile.production -t $ECR_REPO_NAME .

Write-Host "Logging in to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

Write-Host "Tagging image..."
docker tag "${ECR_REPO_NAME}:latest" "${ECR_URI}/${ECR_REPO_NAME}:latest"

Write-Host "Pushing to ECR..."
docker push "${ECR_URI}/${ECR_REPO_NAME}:latest"

Write-Host "Done! App Runner will deploy automatically."
