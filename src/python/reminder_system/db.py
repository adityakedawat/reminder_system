import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv('SUPABASE_SECRET_KEY')
url = os.getenv('SUPABASE_URL')

from dataclasses import dataclass
from supabase import create_client, Client


class DBAdapter:
    def __init__(self):
        self.client: Client = create_client(url, key)