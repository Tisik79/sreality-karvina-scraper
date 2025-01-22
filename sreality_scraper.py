import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import json

class SrealityScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def get_google_drive_service(self):
        """Vytvoří službu Google Drive pomocí service account credentials"""
        try:
            print("Načítám Google credentials...")
            
            # Zkusíme nejprve načíst credentials z proměnné prostředí
            credentials_str = os.environ.get('GOOGLE_CREDENTIALS')
            if credentials_str:
                print("Credentials nalezeny v proměnné prostředí")
                credentials_info = json.loads(credentials_str)
            else:
                print("Credentials nenalezeny v proměnné prostředí, zkouším soubor credentials.json")
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError("Soubor credentials.json neexistuje")
                with open('credentials.json', 'r') as f:
                    credentials_info = json.load(f)
            
            print("Vytvářím service account credentials...")
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            print("Service account vytvořen, připojuji se ke Google Drive...")
            service = build('drive', 'v3', credentials=credentials)
            print("Připojení k Google Drive úspěšné")
            return service
            
        except Exception as e:
            print(f"Chyba při vytváření Google Drive služby: {e}")
            print(f"Typ chyby: {type(e).__name__}")
            return None

    def upload_to_drive(self, filename, folder_id=None):
        """Nahraje soubor na Google Drive do specifikované složky"""
        print(f"\nZačínám nahrávat soubor {filename} na Google Drive...")
        
        service = self.get_google_drive_service()
        if not service:
            print("Nelze nahrát soubor - služba Google Drive není dostupná")
            return None

        try:
            print(f"Připravuji metadata pro soubor...")
            file_metadata = {
                'name': filename,
                'parents': [folder_id] if folder_id else []
            }
            print(f"Vytvářím MediaFileUpload objekt...")
            media = MediaFileUpload(filename, 
                                  mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                  resumable=True)
            
            print(f"Začínám upload souboru...")
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            print(f'Soubor byl úspěšně nahrán na Google Drive s ID: {file.get("id")}')
            return file.get('id')
            
        except Exception as e:
            print(f"Chyba při nahrávání souboru na Google Drive: {e}")
            print(f"Typ chyby: {type(e).__name__}")
            if hasattr(e, 'content'):
                print(f"Odpověď serveru: {e.content}")
            return None

    # ... (zbytek kódu zůstává stejný) ...
