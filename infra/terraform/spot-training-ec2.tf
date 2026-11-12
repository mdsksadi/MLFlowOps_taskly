
# Ubuntu 22.04 AMI for EC2 training
data "aws_ami" "ubuntu_training" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 Spot training instance
resource "aws_instance" "spot_training" {
  ami                         = data.aws_ami.ubuntu_training.id
  instance_type               = "t3.medium"
  subnet_id                   = "subnet-02cb311c9da108228"
  vpc_security_group_ids      = [aws_security_group.spot_training.id]
  iam_instance_profile        = aws_iam_instance_profile.spot_training.name
  associate_public_ip_address = false

  instance_market_options {
    market_type = "spot"

    spot_options {
      spot_instance_type             = "one-time"
      instance_interruption_behavior = "terminate"
    }
  }

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    encrypted             = true
    delete_on_termination = true
  }

  tags = {
    Name    = "taskly-spot-training"
    Project = "Taskly"
    Purpose = "ML Model Training"
  }
}

output "spot_training_instance_id" {
  value = aws_instance.spot_training.id
}

output "spot_training_private_ip" {
  value = aws_instance.spot_training.private_ip
}
