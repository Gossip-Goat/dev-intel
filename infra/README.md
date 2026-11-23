# AWS layout (planned)

Everything in `ap-southeast-2` (Sydney) so data stays in Australia.

| Piece | Service |
| --- | --- |
| Raw zone | S3 bucket `dev-intel-raw`, versioned, private, Block Public Access on |
| Clean zone | RDS for PostgreSQL, migrations in `lake/migrations` |
| Jobs (scrape, extract, inquiry sync) | ECS Fargate scheduled tasks from one container image |
| Schedules | EventBridge Scheduler |
| Secrets (Anthropic key, mailbox credentials) | Secrets Manager |
| Analysis | Athena over S3 exports, or QuickSight on RDS |

Not provisioned yet. Terraform will go here once the AWS account is known.
