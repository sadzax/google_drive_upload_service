import mimetypes


class FileMetadataService:
    @staticmethod
    def get_mime_type(file_name: str) -> str:
        """
        Возвращает первый элемент кортежа mime_type (или 'application/octet-stream', если тип не найден)
        :param file_name: строка "имя файла" с расширением
        :return: строка, MIME-тип файла на основе его расширения
        Например, 'image/jpeg' для "*.jpg", 'video/quicktime' для "*.mov" и т.д.
        """
        mime_type = mimetypes.guess_type(file_name)

        return mime_type[0] or 'application/octet-stream'


    @staticmethod
    def get_file_metadata(file_name: str, folder_id: str = None) -> dict:
        """
        :param file_name: имя файла, строка
        :param folder_id: необязательный аргумент, ID директории в Google Drive, куда нужно поместить файл
        Формат folder_id = '1lVeI-2cVeMaYMVeQnhiR6l53xCT8E168'
        :return: хэш/словарь file_metadata - метаданные файла для формирования body в запросе сервиса Google Drive на создание файла
        """
        file_metadata = {'name': file_name}

        if folder_id:
            file_metadata['parents'] = [folder_id]

        return file_metadata
