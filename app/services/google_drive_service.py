import io
from datetime import datetime
import requests
from fastapi import HTTPException
from urllib.parse import urlparse
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
from app.logging_config import logger
from app.config import lite_gallery_links


class GoogleDriveService:
    def __init__(self, creds_hash: dict):
        """
        Создаёт инстанс ресурса
        :param creds_hash: для создания объекта Credentials нужен хэш/словарь с аналогичной схемой ключей
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
        self.initial_folder_id = self.create_initial_folder()


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
            # Основной кейс - загрузка файла в качестве стрима с прямой ссылки https
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
            # Дополнительный кейс - загрузка файла с локальной машины
            return MediaFileUpload(file_path, mimetype=file_mimetype)


    def create_folder(self, folder_name: str, parent_id: str = None):
        """
        :param folder_name: имя директории (Google Drive не валидирует имена на уникальность, можно создавать одинаковые)
        :param parent_id: id родительской директории, в которой надо создать новую
        :return: id созданной директории в Google Drive
        """
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id] if parent_id else []
        }

        folder = self.drive_service.files().create(body=file_metadata, fields='id').execute()

        logger.info(f"Создана директория: {folder_name} в Google Drive с номером {folder.get('id')}")
        if parent_id:
            logger.info(f"Созданная директория {folder_name} является дочерней для {parent_id}")
        # TODO Обработка исключений
        return folder.get('id')


    def create_initial_folder(self):
        """
        При подключении создаётся директория в Google Drive по имени сервиса + таймстампу
        :return: id созданной директории в Google Drive
        """
        rename_mapper = str.maketrans({':': '_', ' ': '_'})
        initial_folder_name = lite_gallery_links.SERVICE_NAME + "_export_" + str(datetime.now())
        logger.info(f"Установление соединения и создание ")
        return self.create_folder(folder_name=initial_folder_name.translate(rename_mapper))
