# Google Cloud layout (planned)

Everything in `australia-southeast1` (Sydney) so data stays in Australia.

| Piece | Service |
| --- | --- |
| Raw zone | Cloud Storage bucket `dev-intel-raw`, versioned, private |
| Clean zone | Cloud SQL for PostgreSQL, migrations in `lake/migrations` |
| Jobs (scrape, extract, inquiry sync) | Cloud Run jobs |
| Schedules | Cloud Scheduler |
| Secrets (Anthropic key, mailbox credentials) | Secret Manager |
| Analysis | BigQuery federated queries over Cloud SQL, or Looker Studio |

Not provisioned yet. Terraform will go here once the project ID is known.
