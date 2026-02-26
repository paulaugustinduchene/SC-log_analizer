import configparser

global_new_path= "E:\\StarFab_exports\\Data\\Localization\\english\\global.ini"
global_old_path = "E:\\StarFab_exports\\Data\\Data\\Localization\\english\\global.ini"


def load_flat_ini(filepath):
    data = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # On ignore les lignes vides ou les commentaires
            if not line or line.startswith((';', '#')):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                data[key.strip()] = value.strip()
    return data


def compare_flat_files(file1, file2):
    old, new = load_flat_ini(file1), load_flat_ini(file2)

    all_keys = set(old.keys()) | set(new.keys())

    for key in sorted(all_keys):
        if key not in old:
            print(f"[+] AJOUT : {key} = {new[key]}")
        elif key not in new:
            print(f"[-] RETRAIT : {key} (était: {old[key]})")
        elif old[key] != new[key]:
            print(f"[*] MODIFIÉ : {key} ({old[key]} -> {new[key]})")

compare_flat_files(global_old_path, global_new_path)