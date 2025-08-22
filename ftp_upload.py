from ftplib import FTP

def connect_to_ftp(ftp_server, ftp_username, ftp_password):
    try:
        ftp = FTP(ftp_server)
        ftp.login(user=ftp_username, passwd=ftp_password)
        ftp.set_pasv(True)  # Použijte pasivní mód, pokud máte problémy s firewallem
        return ftp
    except Exception as e:
        print(f"Chyba při připojení k FTP serveru: {e}")
        return None

def list_ftp_directory(ftp):
    try:
        print("Obsah aktuální cesty na FTP serveru:")
        ftp.retrlines('LIST')
    except Exception as e:
        print(f"Chyba při výpisu obsahu cesty: {e}")

def upload_file_to_ftp(ftp, local_file_path, remote_file_path):
    try:
        with open(local_file_path, 'rb') as file:
            ftp.storbinary(f'STOR {remote_file_path}', file)
        print(f"Soubor {local_file_path} byl úspěšně nahrán na FTP server jako {remote_file_path}")
    except Exception as e:
        print(f"Chyba při nahrávání souboru: {e}")

def change_ftp_directory(ftp, directory_path):
    try:
        ftp.cwd(directory_path)
        print(f"Přepnuto do cesty: {directory_path}")
    except Exception as e:
        print(f"Chyba při přepnutí cesty: {e}")
