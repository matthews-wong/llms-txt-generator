# Syncing your notes

Nimbus Notes keeps everything on disk first and syncs on your terms. Point it
at any S3-compatible bucket or a plain folder to back up and share notebooks.

## Choosing a backend

Any S3-compatible object store works, including MinIO for self-hosting.

## Conflict handling

Edits are merged per-block, so two devices rarely collide.
