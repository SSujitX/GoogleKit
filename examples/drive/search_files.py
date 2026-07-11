"""Search Drive files example."""

from googlekit.gdrive import DriveClient

drive = DriveClient.from_oauth("client_secrets.json")
for f in drive.files.iterate(query="name contains 'report'"):
    print(f.name, f.id)
