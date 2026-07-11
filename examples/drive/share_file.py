"""Share a Drive file example."""

from googlekit.gdrive import DriveClient

drive = DriveClient.from_oauth("client_secrets.json")
drive.permissions.share_user("FILE_ID", email="colleague@example.com", role="reader")
link = drive.permissions.create_shareable_link("FILE_ID")
print(link)
