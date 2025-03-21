from document_processor import DocumentProcessor

def main():
    # Exemple de document avec variables
    document_text = """
    CONTRAT DE PRESTATION
    
    Entre les soussignés :
    
    <<entreprise>>, représentée par <<nom>>
    Adresse : <<adresse>>
    Email : <<email>>
    Téléphone : <<telephone>>
    
    Il a été convenu ce qui suit :
    
    Article 1 - Montant
    Le montant total de la prestation s'élève à <<montant>> <<devise>>.
    
    Article 2 - Date de réalisation
    La prestation sera réalisée le <<date>>.
    
    Fait à <<lieu>>, le <<date_signature>>
    
    Signature : _________________
    """

    # Création d'une instance du processeur de documents
    processor = DocumentProcessor()

    # Demande du nom du client
    client_name = input("Entrez le nom du client : ")

    # Traitement du document
    processed_document, missing_variables = processor.process_document(document_text, client_name)

    # Si des variables sont manquantes, les demander à l'utilisateur
    if missing_variables:
        print("\nCertaines informations sont manquantes. Veuillez les compléter :")
        user_inputs = {}
        for var in missing_variables:
            value = input(f"Entrez {var} : ")
            user_inputs[var] = value
        
        # Mise à jour finale du document avec les variables manquantes
        final_document = processor.replace_variables_in_document(processed_document, user_inputs)
    else:
        final_document = processed_document

    # Affichage du résultat
    print("\n=== DOCUMENT FINAL ===")
    print(final_document)

if __name__ == "__main__":
    main() 