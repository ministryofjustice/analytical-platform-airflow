data "aws_caller_identity" "session" {
  provider = aws.session
}

data "aws_iam_session_context" "session" {
  provider = aws.session

  arn = data.aws_caller_identity.session.arn
}

data "aws_eks_cluster" "main" {
  provider = aws.analytical-platform-development-eu-west-1

  name = "development-aWrhyc0m"
}
