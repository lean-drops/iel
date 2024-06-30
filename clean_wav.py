import os

def delete_non_mp4_files(directory):
    # Überprüfen, ob das Verzeichnis existiert
    if not os.path.exists(directory):
        print(f"Das Verzeichnis {directory} existiert nicht.")
        return

    # Durch das Verzeichnis iterieren
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Überprüfen, ob die Datei keine MP4-Datei ist
            if not file.lower().endswith('.mp4'):
                # Vollständigen Pfad zur Datei erstellen
                file_path = os.path.join(root, file)
                try:
                    # Datei löschen
                    os.remove(file_path)
                    print(f"Datei gelöscht: {file_path}")
                except Exception as e:
                    print(f"Fehler beim Löschen der Datei {file_path}: {e}")

# Beispielverwendung
directory_path = 'audio'  # Ersetze dies durch den Pfad zu deinem Verzeichnis
delete_non_mp4_files(directory_path)
