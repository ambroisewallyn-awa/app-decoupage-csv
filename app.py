import streamlit as st
import csv
import re
import os
import sys
import zipfile
import io

st.title("Extracteur de fichiers XML depuis un CSV")
st.write("Importez votre fichier CSV contenant les données XML, puis téléchargez l'archive ZIP contenant tous les fichiers générés.")

# 1. Widget d'importation du fichier CSV
fichier_uploade = st.file_uploader("Choisissez votre fichier CSV", type=["csv"])

if fichier_uploade is not None:
    if st.button("Lancer le traitement et préparer le ZIP"):
        with st.spinner("Traitement en cours et création du ZIP..."):
            
            # Gestion de la limite de taille des champs CSV (sécurité Windows/gros volumes)
            max_int = sys.maxsize
            while True:
                try:
                    csv.field_size_limit(max_int)
                    break
                except OverflowError:
                    max_int = int(max_int / 10)

            # Utilisation d'un buffer en mémoire pour créer le fichier ZIP sans saturer le disque
            zip_buffer = io.BytesIO()
            
            # Lecture du fichier uploadé par Streamlit (converti en texte UTF-8)
            chaine_texte = io.TextIOWrapper(fichier_uploade, encoding='utf-8')
            lecteur_csv = csv.reader(chaine_texte)
            
            # Ignorer l'en-tête
            next(lecteur_csv, None)
            
            compteur = 1
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as fichier_zip:
                for ligne in lecteur_csv:
                    if not ligne:
                        continue
                        
                    xml_complet = ligne[0]
                    
                    # --- EXTRACTION DES DONNÉES ---
                    recherche_type = re.search(r"<marketmessagetype>(.*?)</marketmessagetype>", xml_complet)
                    msg_type = recherche_type.group(1) if recherche_type else "TypeInconnu"
                    
                    recherche_from = re.search(r"<fromdate>(.*?)</fromdate>", xml_complet)
                    from_date = recherche_from.group(1).split('T')[0] if recherche_from else "DateDebutInconnue"
                    
                    recherche_to = re.search(r"<todate>(.*?)</todate>", xml_complet)
                    to_date = recherche_to.group(1).split('T')[0] if recherche_to else "DateFinInconnue"

                    recherche_gsrn = re.search(r"<gsrn>(.*?)</gsrn>", xml_complet)
                    gsrn = recherche_gsrn.group(1) if recherche_gsrn else str(compteur)         
                    
                    # --- NETTOYAGE ---
                    def nettoyer_texte(texte):
                        return re.sub(r'[\\/*?:"<>|]', '', texte)

                    msg_type_propre = nettoyer_texte(msg_type)
                    from_date_propre = nettoyer_texte(from_date)
                    to_date_propre = nettoyer_texte(to_date)
                    gsrn_propre = nettoyer_texte(gsrn)
                    
                    # --- NOM DU FICHIER XML ---
                    nom_fichier = f"{msg_type_propre}_{from_date_propre}_au_{to_date_propre}_{gsrn_propre}.xml"
                    
                    # Écriture directe du contenu XML dans l'archive ZIP en mémoire
                    fichier_zip.writestr(nom_fichier, xml_complet.strip())
                    
                    compteur += 1

            nb_fichiers = compteur - 1
            st.success(f"Terminé ! {nb_fichiers} fichiers XML ont été générés et compressés.")

            # Remise du pointeur du buffer au début pour la lecture
            zip_buffer.seek(0)

            # 2. Bouton de téléchargement du fichier ZIP
            st.download_button(
                label="📥 Télécharger l'archive ZIP des XML",
                data=zip_buffer,
                file_name="fichiers_xml_extraits.zip",
                mime="application/zip"
            )