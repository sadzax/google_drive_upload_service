from pydantic import BaseModel


class UrlStreamUpload(BaseModel):
    crc: str
    filesize: int
    name: str
    url: str
    data_id: int
