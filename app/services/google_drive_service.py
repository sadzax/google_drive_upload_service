from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class GoogleDriveService:
    def __init__(self, creds_hash: dict):
        """
        :param creds_hash: для создания объекта Credentials нужен хэш/словарь с аналогичной схемой ключей
        создаёт инстанс ресурса
        """
        creds = Credentials(
            token=creds_hash['token'],
            refresh_token=creds_hash['refresh_token'],
            token_uri=creds_hash['token_uri'],
            client_id=creds_hash['client_id'],
            client_secret=creds_hash['client_secret'],
        )

        # TODO Обработка исключений
        self.drive_service = build('drive', 'v3', credentials=creds)

    def upload_file(self, file_path: str, file_metadata: dict, file_mimetype: str):
        """

        :param file_path: путь к файлу формата 'folder/file.ext'
        :param file_metadata: словарь с ключами 'name': str, 'parents': array
        name - имя файла, которое будет присвоено на Google Drive диске
        parents - ID директорий Google Drive диска, куда будет помещён файл. 
        Формат элемента списка '1lVeI-2cVeMaYMVeQnhiR6l53xCT8E168'
        :param file_mimetype: конечный тип данных формата 'image/jpeg' | 'video/quicktime' и т.д.
        :return: ID созданного файла (строка)
        """
        media = MediaFileUpload(file_path, mimetype=file_mimetype) # TODO определиться с источником файла (если ссылка)
        
        file = self.drive_service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id'
        ).execute()
        
        # TODO Обработка исключений
        return file.get('id')

    def create_folder(self, folder_name: str, parent_id: str = None):
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id] if parent_id else []
        }

        folder = self.drive_service.files().create(body=file_metadata, fields='id').execute()

        # TODO Обработка исключений
        return folder.get('id')
