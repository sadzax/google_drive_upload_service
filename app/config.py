import os
from dotenv import load_dotenv


load_dotenv() # для поиска .env


class Settings:
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
    SCOPES = [os.getenv("GOOGLE_DRIVE_SCOPE")]


settings = Settings()


class GoogleLinks:
    USER_TOKEN_URL = os.getenv("USER_TOKEN_URL")
    GRANT_TYPE = os.getenv("GRANT_TYPE")


google_links = GoogleLinks()


class LiteGalleryEnvs:
    SERVICE_NAME = os.getenv("SERVICE_NAME")
    PROD_NETLOC = os.getenv("PROD_NETLOC")


lite_gallery_links = LiteGalleryEnvs()


class JavaScriptSettings:
    GOOGLE_PLATFORM_LIBRARY_SCRIPT = '<script src="https://apis.google.com/js/platform.js" async defer></script>'

    @staticmethod
    def google_signin_client_id():
        return '<meta name=\"google-signin-client_id\" content=\"' + str(Settings.GOOGLE_CLIENT_ID) + '.apps.googleusercontent.com\">'
