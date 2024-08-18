from pydantic import BaseModel


class CloudArchiveRequest(BaseModel):
    redirect_success_link: str
    redirect_fail_link: str
    archive_url: str
    gallery_name: str
    archive_type: str
    cloud_type: str


class CloudArchiveDoneRequest(BaseModel):
    cloud_type: str
    failed_photos: int
    archive_type: str
