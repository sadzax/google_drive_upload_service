from google_auth_oauthlib.flow import Flow
from app.config import settings


def start_google_auth(request):
    flow = Flow.from_client_secrets_file(
        'client_secrets.json',
        scopes=['https://www.googleapis.com/auth/drive.file']
    )
    flow.redirect_uri = settings.GOOGLE_REDIRECT_URI

    authorization_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    return authorization_url
