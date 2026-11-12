resource "aws_iam_role" "spot_training" {
  name = "taskly-spot-training-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "spot_training_ssm" {
  role       = aws_iam_role.spot_training.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "spot_training_s3" {
  name = "taskly-spot-training-s3-access"
  role = aws_iam_role.spot_training.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = "arn:aws:s3:::${var.artifact_bucket_name}"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "arn:aws:s3:::${var.artifact_bucket_name}/*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "spot_training" {
  name = "taskly-spot-training-profile"
  role = aws_iam_role.spot_training.name
}

output "spot_training_instance_profile" {
  value = aws_iam_instance_profile.spot_training.name
}
