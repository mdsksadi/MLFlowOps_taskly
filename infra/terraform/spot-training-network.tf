
resource "aws_security_group" "spot_training" {
  name        = "taskly-spot-training-sg"
  description = "Security group for Taskly EC2 Spot training"
  vpc_id      = "vpc-0214fbad4d53e3fa3"

  # No inbound rules: SSM access only
  # Outbound access for package installation and MLflow connectivity
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "taskly-spot-training-sg"
    Project = "Taskly"
  }
}

output "spot_training_security_group_id" {
  value = aws_security_group.spot_training.id
}
