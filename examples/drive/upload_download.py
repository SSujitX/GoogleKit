"""Short Drive examples (placeholder IDs — no secrets)."""

from googlekit.gdrive import DriveClient

# Replace with your OAuth client secrets path.
drive = DriveClient.from_oauth("client_secrets.json", token_path="token.json")

# Upload then download
uploaded = drive.files.upload_path("report.pdf")
assert uploaded is not None
downloaded = drive.files.download_path(uploaded.file.id, "report-copy.pdf")
print("downloaded", downloaded.path)
