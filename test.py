import csv
import os.path
import struct
import io
import xml.etree.ElementTree as ET

myxmlpath = "E:\\StarFab_exports\\Data\\Libs\\GameAudio\\SC_DX_PU_VWARRIORS_Voice_Bank.xml"
bnk_path_hhh = "E:\\StarFab_exports\\Data\\Sounds\\wwise\\English(US)\\DX_PU_GEN_CIVILIANS_Voice_Bank.bnk"

def parse_bnk(file_path):
    final_results = {}
    with open(file_path, "rb") as f:
        while True:
            header = f.read(4)
            if not header:
                break  # Fin du fichier

            # On récupère le nom du chunk (ex: BKHD)
            chunk_name = header.decode('ascii')

            # On lit la taille du chunk (Entier 32-bit, Little-Endian)
            chunk_size = struct.unpack('<I', f.read(4))[0]

            print(f"Chunk trouvé : {chunk_name} | Taille : {chunk_size} octets")

            if chunk_name == "DIDX":
                # On pourrait ici boucler pour lire chaque entrée de 12 octets
                # data_index = f.read(chunk_size)
                pass

            if chunk_name == "HIRC":
                links = parse_hirc_links(f, chunk_size)
                resolved_map  = resolve_hierarchy(links)
                final_results.update(resolved_map)

            # On saute à la section suivante
            f.seek(chunk_size, 1)

        return final_results

def get_type_name(t):
    mapping = {2: "Sound", 3: "Action", 4: "Event", 5: "Container", 6: "Switch"}
    return mapping.get(t, "Unknown")

def parse_hirc_links(f, chunk_size):
    # Lecture du nombre d'objets
    num_objs = struct.unpack('<I', f.read(4))[0]
    links = {"events": {}, "actions": {}, "sounds": {}}
    print(f"Nombre d'objets HIRC : {num_objs}")

    for _ in range(num_objs):
        obj_type = struct.unpack('B', f.read(1))[0]
        obj_size = struct.unpack('<I', f.read(4))[0]
        obj_id = struct.unpack('<I', f.read(4))[0]

        # On récupère le contenu de l'objet (moins l'ID déjà lu)
        obj_payload = f.read(obj_size - 4)
        payload = io.BytesIO(obj_payload)

        if obj_type == 4:  # EVENT
            # Un event contient souvent une liste d'actions
            num_actions = struct.unpack('B', payload.read(1))[0]
            action_ids = []
            for _ in range(num_actions):
                action_ids.append(struct.unpack('<I', payload.read(4))[0])
            links["events"][obj_id] = action_ids

        elif obj_type == 3:  # ACTION
            # L'action pointe vers un objet cible (Sound ou Container)
            # On saute 1 octet (Scope) et 1 octet (Type d'action)
            payload.seek(2, 1)
            target_id = struct.unpack('<I', payload.read(4))[0]
            links["actions"][obj_id] = target_id

        elif obj_type == 2:  # SOUND
            # On cherche l'ID du fichier .wem associé
            # Structure type : [4B Unknown] [1B SourceType] [4B AudioID]
            payload.seek(4, 1)
            source_type = struct.unpack('B', payload.read(1))[0]
            audio_id = struct.unpack('<I', payload.read(4))[0]
            links["sounds"][obj_id] = audio_id

    return links

# --- Logique de résolution ---
def resolve_hierarchy(links):
    resolved_map = {}

    for ev_id, act_ids in links["events"].items():
        # On initialise une liste vide pour cet événement
        if ev_id not in resolved_map:
            resolved_map[ev_id] = []

        for act_id in act_ids:
            target_id = links["actions"].get(act_id)

            if target_id is None:
                continue

            # Cas 1 : L'action pointe directement vers un son
            if target_id in links["sounds"]:
                audio_id = links["sounds"][target_id]
                if audio_id not in resolved_map[ev_id]:
                    resolved_map[ev_id].append(audio_id)

            # Cas 2 : L'action pointe vers un Container (Type 05, 06, etc.)
            # Si tu as déjà parsé les containers dans ton dictionnaire 'links'
            elif "containers" in links and target_id in links["containers"]:
                # On ajoute tous les sons enfants du container
                for child_audio_id in links["containers"][target_id]:
                    if child_audio_id not in resolved_map[ev_id]:
                        resolved_map[ev_id].append(child_audio_id)

    return resolved_map

def wwise_hash(name):
    name = name.lower().strip()
    hash_value = 2166136261  # Offset basis pour 32-bit
    prime = 16777619  # FNV prime pour 32-bit

    for char in name:
        # Multiplication par le prime et modulo 2^32
        hash_value = (hash_value * prime) & 0xFFFFFFFF
        # XOR avec la valeur ASCII du caractère
        hash_value = hash_value ^ ord(char)

    return hash_value

def build_translation_table(xml_file):
    translation_table = {}
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # On cherche tous les attributs atl_name
    for trigger in root.findall(".//ATLTrigger"):
        name = trigger.get("atl_name")
        if name:
            # Calcul du hash FNV1-32 (Wwise style)
            id_hash = wwise_hash(name)
            translation_table[id_hash] = name

    return translation_table

def extractBNKfile(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    # On cherche tous les attributs wwise_name
    for trigger in root.findall(".//WwiseFile"):
        name = trigger.get("wwise_name")
        if name and name.endswith(".bnk"):
           return name

    return ""

def afficher_resultats(resultats, name_map):
    print("\n" + "=" * 50)
    print("RECONSTRUCTION DES LIENS AUDIO")
    print("=" * 50)

    for ev_id, wems in resultats.items():
        # On cherche le nom en clair de l'Event
        event_name = name_map.get(ev_id, f"ID_Inconnu ({ev_id})")
        nom_atl = name_map.get(ev_id, f"HASH_INCONNU_{ev_id}")

        print(f"\n[EVENT] {event_name}")
        if not wems:
            print("   (Pas de sons directs trouvés)")
        else:
            print(f"{nom_atl:<60} | {wems[0]}.wem")
            for wem_id in wems:
                print(f"   └──> Fichier : {wem_id}.wem")

def exporter_vers_csv(resultats_bnk, dictionnaire_noms, nom_fichier_sortie="mapping_audio.csv"):
    print(f"--- Exportation en cours vers {nom_fichier_sortie} ---")

    with open(nom_fichier_sortie, mode='w', newline='', encoding='utf-8') as fichier_csv:
        writer = csv.writer(fichier_csv, delimiter=';')  # Point-virgule pour Excel FR

        # En-tête du tableau
        writer.writerow(['Nom ATL (Source XML)', 'ID Event (Hash)', 'Fichiers .wem associés'])

        for ev_id, wems in resultats_bnk.items():
            # On récupère le nom en clair
            nom_atl = dictionnaire_noms.get(ev_id, "NOM_INCONNU")

            # On transforme la liste de .wem [123, 456] en une chaîne "123.wem, 456.wem"
            liste_wems = ", ".join([f"{w}.wem" for w in wems]) if wems else "Aucun son trouvé"

            # On écrit la ligne
            writer.writerow([nom_atl, ev_id, liste_wems])

    print("--- Exportation terminée avec succès ! ---")

basedir_wwise = "E:\\StarFab_exports\\Data\\Sounds\\wwise\\English(US)"
basedir_xml = "E:\\StarFab_exports\\Data\\Libs\\GameAudio"
listdir = os.listdir(basedir_xml)



unprocessed = []
master_map = {}
master_translation_table = {}

for file in listdir:
    full_xml_path = os.path.join(basedir_xml, file)

    if not os.path.isfile(full_xml_path):
        continue

    print(f"Liniking on file : {file}")
    bnk_file = extractBNKfile(full_xml_path)
    if bnk_file:
        translation_table = build_translation_table(os.path.join(basedir_xml, file))
        master_translation_table.update(translation_table)

        bnk_path = os.path.join(basedir_wwise, bnk_file)

        if os.path.exists(bnk_path):
            print(f"Processing : {bnk_path}")
            map = parse_bnk(bnk_path)
            #afficher_resultats(map, translation_table)
            master_map.update(map)
        else:
            print(f"{bnk_path} n'existe pas")
            unprocessed.append(bnk_path)

exporter_vers_csv(master_map, master_translation_table, "total_game_audio_mapping.csv")




# Usage
#ma_table = build_translation_table(basedir_xml.join())
#bnk_path = extractBNKfile(myxmlpath)




















print(listdir.__len__())

def process_all_banks(listdirs, translation_table):
    master_map = {}

    for file in listdirs:
        if file.endswith(".bnk"):
            for file in listdirs:
                print(f"Analyse de : {file}...")
                map = parse_bnk(os.path.join(basedir_wwise, file))
                #afficher_resultats(map, translation_table)

                for ev_id, wems in map.items():
                    if ev_id not in master_map:
                        master_map[ev_id] = set()  # Utilise un set pour éviter les doublons de .wem
                    master_map[ev_id].update(wems)
        final_dict = {k: list(v) for k, v in master_map.items()}
        exporter_vers_csv(final_dict, translation_table, "total_game_audio_mapping.csv")

#process_all_banks(listdir, ma_table)




