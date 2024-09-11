import io
import requests
from fastapi import HTTPException
from urllib.parse import urlparse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from ..logging_config import logger


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

        logger.info(f"Установлено соединение с пользователем через токен {creds_hash['token']}")
        # TODO Обработка исключений
        self.drive_service = build('drive', 'v3', credentials=creds)


    def upload_file(self, file_path: str, file_metadata: dict, file_mimetype: str):
        """
        :param file_path: путь к файлу формата 'folder/file.ext' или 'https://up-d.lite.gallery/litepr-m/uploads/image/image/49851961/Test_001.jpg'
        :param file_metadata: словарь с ключами 'name': str, 'parents': array
        name - имя файла, которое будет присвоено на Google Drive диске
        parents - ID директорий Google Drive диска, куда будет помещён файл. 
        Формат элемента списка '1lVeI-2cVeMaYMVeQnhiR6l53xCT8E168'
        :param file_mimetype: конечный тип данных формата 'image/jpeg' | 'video/quicktime' и т.д.
        :return: ID созданного файла (строка)
        """
        logger.info(f"Начало загрузки файла: {file_path} на Google Drive с MIME-типом {file_mimetype}, параметры: {file_metadata}")
        media = self.media_tool(file_path=file_path, file_mimetype=file_mimetype) # TODO определиться с источником файла (если ссылка)

        try:
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            logger.info(f"Загрузка файла: {file_path} на Google Drive завершена")
            return file.get('id')
        except Exception as e:
            logger.error(f"Ошибка при загрузке файла {file_path}: {e}")
            raise


    @staticmethod
    def media_tool(file_path: str, file_mimetype: str):
        """
        :param file_path: путь к файлу формата 'folder/file.ext' или 'https://up-d.lite.gallery/litepr-m/uploads/image/image/49851961/Test_001.jpg'
        :param file_mimetype: конечный тип данных формата 'image/jpeg' | 'video/quicktime' и т.д.
        :return: объект класса MediaFileUpload или MediaIoBaseUpload
        """
        if urlparse(file_path).scheme in ['https', 'http']:
            try:
                response = requests.get(file_path, stream=True)
                if response.status_code == 200:
                    file_stream = io.BytesIO()
                    for chunk in response.iter_content(1024):
                        file_stream.write(chunk)
                    file_stream.seek(0)  # Сбрасываем указатель на начало потока
                else:
                    raise HTTPException(status_code=400, detail="Не удалось скачать файл.")
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))
            return MediaIoBaseUpload(file_stream, mimetype=file_mimetype, chunksize=1024*1024, resumable=True)
        else:
            return MediaFileUpload(file_path, mimetype=file_mimetype)


    def create_folder(self, folder_name: str, parent_id: str = None):
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id] if parent_id else []
        }

        folder = self.drive_service.files().create(body=file_metadata, fields='id').execute()

        logger.info(f"Создана папка: {folder_name} в Google Drive")
        # TODO Обработка исключений
        return folder.get('id')
