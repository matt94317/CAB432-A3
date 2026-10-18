terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Local state for now (*.tfstate is gitignored). To share state, create the
  # bucket once, uncomment, then run `terraform init -migrate-state`.
  # use_lockfile gives S3-native locking (no DynamoDB table needed).
  #
  # backend "s3" {
  #   bucket       = "n12191434-a3-hookd-tfstate"
  #   key          = "cab432/terraform.tfstate"
  #   region       = "ap-southeast-2"
  #   profile      = "CAB432"
  #   use_lockfile = true
  #   encrypt      = true
  # }
}
