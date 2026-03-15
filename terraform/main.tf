resource "aws_s3_bucket" "example" {
  bucket = "my-secure-bucket"
  acl    = "private"

  versioning {
    enabled = true
  }
}
