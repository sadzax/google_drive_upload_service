import requests
import json
from urllib.parse import urlparse, urlencode, urlunparse
from app.logging_config import logger
from app.config import lite_gallery_links


class LiteGalleryStreamService:
    def __init__(self, url: str):
        """
        :param url: 'https://arch-d.lite.gallery/g/api/stream/858329/f9d24b1dfb81a1bfa215cc008f46f3d3?mod=web'
        """
        logger.info(f"Получена ссылка {url} для загрузки на Google Drive")
        try:
            url_serialized_items = self.convert_url_to_prod_json_list(url)
            raw_data = self.flatten_media_list(url_serialized_items)
            self.data = self.create_sorted_by_folders_hash(raw_data)
        except Exception as e:
            logger.error(f"Ошибка при обработки ссылки {url}, детали: {e}")
            raise


    @staticmethod
    def convert_url_to_prod_json_list(url: str):
        """
        Конвертирует url для получения сериализированного списка файлов
        :param url: e.g. 'https://arch-d.lite.gallery/g/api/stream/858329/f9d24b1dfb81a1bfa215cc008f46f3d3?mod=web'
        :return: e.g. 'https://app.litegallery.io/g/api/stream/858329/f9d24b1dfb81a1bfa215cc008f46f3d3?json=true'
        """
        parsed_url = urlparse(url)
        query_params = {'json': ['true']}
        new_query = urlencode(query_params, doseq=True)
        new_url = urlunparse(
            (parsed_url.scheme, lite_gallery_links.PROD_NETLOC, parsed_url.path, parsed_url.params, new_query, parsed_url.fragment))
        return str(new_url)


    @staticmethod
    def flatten_media_list(url: str):
        """
        Сериализация альбома
        :param url: e.g. 'https://app.litegallery.io/g/api/stream/858329/f9d24b1dfb81a1bfa215cc008f46f3d3?json=true'
        :return: [ ] массив с хэшами, в которых информация о файлах
        """
        try:
            logger.info(f"Сериализация альбома для загрузки по ссылке {url}")
            response = requests.get(url)
            json_string = response.text
            data = json.loads(json_string)
            # TODO нужна логика сохранения данных в модель uploads
            return data
        except Exception as e:
            logger.error(f"Ошибка при сериализации ссылки {url}, детали: {e}")
            raise


    @staticmethod
    def create_sorted_by_folders_hash(data: list):
        """
        Формирует данные для загрузки по директориям в хэш/словарь
        :param data: [ ] массив с хэшами, в которых информация о файлах
        :return: { }
        """
        res_data = {}
        for rec in data:
            folder_name, file_name = rec['name'].rsplit('/', 1) # Разделение по последнему слэшу
            rec['file_name'] = file_name
            res_data.setdefault(folder_name, []).append(rec) # Распределение массива в словарь с ключами - директориями
        logger.info(f"Распределение альбома для загрузки по {len(res_data)} директориям завершено")
        return res_data
