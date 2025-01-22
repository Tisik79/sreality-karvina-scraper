
# ... (začátek souboru zůstává stejný) ...

    def get_google_drive_service(self):
        """Vytvoří službu Google Drive pomocí service account credentials"""
        try:
            print("Načítám Google credentials...")
            credentials_json = json.loads(os.environ.get('GOOGLE_CREDENTIALS', '{}'))
            print("Credentials načteny, vytvářím service account...")
            
            credentials = service_account.Credentials.from_service_account_info(
                credentials_json,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            print("Service account vytvořen, připojuji se ke Google Drive...")
            
            service = build('drive', 'v3', credentials=credentials)
            print("Připojení k Google Drive úspěšné")
            return service
        except Exception as e:
            print(f"Chyba při vytváření Google Drive služby: {e}")
            if os.environ.get('GOOGLE_CREDENTIALS'):
                print("Credentials jsou nastaveny v prostředí")
            else:
                print("GOOGLE_CREDENTIALS není nastaven v prostředí")
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
                fields='id,webViewLink'
            ).execute()
            
            print(f'Soubor byl úspěšně nahrán na Google Drive')
            print(f'ID souboru: {file.get("id")}')
            print(f'Odkaz na soubor: {file.get("webViewLink")}')
            return file.get('id')
            
        except Exception as e:
            print(f"Chyba při nahrávání souboru na Google Drive: {e}")
            print(f"Typ chyby: {type(e).__name__}")
            if hasattr(e, 'content'):
                print(f"Odpověď serveru: {e.content}")
            return None

# ... (zbytek souboru zůstává stejný) ...
