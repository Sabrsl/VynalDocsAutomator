def open_document(self, doc_id):
    try:
        # Implémentation de base
        document = self.model.get_document(doc_id)
        if document:
            logger.info(f"Ouverture du document {doc_id}")
            return document
        else:
            logger.warning(f"Document {doc_id} non trouvé")
            return None
    except Exception as e:
        logger.error(f"Erreur lors de l'ouverture du document: {str(e)}")
        return None

def filter_documents(self, filters):
    try:
        # Implémentation de base
        filtered_docs = self.model.filter_documents(filters)
        logger.info(f"Filtrage des documents avec {len(filters)} critères")
        return filtered_docs if filtered_docs else []
    except Exception as e:
        logger.error(f"Erreur lors du filtrage des documents: {str(e)}")
        return [] 