terraform {
  required_version = ">= 1.16.0, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region  = "us-east-1"
  profile = "devsecops-terraform"
}

resource "aws_ecr_repository" "app" {
  name                 = "devsecops-cicd-platform"
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = {
    Name        = "devsecops-cicd-platform"
    Project     = "DevSecOps-CICD-Platform"
    ManagedBy   = "Terraform"
    Environment = "development"
  }
}
