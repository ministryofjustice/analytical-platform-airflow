EKS_CLUSTER_NAME="${1}"

unset $(env | awk -F= '/^AWS_/ {print $1}')
AWS_SSO_FILE_PASSWORD=a7b3104e753a0d5e70ed2548dfe78dcc280605fd8bdef638ac6694e10c891238
aws-sso login
aws-sso exec --profile $EKS_CLUSTER_NAME:platform-engineer-admin -- aws eks get-token --cluster-name "${EKS_CLUSTER_NAME}"
