provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile # always the named profile, never the default

  # Refuse to run against any other account (e.g. a personal default profile)
  allowed_account_ids = [var.account_id]

  default_tags {
    tags = {
      qut-username = var.qut_username
      purpose      = var.purpose
      project      = "hookd"
    }
  }
}
