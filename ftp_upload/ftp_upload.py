from ftplib import FTP
from ftplib import FTP_TLS
import re
import ssl

def connect_to_ftp(ftp_server, ftp_username, ftp_password):
    try:
        ftp = FTP(ftp_server)
        ftp.login(user=ftp_username, passwd=ftp_password)
        ftp.set_pasv(True)  # pasivní mód
        return ftp
    except Exception as e:
        print(f"Chyba při připojení k FTP serveru: {e}")
        return None

def connect_to_ftps(ftp_server, ftp_username, ftp_password, port=21):
    try:
        context = ssl.create_default_context()
        ftp = FTP_TLS(context=context)  # šifrovaný řídicí kanál
        ftp.connect(ftp_server, port, timeout=30)
        ftp.login(user=ftp_username, passwd=ftp_password)
        # ftp.prot_p()      # šifrování datového kanálu > Chyba při nahrávání souboru: 522 SSL connection failed; session reuse required: see require_ssl_reuse option in vsftpd.conf man page
        ftp.prot_c()        # nešifrovaný datový kanál
        ftp.set_pasv(True)
        print(f"Pripojeno k FTPS serveru: {ftp_server}")
        return ftp
    except Exception as e:
        print(f"Chyba při připojení k FTPS serveru: {e}")
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
            ftp.storbinary(f"STOR {remote_file_path}", file)
        print(f"Soubor {local_file_path} byl úspěšně nahrán na FTP server jako {remote_file_path}")
    except Exception as e:
        print(f"Chyba při nahrávání souboru: {e}")

def change_ftp_directory(ftp, directory_path):
    try:
        ftp.cwd(directory_path)
        print(f"Přepnuto do cesty: {directory_path}")
    except Exception as e:
        print(f"Chyba při přepnutí cesty: {e}")

def build_year_to_filename_map(ftp, directory_path=None):
    """
    Načte seznam souborů (v aktuální cestě nebo v directory_path),
    vyfiltruje soutez_vysledky_XXXX.json a vrátí dict: {year(int): filename(str)}.
    """
    pattern = re.compile(r"^soutez_vysledky_(\d{4})\.json$")

    # Volitelné přepnutí do cílové složky
    if directory_path:
        try:
            ftp.cwd(directory_path)
        except Exception as e:
            print(f"Chyba při přepnutí cesty na {directory_path}: {e}")
            return {}

    try:
        # nlst() vrací seznam jmen souborů (některé servery mohou vracet i relativní cesty)
        names = ftp.nlst()
    except Exception as e:
        print(f"Chyba při načítání seznamu souborů (NLST): {e}")
        return {}

    year_to_file = {}
    duplicates = []

    for name in names:
        # některé FTP servery vrací 'dir/filename', vezmeme jen poslední segment
        base = name.split("/")[-1]
        m = pattern.match(base)
        if not m:
            continue

        year = int(m.group(1))

        if year in year_to_file:
            duplicates.append((year, base))
            continue

        year_to_file[year] = base

    if duplicates:
        # volitelně: logování duplicit
        print("Pozor: nalezeny duplicitní roky (ponechán první výskyt):")
        for year, fname in duplicates:
            print(f"  rok={year}, soubor={fname}")

    return year_to_file
