from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload

creds = service_account.Credentials.from_service_account_file(
    'path/to/your/json/key.json',
    scopes=['https://www.googleapis.com/auth/drive']
)

drive_service = build('drive', 'v3', credentials=creds)

file_metadata = {
    'name': 'MyFile.txt',  
    'parents': ['<folder_id>']  # ID of the folder where you want to upload
}
file_path = 'path/to/your/local/file.txt'

media = MediaFileUpload(file_path, mimetype='text/plain')

file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()