terraform -chdir=modules init 
terraform -chdir=modules apply -auto-approve 

echo $(terraform -chdir=modules output -raw alb)
$account_id = $(terraform -chdir=modules output -raw account_id)
 


aws ecr get-login-password --region sa-east-1 | docker login --username AWS --password-stdin "$account_id.dkr.ecr.sa-east-1.amazonaws.com"
docker build -t web-app .
docker tag web-app:latest "$account_id.dkr.ecr.sa-east-1.amazonaws.com/web-app:latest"
docker push "$account_id.dkr.ecr.sa-east-1.amazonaws.com/web-app:latest"

pause