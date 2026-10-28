from supabase import create_client, Client
from kckservices.config import settings

# Service-role client: verifies tokens and uploads to Storage (server side only!)
supabase_admin: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key
)

def new_anon_client() -> Client:
    # A fresh client per login/register so one user's session never leaks into another request
    return create_client(settings.supabase_url, settings.supabase_anon_key)
