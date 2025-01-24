import shutil
import os
import json
from estoque import banco

BACKUP_DIR = 'backup/'

# Função para salvar backup dos dados


def salvar_backup():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)

    # Salva o backup do estoque
    arquivo_backup = os.path.join(BACKUP_DIR, 'estoque_backup.json')
    with open(arquivo_backup, 'w') as file:
        json.dump({
            'estoque': banco.estoque,
            'entradas': banco.entradas,
            'saidas': banco.saidas,
            'descarte': banco.descarte
        }, file, indent=4)
    print("Backup realizado com sucesso!")
