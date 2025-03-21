def read_active_user(self):
    try:
        with open(self.user_file, 'rb') as f:
            raw_data = f.read()
            # Essayer plusieurs encodages courants
            encodings = ['utf-8', 'latin-1', 'utf-16', 'ascii']
            for encoding in encodings:
                try:
                    return raw_data.decode(encoding)
                except UnicodeDecodeError:
                    continue
            # Si aucun encodage ne fonctionne, logger l'erreur et retourner None
            logger.error(f"Aucun encodage valide trouvé pour le fichier utilisateur")
            return None
    except Exception as e:
        logger.error(f"Erreur critique lors de la lecture de l'utilisateur actif: {str(e)}")
        return None 