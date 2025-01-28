import json
import os

# Banco simulado
entradas = []
saidas = []
descarte = []
estoque = []

def carregar_dados():
    global entradas, saidas, descarte, estoque

    if os.path.exists('backup/estoque.json'):
        with open('backup/estoque.json', 'r') as file:
            estoque = json.load(file)
    if os.path.exists('backup/entradas.json'):
        with open('backup/entradas.json', 'r') as file:
            entradas = json.load(file)
    if os.path.exists('backup/saidas.json'):
        with open('backup/saidas.json', 'r') as file:
            saidas = json.load(file)
    if os.path.exists('backup/descarte.json'):
        with open('backup/descarte.json', 'r') as file:
            descarte = json.load(file)

def salvar_dados():
    # Salva o estoque sempre
    with open('backup/estoque.json', 'w') as file:
        json.dump(estoque, file, indent=4)

    # Salva apenas se houver dados em 'entradas'
    if entradas:
        with open('backup/entradas.json', 'w') as file:
            json.dump(entradas, file, indent=4)
    elif os.path.exists('backup/entradas.json'):
        os.remove('backup/entradas.json')  # Remove o arquivo se estiver vazio

    # Salva apenas se houver dados em 'saidas'
    if saidas:
        with open('backup/saidas.json', 'w') as file:
            json.dump(saidas, file, indent=4)
    elif os.path.exists('backup/saidas.json'):
        os.remove('backup/saidas.json')  # Remove o arquivo se estiver vazio

    # Salva o descarte sempre
    with open('backup/descarte.json', 'w') as file:
        json.dump(descarte, file, indent=4)

