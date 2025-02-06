# imports

from typing import Optional
import os
import json
from functools import wraps
import keyboard
import sys
from datetime import datetime
from estoque import banco
import pandas as pd
import subprocess
import logging
from pathlib import Path
import re

# limpar tela


def limpar_tela():
    """Função para limpar a tela do terminal."""
    sistema = os.name
    if sistema == "nt":  # Para Windows
        os.system("cls")
    else:
        os.system("clear")
    print("=" * 37)
    print("Digite 'cancelar' a qualquer momento\n caso queira cancelar o processo!")
    print("=" * 37)


def verificar_cancelamento(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, str) and result.strip().lower() == 'cancelar':
            limpar_tela()
            print("Processo cancelado.")
        return result
    return wrapper


def salvar_dados_seguro(func):
    """
    Decorador para garantir o salvamento seguro de dados com backup automático
    e registro de erros.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Criar backup antes da operação
        try:
            if os.path.exists('dados.json'):
                with open('dados.json', 'r') as f:
                    backup_data = f.read()

                # Criar pasta de backup se não existir
                if not os.path.exists('backup'):
                    os.makedirs('backup')

                # Salvar backup com timestamp
                backup_file = f'backup/backup_{
                    datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
                with open(backup_file, 'w') as f:
                    f.write(backup_data)
        except Exception as e:
            print(f"Erro ao criar backup: {e}")
            return None

        try:
            # Executar a função original
            result = func(*args, **kwargs)

            # Salvar dados
            banco.salvar_dados()

            return result

        except Exception as e:
            # Registrar erro em um arquivo de log
            error_msg = f"[{datetime.now()}] Erro na função {
                func.__name__}: {str(e)}\n"

            try:
                with open('error_log.txt', 'a') as f:
                    f.write(error_msg)
            except:
                print("Não foi possível salvar o log de erro")

            # Tentar restaurar backup em caso de erro
            try:
                if os.path.exists(backup_file):
                    with open(backup_file, 'r') as f:
                        backup_data = json.load(f)
                    with open('dados.json', 'w') as f:
                        json.dump(backup_data, f, indent=4)
                    print("Dados restaurados do backup após erro")
            except:
                print("Não foi possível restaurar o backup")

            print(f"Erro ao processar operação: {e}")
            return None

    return wrapper


def limpar_backups_antigos(dias=365):
    """Remove backups mais antigos que o número de dias especificado"""
    try:
        import time
        now = time.time()
        backup_dir = 'backup'

        if os.path.exists(backup_dir):
            for f in os.listdir(backup_dir):
                if f.startswith('backup_') and f.endswith('.json'):
                    f_path = os.path.join(backup_dir, f)
                    if os.stat(f_path).st_mtime < now - (dias * 86400):
                        os.remove(f_path)
    except Exception as e:
        print(f"Erro ao limpar backups antigos: {e}")


def configurar_log():
    """Configura log básico para rastreamento de erros"""
    if not os.path.exists('logs'):
        os.makedirs('logs')

    logging.basicConfig(
        filename=f'logs/sistema_{datetime.now().strftime("%Y%m")}.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


@verificar_cancelamento
def selecionar_classificacao():
    while True:
        print("\nClassificação do produto:")
        print("1 - AERO (Aeronáutico)")
        print("2 - AUTO (Automotivo)")
        print("3 - EPI (Equipamento de Proteção)")
        print("4 - CONS (Produto de Consumo)")

        opcao = input("\nDigite a opção desejada (1-4): ")

        if opcao.lower() == "cancelar":
            return "cancelar"

        classificacoes = {
            "1": "AERO",
            "2": "AUTO",
            "3": "EPI",
            "4": "CONS"
        }

        if opcao in classificacoes:
            return classificacoes[opcao]

        print("Opção inválida! Por favor, tente novamente.")


@salvar_dados_seguro
@verificar_cancelamento
def adicionar_produto():
    limpar_tela()
    print("===========================================================")
    print("Entrada ao estoque, sobre o produto, digite o que se pede: ")
    print("===========================================================")

    classificacao = selecionar_classificacao()
    if classificacao.lower() == 'cancelar':
        return

    # Verifica se quer adicionar a um produto existente primeiro
    opcao = input("Deseja adicionar a um produto existente? (S/N): ")
    if opcao.lower() == 'cancelar':
        return

    if opcao.lower() == 's':
        # Busca produto existente
        print("\nBusca de produto existente:")
        print("1 - Buscar por Nome")
        print("2 - Buscar por Modelo")
        if classificacao == "AERO":
            print("3 - Buscar por Part Number")

        opcao_busca = input("\nDigite a opção desejada: ")
        if opcao_busca.lower() == 'cancelar':
            return

        termo_busca = input("Digite o termo de busca: ")
        if termo_busca.lower() == 'cancelar':
            return

        # Filtra os produtos
        resultados = []
        if opcao_busca == "1":
            resultados = [p for p in banco.estoque if termo_busca.lower(
            ) in p['nome'].lower() and p['classificacao'] == classificacao]
        elif opcao_busca == "2":
            resultados = [p for p in banco.estoque if termo_busca.lower(
            ) in p['modelo'].lower() and p['classificacao'] == classificacao]
        elif opcao_busca == "3" and classificacao == "AERO":
            resultados = [p for p in banco.estoque if termo_busca.lower() in str(
                p.get('partNumber', '')).lower()]

        if resultados:
            print("\nProdutos encontrados:")
            for i, produto in enumerate(resultados):
                part_number = f", PN: {produto.get(
                    'partNumber', 'N/A')}" if classificacao == "AERO" else ""
                print(f"{i + 1} - Nome: {produto['nome']}, Modelo: {produto['modelo']}{part_number}, "
                      f"Condição: {produto.get('condicao', 'N/A')}, Quantidade: {produto['quantidade']}")

            try:
                escolha = int(input("\nSelecione o número do produto: ")) - 1
                produto_existente = resultados[escolha]

                quantidade = int(input("Quantidade a adicionar: "))
                if quantidade <= 0:
                    print("Quantidade inválida!")
                    return

                produto_existente['quantidade'] += quantidade
                print(f"Quantidade atualizada com sucesso! Nova quantidade: {
                      produto_existente['quantidade']}")
                banco.salvar_dados()
                return

            except (ValueError, IndexError):
                print("Seleção inválida!")
                return
        else:
            print(
                "Nenhum produto encontrado. Continuando com cadastro de novo produto...")

    # Cadastro de novo produto
    produto = {
        'classificacao': classificacao,
        'nome': '',
        'modelo': '',
        'valor': 0,
        'quantidade': 0,
        'origem': '',
        'data': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

    # Campo de condição para todos os produtos exceto CONS
    if classificacao != "CONS":
        print("\nCondição do produto:")
        print("1 - Novo")
        print("2 - Usado")
        print("3 - Revisado")

        while True:
            condicao_opcao = input("Digite a opção (1/2/3): ")
            if condicao_opcao.lower() == 'cancelar':
                return
            if condicao_opcao in ['1', '2', '3']:
                produto['condicao'] = {
                    '1': 'Novo',
                    '2': 'Usado',
                    '3': 'Revisado'
                }[condicao_opcao]
                break
            print("Opção inválida!")

    # Campos comuns para todos os tipos
    produto['nome'] = input("Nome----------> ")
    if produto['nome'].lower() == 'cancelar':
        return

    produto['modelo'] = input("Modelo--------> ")
    if produto['modelo'].lower() == 'cancelar':
        return

    quantidade = input("Quantidade----> ")
    if quantidade.lower() == 'cancelar':
        return
    produto['quantidade'] = int(quantidade)

    valor = input("Valor Unidade-> ")
    if valor.lower() == 'cancelar':
        return
    produto['valor'] = float(valor)

    produto['origem'] = input("Origem--------> ")
    if produto['origem'].lower() == 'cancelar':
        return

    # Campos específicos por classificação
    if classificacao == "AERO":
        produto['partNumber'] = input(
            "PartNumber (opcional, pressione Enter para pular): ")
    if produto['partNumber'].lower() == 'cancelar':
        return

    # Se não for preenchido, define como traço
    if not produto['partNumber'].strip():
        produto['partNumber'] = '-'

    banco.estoque.append(produto)
    print(f"Produto {produto['nome']} adicionado com sucesso!")
    banco.salvar_dados()

    # Registro do log de entrada
    arquivo_log = 'backup/estoque_entradas.json'
    if not os.path.exists('backup'):
        os.makedirs('backup')

    if not os.path.exists(arquivo_log):
        with open(arquivo_log, 'w') as file:
            json.dump([], file)

    with open(arquivo_log, 'r+') as file:
        logs = json.load(file)
        logs.append(produto)
        file.seek(0)
        json.dump(logs, file, indent=4)


# registrar saida


@salvar_dados_seguro
@verificar_cancelamento
def registrar_saida():
    try:
        limpar_tela()
        print("\n===========================================================")
        print("Saída de produto do estoque. Escolha uma opção de busca:")
        print("1 - Buscar por Nome")
        print("2 - Buscar por Modelo")
        print("3 - Buscar por Part Number")
        print("===========================================================")

        opcao_busca = input("Digite a opção desejada (1/2/3): ")
        if opcao_busca.lower() == "cancelar":
            return

        termo_busca = input("Digite o termo de busca: ")
        if termo_busca.lower() == "cancelar":
            return

        if opcao_busca == "1":
            resultados = [
                p for p in banco.estoque if termo_busca.lower() in p['nome'].lower()]
        elif opcao_busca == "2":
            resultados = [
                p for p in banco.estoque if termo_busca.lower() in p['modelo'].lower()]
        elif opcao_busca == "3":
            resultados = [p for p in banco.estoque if termo_busca.lower() in str(
                p.get('partNumber', '')).lower()]
        else:
            print("Opção inválida! Tente novamente.")
            return

        if not resultados:
            print("Nenhum produto encontrado.")
            return

        print("\nProdutos encontrados:")
        for i, produto in enumerate(resultados):
            part_number = f", PN: {produto.get(
                'partNumber', 'N/A')}" if 'partNumber' in produto else ""
            print(f"{i + 1} - Nome: {produto['nome']}, Modelo: {produto['modelo']}"
                  f"{part_number}, Classificação: {produto['classificacao']}, "
                  f"Condição: {produto.get('condicao', 'N/A')}, "
                  f"Quantidade: {produto['quantidade']}")

        try:
            escolha = int(
                input("\nSelecione o número do produto para saída: ")) - 1
            produto_selecionado = resultados[escolha]
        except (ValueError, IndexError):
            print("Seleção inválida!")
            return

        try:
            quantidade = int(input("Quantidade para saída: "))
            if quantidade > produto_selecionado['quantidade']:
                print("Quantidade insuficiente em estoque!")
                return
            if quantidade <= 0:
                print("Quantidade deve ser maior que zero!")
                return
        except ValueError:
            print("Quantidade inválida!")
            return

        while True:
            data_manual = input("Digite a data (DD/MM/AAAA): ")
            if data_manual.lower() == "cancelar":
                return
            try:
                data = datetime.strptime(
                    data_manual, "%d/%m/%Y").strftime("%d/%m/%Y")
                break
            except ValueError:
                print("Data inválida! Use o formato DD/MM/AAAA")

        saida = {
            'data': data,
            'nome': produto_selecionado['nome'],
            'modelo': produto_selecionado['modelo'],
            'classificacao': produto_selecionado['classificacao'],
            'condicao': produto_selecionado.get('condicao', 'N/A'),
            'quantidade': quantidade,
            'valor': produto_selecionado.get('valor', 0),
            'origem': produto_selecionado.get('origem', 'N/A'),
            'partNumber': produto_selecionado.get('partNumber', 'N/A'),
            'observacoes': 'N/A'
        }

        if produto_selecionado['classificacao'] == "AERO":
            prefixo = input("Digite o prefixo do avião (obrigatório): ")
            if prefixo.lower() == "cancelar":
                return
            if not prefixo.strip():
                print("Para peças AERO, o prefixo do avião é obrigatório!")
                return

            serial_number = input(
                "Digite o Serial Number da peça (opcional): ")
            if serial_number.lower() == "cancelar":
                return

            observacoes = input("Observações (opcional): ")
            if observacoes.lower() == "cancelar":
                return

            saida.update({
                'prefixo_aviao': prefixo,
                'serialNumber': serial_number if serial_number.strip() else 'N/A',
                'observacoes': observacoes if observacoes.strip() else 'N/A'
            })

        elif produto_selecionado['classificacao'] == "AUTO":
            prefixo = input("Digite o prefixo (obrigatório): ")
            if prefixo.lower() == "cancelar":
                return
            if not prefixo.strip():
                print("Para peças AUTO, o prefixo é obrigatório!")
                return
            placa = input("Digite a placa da camionete (obrigatório): ")
            if placa.lower() == "cancelar":
                return
            if not placa.strip():
                print("Para peças AUTO, a placa da camionete é obrigatória!")
                return

            observacoes = input("Observações (opcional): ")
            if observacoes.lower() == "cancelar":
                return

            saida.update({
                'prefixo_aviao': prefixo,
                'placa_camionete': placa,
                'observacoes': observacoes if observacoes.strip() else 'N/A'
            })

        elif produto_selecionado['classificacao'] == "EPI":
            prefixo = input("Digite o prefixo (obrigatório): ")
            if prefixo.lower() == "cancelar":
                return
            if not prefixo.strip():
                print("Para peças EPI, o prefixo é obrigatório!")
                return
            nome_badeco = input("Digite o nome do badeco (obrigatório): ")
            if nome_badeco.lower() == "cancelar":
                return
            if not nome_badeco.strip():
                print("Para peças EPI, o nome do badeco é obrigatório!")
                return

            observacoes = input("Observações (opcional): ")
            if observacoes.lower() == "cancelar":
                return

            saida.update({
                'prefixo_aviao': prefixo,
                'nome_badeco': nome_badeco,
                'observacoes': observacoes if observacoes.strip() else 'N/A'
            })

        elif produto_selecionado['classificacao'] == "CONS":
            observacoes = input("Observações (opcional): ")
            if observacoes.lower() == "cancelar":
                return
            saida['observacoes'] = observacoes if observacoes.strip() else 'N/A'

        produto_selecionado['quantidade'] -= quantidade

        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(os.path.dirname(sys.executable))
        else:
            base_path = os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))

        caminho_backup = os.path.join(base_path, 'backup')
        os.makedirs(caminho_backup, exist_ok=True)

        arquivo_saidas = os.path.join(
            base_path, 'backup', 'estoque_saidas.json')

        try:
            with open(arquivo_saidas, 'r', encoding='utf-8') as f:
                estoque_saidas = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            estoque_saidas = []

        estoque_saidas.append(saida)

        with open(arquivo_saidas, 'w', encoding='utf-8') as f:
            json.dump(estoque_saidas, f, ensure_ascii=False, indent=4)

        if produto_selecionado['quantidade'] == 0:
            banco.estoque.remove(produto_selecionado)
            print(f"Produto removido do estoque.")

        banco.salvar_dados()
        print("Saída registrada com sucesso!")

    except Exception as e:
        logging.error(f"Erro ao registrar saída: {str(e)}")
        print(f"Erro ao registrar saída: {str(e)}")
        return None

# Função para registrar o descarte de um produto


@salvar_dados_seguro
@verificar_cancelamento
def registrar_descarte():
    limpar_tela()
    print("\n===========================================================")
    print("Descarte de produto. Escolha uma opção de busca:")
    print("1 - Buscar por Nome")
    print("2 - Buscar por Modelo")
    print("===========================================================")

    opcao_busca = input("Digite a opção desejada (1/2): ")
    if opcao_busca.lower() == "cancelar":
        return

    termo_busca = input("Digite o termo de busca: ")
    if termo_busca.lower() == "cancelar":
        return

    # Filtra os produtos
    if opcao_busca == "1":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['nome'].lower()]
    elif opcao_busca == "2":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['modelo'].lower()]
    else:
        print("Opção inválida! Tente novamente.")
        return

    if not resultados:
        print("Nenhum produto encontrado.")
        return

    # Exibe os resultados
    print("\nProdutos encontrados:")
    for i, produto in enumerate(resultados):
        print(f"{i + 1} - Nome: {produto['nome']}, Modelo: {produto['modelo']}, "
              f"Classificação: {produto['classificacao']}, Quantidade: {produto['quantidade']}")

    try:
        escolha = int(
            input("\nSelecione o número do produto para descarte: ")) - 1
        produto_selecionado = resultados[escolha]
    except (ValueError, IndexError):
        print("Seleção inválida!")
        return

    try:
        quantidade = int(input("\nQuantidade para descarte: "))
        if quantidade > produto_selecionado['quantidade']:
            print("Quantidade insuficiente!")
            return
    except ValueError:
        print("Quantidade inválida!")
        return

    motivo = input("Motivo do descarte: ")
    if motivo.lower() == "cancelar":
        return

    # Atualiza o estoque
    produto_selecionado['quantidade'] -= quantidade

    if produto_selecionado['quantidade'] == 0:
        banco.estoque.remove(produto_selecionado)
        print(f"Produto removido do estoque.")

    # Registra o descarte
    descarte = {
        'data': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'nome': produto_selecionado['nome'],
        'modelo': produto_selecionado['modelo'],
        'classificacao': produto_selecionado['classificacao'],
        'quantidade': quantidade,
        'motivo': motivo
    }

    if produto_selecionado['classificacao'] == "AERO":
        descarte['partNumber'] = produto_selecionado.get('partNumber')
        descarte['serialNumber'] = produto_selecionado.get('serialNumber')
        descarte['prefixo_aviao'] = produto_selecionado.get('prefixo_aviao')
    elif produto_selecionado['classificacao'] == "AUTO":
        descarte['placa_camionete'] = produto_selecionado.get(
            'placa_camionete')
        descarte['prefixo_aviao'] = produto_selecionado.get('prefixo_aviao')
    elif produto_selecionado['classificacao'] == "EPI":
        descarte['nome_badeco'] = produto_selecionado.get('nome_badeco')
        descarte['prefixo_aviao'] = produto_selecionado.get('prefixo_aviao')

    banco.descarte.append(descarte)
    banco.salvar_dados()

    print("Descarte registrado com sucesso!")


# função para mostrar o estoque


@verificar_cancelamento
def mostrar_estoque():
    limpar_tela()
    print("\nEstoque atual:")

    if not banco.estoque:
        print("O estoque está vazio.")
    else:
        # Agrupa produtos por classificação
        aero = [p for p in banco.estoque if p['classificacao'] == "AERO"]
        auto = [p for p in banco.estoque if p['classificacao'] == "AUTO"]
        epi = [p for p in banco.estoque if p['classificacao'] == "EPI"]

        def mostrar_produto(produto):
            print("=" * 50)
            print(f"Nome         : {produto['nome']}")
            print(f"Modelo       : {produto['modelo']}")
            print(f"Quantidade   : {produto['quantidade']}")
            print(f"Valor        : R${produto['valor']:.2f}")

            if produto['classificacao'] == "AERO":
                print(f"PartNumber   : {produto.get('partNumber', 'N/A')}")
                print(f"SerialNumber : {produto.get('serialNumber', 'N/A')}")
                print(f"Prefixo Avião: {produto.get('prefixo_aviao', 'N/A')}")
            elif produto['classificacao'] == "AUTO":
                print(f"Placa        : {
                      produto.get('placa_camionete', 'N/A')}")
                print(f"Prefixo Avião: {produto.get('prefixo_aviao', 'N/A')}")
            elif produto['classificacao'] == "EPI":
                print(f"Funcionário  : {produto.get('nome_badeco', 'N/A')}")
                print(f"Prefixo Avião: {produto.get('prefixo_aviao', 'N/A')}")

        if aero:
            print("\n=== PRODUTOS AERONÁUTICOS ===")
            for produto in aero:
                mostrar_produto(produto)

        if auto:
            print("\n=== PRODUTOS AUTOMOTIVOS ===")
            for produto in auto:
                mostrar_produto(produto)

        if epi:
            print("\n=== EQUIPAMENTOS DE PROTEÇÃO INDIVIDUAL ===")
            for produto in epi:
                mostrar_produto(produto)

    # Aguarda o usuário digitar "voltar" antes de retornar ao menu principal
    while True:
        opcao = input(
            "\nDigite 'voltar' para retornar ao menu: ").strip().lower()
        if opcao == "voltar":
            break


# função de busca de produto


@verificar_cancelamento
def buscar_produto():
    limpar_tela()
    print("\nBuscar produto no estoque:")
    print("1. Buscar por PartNumber (produtos aeronáuticos)")
    print("2. Buscar por Nome")
    print("3. Buscar por Modelo")
    print("4. Buscar por Classificação")

    opcao = input("Escolha uma opção (1-4): ").strip()

    if opcao.lower() == "cancelar":
        return

    if opcao == "4":
        classificacao = selecionar_classificacao()
        resultados = [
            p for p in banco.estoque if p['classificacao'] == classificacao]
    else:
        termo_busca = input("Digite o termo de busca: ").strip()
        if termo_busca.lower() == "cancelar":
            return

        if opcao == "1":
            resultados = [
                p for p in banco.estoque
                if p.get('partNumber') and termo_busca.lower() in p['partNumber'].lower()
            ]
        elif opcao == "2":
            resultados = [
                p for p in banco.estoque
                if termo_busca.lower() in p['nome'].lower()
            ]
        elif opcao == "3":
            resultados = [
                p for p in banco.estoque
                if termo_busca.lower() in p['modelo'].lower()
            ]
        else:
            print("Opção inválida.")
            return

    limpar_tela()
    if resultados:
        print("\nProdutos encontrados:")
        for produto in resultados:
            print("\n" + "=" * 40)
            for chave, valor in sorted(produto.items()):
                print(f"{chave.capitalize()}: {valor}")

        total_produtos = len(resultados)
        total_quantidade = sum(p['quantidade'] for p in resultados)
        total_valor = sum(p['quantidade'] * p['valor'] for p in resultados)

        print("\n=== Resumo da Busca ===")
        print(f"Total de Produtos Encontrados: {total_produtos}")
        print(f"Quantidade Total: {total_quantidade}")
        print(f"Valor Total: R$ {total_valor:.2f}")
    else:
        print("Nenhum produto encontrado.")

    input("\nDigite 'voltar' para retornar ao menu: ")
# editar produto


@salvar_dados_seguro
@verificar_cancelamento
def editar_produto():
    limpar_tela()
    print("\nEditar produto no estoque:")
    print("1. Buscar por Nome")
    print("2. Buscar por Modelo")
    opcao = input("Escolha uma opção (1-2): ").strip()

    if opcao.lower() == "cancelar":
        return

    termo_busca = input("Digite o termo de busca: ").strip()
    if termo_busca.lower() == "cancelar":
        return

    resultados = []
    if opcao == "1":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['nome'].lower()]
    elif opcao == "2":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['modelo'].lower()]
    else:
        print("Opção inválida.")
        return

    if resultados:
        print("\nProdutos encontrados:")
        for idx, produto in enumerate(resultados):
            print(f"\n{idx + 1}. Nome: {produto['nome']}, Modelo: {produto['modelo']}, "
                  f"Classificação: {produto['classificacao']}")

        try:
            escolha = int(
                input("\nEscolha o número do produto correspondente para editar: "))
            if escolha.lower == "cancelar":
                return

            produto_selecionado = resultados[escolha - 1]

            print("\nDados atuais do produto:")
            for key, value in produto_selecionado.items():
                print(f"- {key}: {value}")

            # Define campos editáveis baseados na classificação
            campos_comuns = {
                '1': 'nome',
                '2': 'modelo',
                '3': 'quantidade',
                '4': 'valor'
            }

            campos_especificos = {}
            if produto_selecionado['classificacao'] == "AERO":
                campos_especificos.update({
                    '5': 'partNumber',
                    '6': 'serialNumber',
                    '7': 'prefixo_aviao'
                })
            elif produto_selecionado['classificacao'] == "AUTO":
                campos_especificos.update({
                    '5': 'placa_camionete',
                    '6': 'prefixo_aviao'
                })
            elif produto_selecionado['classificacao'] == "EPI":
                campos_especificos.update({
                    '5': 'nome_badeco',
                    '6': 'prefixo_aviao'
                })

            campos = {**campos_comuns, **campos_especificos}

            print("\nCampos disponíveis para edição:")
            for num, campo in campos.items():
                print(f"{num}. {campo}")

            campo_escolhido = input("\nEscolha o campo para editar: ").strip()
            if campo_escolhido not in campos:
                print("Campo inválido.")
                return

            novo_valor = input("Digite o novo valor: ").strip()
            if novo_valor.lower() == "cancelar":
                return

            # Converte valores numéricos
            if campos[campo_escolhido] == 'quantidade':
                novo_valor = int(novo_valor)
            elif campos[campo_escolhido] == 'valor':
                novo_valor = float(novo_valor)

            produto_selecionado[campos[campo_escolhido]] = novo_valor
            banco.salvar_dados()
            print("Produto atualizado com sucesso!")

        except (ValueError, IndexError):
            print("Seleção inválida.")
    else:
        print("Nenhum produto encontrado.")

# excluir produto


@salvar_dados_seguro
@verificar_cancelamento
def excluir_produto():
    limpar_tela()
    print("\nExcluir produto do estoque:")
    print("1. Buscar por Nome")
    print("2. Buscar por Modelo")
    opcao = input("Escolha uma opção (1-2): ").strip()

    if opcao.lower() == "cancelar":
        return

    termo_busca = input("Digite o termo de busca: ").strip()
    if termo_busca.lower() == "cancelar":
        return

    resultados = []
    if opcao == "1":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['nome'].lower()]
    elif opcao == "2":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['modelo'].lower()]
    else:
        print("Opção inválida.")
        return

    if resultados:
        print("\nProdutos encontrados:")
        for idx, produto in enumerate(resultados):
            print(f"{idx + 1}. Nome: {produto['nome']}, "
                  f"Modelo: {produto['modelo']}, "
                  f"Classificação: {produto['classificacao']}")

        try:
            escolha = input(
                "\nSelecione o número do produto correspondente para excluir: ").strip()
            if escolha.lower() == "cancelar":
                return

            escolha = int(escolha)
            produto_selecionado = resultados[escolha - 1]

            print("\nProduto selecionado para exclusão:")
            for chave, valor in produto_selecionado.items():
                print(f"{chave.capitalize()}: {valor}")

            confirmar = input("\nConfirma a exclusão? (S/N): ").strip().lower()
            if confirmar != "s":
                print("Exclusão cancelada.")
                return

            # Remove o produto do estoque
            banco.estoque.remove(produto_selecionado)
            banco.salvar_dados()

            # Registro da exclusão
            log_exclusao = {
                'data_hora': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                'classificacao': produto_selecionado['classificacao'],
                'nome': produto_selecionado['nome'],
                'modelo': produto_selecionado['modelo'],
                'quantidade': produto_selecionado['quantidade'],
                'valor': produto_selecionado['valor'],
                'origem': produto_selecionado.get('origem', 'N/A')
            }

            # Adiciona campos específicos baseado na classificação
            if produto_selecionado['classificacao'] == "AERO":
                log_exclusao.update({
                    'partNumber': produto_selecionado.get('partNumber'),
                    'serialNumber': produto_selecionado.get('serialNumber'),
                    'prefixo_aviao': produto_selecionado.get('prefixo_aviao')
                })
            elif produto_selecionado['classificacao'] == "AUTO":
                log_exclusao.update({
                    'placa_camionete': produto_selecionado.get('placa_camionete'),
                    'prefixo_aviao': produto_selecionado.get('prefixo_aviao')
                })
            elif produto_selecionado['classificacao'] == "EPI":
                log_exclusao.update({
                    'nome_badeco': produto_selecionado.get('nome_badeco'),
                    'prefixo_aviao': produto_selecionado.get('prefixo_aviao')
                })

            # Salva o log de exclusão
            arquivo_log = 'backup/estoque_exclusoes.json'
            if not os.path.exists('backup'):
                os.makedirs('backup')

            # Carrega ou cria o arquivo de log
            if os.path.exists(arquivo_log):
                with open(arquivo_log, 'r') as file:
                    logs_exclusao = json.load(file)
            else:
                logs_exclusao = []

            # Adiciona o novo log e salva
            logs_exclusao.append(log_exclusao)
            with open(arquivo_log, 'w') as file:
                json.dump(logs_exclusao, file, indent=4)

            print("\nProduto excluído com sucesso!")
            print("Log de exclusão registrado.")

        except (ValueError, IndexError):
            print("Seleção inválida!")
            return
    else:
        print("Nenhum produto encontrado com o termo de busca informado.")


def configurar_log():
    logging.basicConfig(filename='relatorio.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')


# Configura encoding do console para UTF-8
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')


def criar_pasta_backup():
    """
    Cria a pasta de backup se não existir, funcionando tanto em desenvolvimento quanto em exe
    """
    try:
        # Determina o caminho base do aplicativo
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Cria o caminho absoluto para a pasta de backup
        caminho_backup = os.path.join(base_path, 'backup')

        # Cria a pasta se não existir
        Path(caminho_backup).mkdir(parents=True, exist_ok=True)

        # Cria o arquivo JSON se não existir
        arquivo_saidas = os.path.join(caminho_backup, 'estoque_saidas.json')
        if not os.path.exists(arquivo_saidas):
            with open(arquivo_saidas, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)

        return caminho_backup

    except Exception as e:
        logging.error(f"Erro ao criar pasta de backup: {str(e)}")
        print(f"Erro ao criar pasta de backup: {str(e)}")
        return None


def criar_pasta_relatorios():
    """
    Cria a pasta de relatórios se não existir, funcionando tanto em desenvolvimento quanto em exe
    """
    try:
        # Determina o caminho base do aplicativo
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Cria o caminho absoluto para a pasta de relatórios
        caminho_relatorios = os.path.join(base_path, 'relatorios')

        # Cria a pasta se não existir
        Path(caminho_relatorios).mkdir(parents=True, exist_ok=True)
        return caminho_relatorios

    except Exception as e:
        print(f"Erro ao criar pasta de relatórios: {str(e)}")
        return None


def configurar_log():
    """
    Configura o sistema de logging
    """
    caminho_relatorios = criar_pasta_relatorios()
    if caminho_relatorios:
        arquivo_log = os.path.join(caminho_relatorios, 'log_relatorios.txt')
        logging.basicConfig(
            filename=arquivo_log,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%d/%m/%Y %H:%M:%S'
        )


def gerar_relatorio_saidas(data_inicial: str, data_final: str) -> str:
    """
    Gera relatório de saídas do estoque com tratamento de erros e validações
    """
    try:
        caminho_relatorios = criar_pasta_relatorios()
        if not caminho_relatorios:
            print("Erro: Não foi possível criar a pasta de relatórios")
            return None

        configurar_log()
        logging.info(f"Iniciando relatório: {data_inicial} a {data_final}")

        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(os.path.dirname(sys.executable))
        else:
            base_path = os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))

        backup_path = criar_pasta_backup()
        if not backup_path:
            logging.error("Erro ao criar pasta de backup")
            print("Erro: Não foi possível criar a pasta de backup")
            return None

        arquivo_saidas = os.path.join(
            base_path, 'backup', 'estoque_saidas.json')

        if not os.path.exists(arquivo_saidas):
            logging.error(f"Arquivo não encontrado: {arquivo_saidas}")
            print(f"Erro: Arquivo de saídas não encontrado em {
                  arquivo_saidas}")
            return None

        try:
            with open(arquivo_saidas, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                if not conteudo.strip():
                    logging.error("Arquivo de saídas está vazio")
                    print("Erro: Arquivo de saídas está vazio")
                    return None

                saidas = json.loads(conteudo)

                if not isinstance(saidas, list):
                    logging.error(
                        "Formato de dados inválido - esperado uma lista de saídas")
                    print("Erro: Formato de dados inválido no arquivo de saídas")
                    return None

                if not saidas:
                    logging.warning("Nenhum dado encontrado no arquivo")
                    print("Nenhum dado encontrado no arquivo de saídas")
                    return None

        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON: {str(e)}")
            print(f"Erro: Arquivo de saídas contém JSON inválido - {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Erro ao ler arquivo de saídas: {str(e)}")
            print(f"Erro ao ler arquivo de saídas: {str(e)}")
            return None

        df = pd.DataFrame(saidas)

        colunas_necessarias = {
            'nome': 'Nome',
            'modelo': 'Modelo',
            'partNumber': 'Part Number',
            'serialNumber': 'Serial Number',
            'prefixo_aviao': 'Prefixo',
            'nome_badeco': 'Ajudante EPI',
            'data': 'Data',
            'quantidade': 'Quantidade',
            'valor': 'Valor Unit.',
            'classificacao': 'Classificação',
            'placa_camionete': 'Placa',
            'condicao': 'Condição',
            'origem': 'Origem',
            'observacoes': 'Observações'
        }

        for col_original, col_novo in colunas_necessarias.items():
            if col_original not in df.columns:
                df[col_original] = '-'
            if col_original not in ['quantidade', 'valor', 'data']:
                df[col_original] = df[col_original].fillna('-').astype(str)

        df = df.rename(columns=colunas_necessarias)

        df['Quantidade'] = pd.to_numeric(
            df['Quantidade'], errors='coerce').fillna(0).astype(float)
        df['Valor Unit.'] = pd.to_numeric(
            df['Valor Unit.'], errors='coerce').fillna(0).astype(float)

        try:
            data_inicial_dt = datetime.strptime(data_inicial, "%d/%m/%Y")
            data_final_dt = datetime.strptime(data_final, "%d/%m/%Y")

            # Converter a coluna 'Data' para datetime
            df['Data'] = pd.to_datetime(df['Data'], format="%d/%m/%Y")

        except ValueError as e:
            logging.error(f"Erro no processamento de datas: {str(e)}")
            print("Erro: Formato de data inválido!")
            return None

        mask = (df['Data'].dt.date >= data_inicial_dt.date()) & (
            df['Data'].dt.date <= data_final_dt.date())
        df_periodo = df.loc[mask].copy()

        if df_periodo.empty:
            logging.warning("Nenhum dado encontrado no período especificado")
            print("Nenhum dado encontrado para o período especificado")
            return None

        df_periodo['Valor Total'] = df_periodo['Quantidade'] * \
            df_periodo['Valor Unit.']
        df_periodo['Valor Total'] = df_periodo['Valor Total'].fillna(
            0).astype(float)

        df_periodo = df_periodo.sort_values('Data')

        nome_arquivo = f'Relatorio_{data_inicial.replace(
            "/", "")}_{data_final.replace("/", "")}.xlsx'
        caminho_completo = os.path.join(caminho_relatorios, nome_arquivo)

        try:
            writer = pd.ExcelWriter(caminho_completo, engine='xlsxwriter')
            workbook = writer.book
            workbook.nan_inf_to_errors = True

            # Definição das cores
            cores = {
                'header': '#1B5E20',  # Verde escuro
                'subheader': '#2E7D32',  # Verde médio escuro
                'linha_clara': '#E8F5E9',  # Verde muito claro
                'linha_escura': '#C8E6C9',  # Verde claro
                'total': '#81C784',  # Verde médio
                'total_geral': '#4CAF50'  # Verde vibrante
            }

            formatos = {
                'header': workbook.add_format({
                    'bold': True,
                    'align': 'center',
                    'bg_color': cores['header'],
                    'font_color': 'white',
                    'border': 1,
                    'text_wrap': True,
                    'valign': 'vcenter'
                }),
                'subheader': workbook.add_format({
                    'bold': True,
                    'align': 'left',
                    'bg_color': cores['subheader'],
                    'font_color': 'white',
                    'border': 1
                }),
                'data': workbook.add_format({
                    'border': 1,
                    'border_color': '#81C784',
                    'align': 'left',
                    'valign': 'vcenter'
                }),
                'data_clara': workbook.add_format({
                    'border': 1,
                    'border_color': '#81C784',
                    'align': 'left',
                    'valign': 'vcenter',
                    'bg_color': cores['linha_clara']
                }),
                'data_escura': workbook.add_format({
                    'border': 1,
                    'border_color': '#81C784',
                    'align': 'left',
                    'valign': 'vcenter',
                    'bg_color': cores['linha_escura']
                }),
                'date': workbook.add_format({
                    'border': 1,
                    'border_color': '#81C784',
                    'align': 'center',
                    'num_format': 'dd/mm/yyyy'
                }),
                'number_clara': workbook.add_format({
                    'border': 1,
                    'border_color': '#81C784',
                    'align': 'right',
                    'bg_color': cores['linha_clara']
                }),
                'number_escura': workbook.add_format({
                    'border': 1,
                    'border_color': '#81C784',
                    'align': 'right',
                    'bg_color': cores['linha_escura']
                }),
                'money_clara': workbook.add_format({
                    'num_format': 'R$ #,##0.00',
                    'border': 1,
                    'border_color': '#81C784',
                    'align': 'right',
                    'bg_color': cores['linha_clara']
                }),
                'money_escura': workbook.add_format({
                    'num_format': 'R$ #,##0.00',
                    'border': 1,
                    'border_color': '#81C784',
                    'align': 'right',
                    'bg_color': cores['linha_escura']
                }),
                'total': workbook.add_format({
                    'bold': True,
                    'num_format': 'R$ #,##0.00',
                    'bg_color': cores['total'],
                    'border': 1,
                    'border_color': '#4CAF50',
                    'align': 'right'
                }),
                'total_geral': workbook.add_format({
                    'bold': True,
                    'num_format': 'R$ #,##0.00',
                    'bg_color': cores['total_geral'],
                    'font_color': 'white',
                    'border': 2,
                    'border_color': '#1B5E20',
                    'align': 'right'
                })
            }

            # Aba Resumo Geral
            sheet_resumo = workbook.add_worksheet('Resumo Geral')

            larguras_colunas = {
                'A:A': 15,  # Data
                'B:B': 15,  # Classificação
                'C:C': 20,  # Nome
                'D:D': 20,  # Modelo
                'E:E': 20,  # Part Number
                'F:F': 20,  # Serial Number
                'G:G': 15,  # Prefixo
                'H:H': 15,  # Condição
                'I:I': 20,  # Origem
                'J:J': 10,  # Quantidade
                'K:K': 15,  # Valor Total
            }

            for col, width in larguras_colunas.items():
                sheet_resumo.set_column(col, width)

            sheet_resumo.merge_range(
                'A1:K1',
                f'RESUMO DE SAÍDAS - {data_inicial} a {data_final}',
                formatos['header']
            )

            headers = ['Data', 'Classificação', 'Nome', 'Modelo', 'Part Number', 'Serial Number',
                       'Prefixo', 'Condição', 'Origem', 'Quantidade', 'Valor Total']
            for idx, header in enumerate(headers):
                sheet_resumo.write(2, idx, header, formatos['header'])

            row = 3
            for _, item in df_periodo.iterrows():
                linha_alternada = row % 2 == 0
                formato = formatos['data_clara'] if linha_alternada else formatos['data_escura']
                formato_number = formatos['number_clara'] if linha_alternada else formatos['number_escura']
                formato_money = formatos['money_clara'] if linha_alternada else formatos['money_escura']

                sheet_resumo.write(row, 0, item['Data'], formatos['date'])
                sheet_resumo.write(row, 1, str(item['Classificação']), formato)
                sheet_resumo.write(row, 2, str(item['Nome']), formato)
                sheet_resumo.write(row, 3, str(item['Modelo']), formato)
                sheet_resumo.write(row, 4, str(item['Part Number']), formato)
                sheet_resumo.write(row, 5, str(item['Serial Number']), formato)
                sheet_resumo.write(row, 6, str(item['Prefixo']), formato)
                sheet_resumo.write(row, 7, str(item['Condição']), formato)
                sheet_resumo.write(row, 8, str(item['Origem']), formato)
                sheet_resumo.write(row, 9, float(
                    item['Quantidade']), formato_number)
                sheet_resumo.write(row, 10, float(
                    item['Valor Total']), formato_money)
                row += 1

            sheet_resumo.merge_range(
                f'A{row + 1}:J{row + 1}', 'TOTAL', formatos['header'])
            sheet_resumo.write(row, 10, float(
                df_periodo['Valor Total'].sum()), formatos['total'])

            # Criar páginas para cada prefixo de avião
            for prefixo in sorted(df_periodo['Prefixo'].unique()):
                if pd.notna(prefixo) and prefixo != '-':
                    df_prefixo = df_periodo[df_periodo['Prefixo'] == prefixo].copy(
                    )

                    sheet_name = re.sub(
                        r'[\\/*?:\[\]]', '-', str(prefixo))[:31]
                    sheet = workbook.add_worksheet(sheet_name)

                    larguras_prefixo = {
                        'A:A': 15,  # Data
                        'B:B': 20,  # Nome
                        'C:C': 20,  # Modelo
                        'D:D': 20,  # Part Number
                        'E:E': 20,  # Serial Number
                        'F:F': 15,  # Classificação
                        'G:G': 15,  # Condição
                        'H:H': 20,  # Origem
                        'I:I': 20,  # Ajudante EPI
                        'J:J': 15,  # Placa
                        'K:K': 20,  # Observações
                        'L:L': 10,  # Quantidade
                        'M:M': 15,  # Valor Unit.
                        'N:N': 15,  # Valor Total
                    }

                    for col, width in larguras_prefixo.items():
                        sheet.set_column(col, width)

                    sheet.merge_range(
                        'A1:N1',
                        f'SAÍDAS {prefixo} - {data_inicial} a {data_final}',
                        formatos['header']
                    )

                    colunas_ordenadas = [
                        'Data', 'Nome', 'Modelo', 'Part Number', 'Serial Number',
                        'Classificação', 'Condição', 'Origem', 'Ajudante EPI', 'Placa',
                        'Observações',
                        'Quantidade', 'Valor Unit.', 'Valor Total'
                    ]

                    for idx, col in enumerate(colunas_ordenadas):
                        sheet.write(2, idx, col, formatos['header'])

                    linha_alternada = True
                    row = 3
                    for _, item in df_prefixo.iterrows():
                        formato = formatos['data_clara'] if linha_alternada else formatos['data_escura']
                        formato_number = formatos['number_clara'] if linha_alternada else formatos['number_escura']
                        formato_money = formatos['money_clara'] if linha_alternada else formatos['money_escura']

                        sheet.write(row, 0, item['Data'], formatos['date'])
                        sheet.write(row, 1, str(item['Nome']), formato)
                        sheet.write(row, 2, str(item['Modelo']), formato)
                        sheet.write(row, 3, str(item['Part Number']), formato)
                        sheet.write(row, 4, str(
                            item['Serial Number']), formato)
                        sheet.write(row, 5, str(
                            item['Classificação']), formato)
                        sheet.write(row, 6, str(item['Condição']), formato)
                        sheet.write(row, 7, str(item['Origem']), formato)
                        sheet.write(row, 8, str(item['Ajudante EPI']), formato)
                        sheet.write(row, 9, str(item['Placa']), formato)
                        sheet.write(row, 10, str(item['Observações']), formato)
                        sheet.write(row, 11, float(
                            item['Quantidade']), formato_number)
                        sheet.write(row, 12, float(
                            item['Valor Unit.']), formato_money)
                        sheet.write(row, 13, float(
                            item['Valor Total']), formato_money)

                        row += 1
                        linha_alternada = not linha_alternada

                    ultima_linha = len(df_prefixo) + 3
                    sheet.merge_range(
                        f'A{ultima_linha + 1}:M{ultima_linha + 1}', 'TOTAL', formatos['header'])
                    sheet.write(ultima_linha, 13, float(
                        df_prefixo['Valor Total'].sum()), formatos['total'])

            # Aba de Consumo
            df_consumo = df_periodo[df_periodo['Classificação']
                                    == 'CONS'].copy()
            if not df_consumo.empty:
                sheet_consumo = workbook.add_worksheet('Consumo')

                larguras_consumo = {
                    'A:A': 15,  # Data
                    'B:B': 20,  # Nome
                    'C:C': 20,  # Modelo
                    'D:D': 15,  # Classificação
                    'E:E': 15,  # Condição
                    'F:F': 20,  # Origem
                    'G:G': 10,  # Quantidade
                    'H:H': 15,  # Valor Unit.
                    'I:I': 15,  # Valor Total
                }

                for col, width in larguras_consumo.items():
                    sheet_consumo.set_column(col, width)

                sheet_consumo.merge_range(
                    'A1:I1',
                    f'ITENS DE CONSUMO - {data_inicial} a {data_final}',
                    formatos['header']
                )

                colunas_consumo = [
                    'Data', 'Nome', 'Modelo', 'Classificação',
                    'Condição', 'Origem', 'Quantidade', 'Valor Unit.',
                    'Valor Total'
                ]

                for idx, col in enumerate(colunas_consumo):
                    sheet_consumo.write(2, idx, col, formatos['header'])

                linha_alternada = True
                row = 3
                for _, item in df_consumo.iterrows():
                    formato = formatos['data_clara'] if linha_alternada else formatos['data_escura']
                    formato_number = formatos['number_clara'] if linha_alternada else formatos['number_escura']
                    formato_money = formatos['money_clara'] if linha_alternada else formatos['money_escura']

                    sheet_consumo.write(row, 0, item['Data'], formatos['date'])
                    sheet_consumo.write(row, 1, str(item['Nome']), formato)
                    sheet_consumo.write(row, 2, str(item['Modelo']), formato)
                    sheet_consumo.write(row, 3, str(
                        item['Classificação']), formato)
                    sheet_consumo.write(row, 4, str(item['Condição']), formato)
                    sheet_consumo.write(row, 5, str(item['Origem']), formato)
                    sheet_consumo.write(row, 6, float(
                        item['Quantidade']), formato_number)
                    sheet_consumo.write(row, 7, float(
                        item['Valor Unit.']), formato_money)
                    sheet_consumo.write(row, 8, float(
                        item['Valor Total']), formato_money)

                    row += 1
                    linha_alternada = not linha_alternada

                ultima_linha = len(df_consumo) + 3
                sheet_consumo.merge_range(
                    f'A{ultima_linha + 1}:H{ultima_linha + 1}', 'TOTAL', formatos['header'])
                sheet_consumo.write(ultima_linha, 8, float(
                    df_consumo['Valor Total'].sum()), formatos['total'])

            # Criar aba única de compras com todas as classificações
            sheet_compras = workbook.add_worksheet('Compras')

            larguras_compras = {
                'A:A': 25,  # Nome
                'B:B': 20,  # Modelo
                'C:C': 20,  # Part Number
                'D:D': 15,  # Classificação
                'E:E': 15,  # Quantidade Total
                'F:F': 15,  # Valor Unit.
                'G:G': 20,  # Valor Total
                'H:H': 25,  # Origem
            }

            for col, width in larguras_compras.items():
                sheet_compras.set_column(col, width)

            sheet_compras.merge_range(
                'A1:H1',
                f'LISTA DE COMPRAS BASEADA NAS SAÍDAS DO PERÍODO - {
                    data_inicial} a {data_final}',
                formatos['header']
            )

            headers_compras = ['Nome', 'Modelo', 'Part Number', 'Classificação',
                               'Quantidade Total', 'Valor Unit.', 'Valor Total',
                               'Origem']

            for idx, header in enumerate(headers_compras):
                sheet_compras.write(2, idx, header, formatos['header'])

            row = 3
            valor_total_geral = 0
            totais_por_classificacao = {}

            classificacoes_ordem = ['AERO', 'AUTO', 'EPI', 'CONS']
            classificacoes_existentes = [
                c for c in classificacoes_ordem if c in df_periodo['Classificação'].unique()]

            row += 1

            for classificacao in classificacoes_existentes:
                df_class = df_periodo[df_periodo['Classificação']
                                      == classificacao].copy()

                sheet_compras.merge_range(f'A{row}:H{row}', f'Classificação: {
                                          classificacao}', formatos['subheader'])
                row += 1

                df_itens = df_class.groupby(['Nome', 'Modelo', 'Part Number', 'Valor Unit.', 'Origem']).agg({
                    'Quantidade': 'sum'
                }).reset_index()

                df_itens['Valor Total'] = df_itens['Quantidade'] * \
                    df_itens['Valor Unit.']
                df_itens = df_itens.sort_values(['Origem', 'Nome'])

                linha_alternada = True
                for _, item in df_itens.iterrows():
                    formato = formatos['data_clara'] if linha_alternada else formatos['data_escura']
                    formato_number = formatos['number_clara'] if linha_alternada else formatos['number_escura']
                    formato_money = formatos['money_clara'] if linha_alternada else formatos['money_escura']

                    sheet_compras.write(row, 0, str(item['Nome']), formato)
                    sheet_compras.write(row, 1, str(item['Modelo']), formato)
                    sheet_compras.write(row, 2, str(
                        item['Part Number']), formato)
                    sheet_compras.write(row, 3, classificacao, formato)
                    sheet_compras.write(row, 4, float(
                        item['Quantidade']), formato_number)
                    sheet_compras.write(row, 5, float(
                        item['Valor Unit.']), formato_money)
                    sheet_compras.write(row, 6, float(
                        item['Valor Total']), formato_money)
                    sheet_compras.write(row, 7, str(item['Origem']), formato)

                    row += 1
                    linha_alternada = not linha_alternada

                total_classificacao = df_itens['Valor Total'].sum()
                totais_por_classificacao[classificacao] = total_classificacao
                sheet_compras.merge_range(
                    f'A{row + 1}:F{row + 1}', f'Total {classificacao}', formatos['total'])
                sheet_compras.write(row, 6, float(
                    total_classificacao), formatos['total'])
                sheet_compras.write(row, 7, '', formatos['total'])
                row += 1

                row += 1

                valor_total_geral += total_classificacao

            row += 1

            sheet_compras.merge_range(
                f'A{row}:E{row}', 'TOTAL GERAL ESTIMADO:', formatos['total_geral'])
            sheet_compras.merge_range(
                f'F{row}:G{row}', valor_total_geral, formatos['total_geral'])

            row += 1

            sheet_compras.merge_range(f'A{row}:G{
                                      row}', '* Valores podem variar conforme fornecedor e data da compra', formatos['data_clara'])

            writer.close()
            logging.info(f"Relatório gerado com sucesso: {caminho_completo}")
            print(f"\nRelatório gerado com sucesso!")
            print(f"Caminho: {caminho_completo}")
            return caminho_completo

        except Exception as e:
            logging.error(f"Erro ao gerar Excel: {str(e)}")
            print(f"Erro ao gerar arquivo Excel: {str(e)}")
            return None

    except Exception as e:
        logging.error(f"Erro inesperado: {str(e)}")
        print(f"Erro inesperado: {str(e)}")
        return None


def executar_relatorio():
    """
    Função principal para execução do relatório
    """
    while True:
        try:
            print("\n=== Geração de Relatórios de Saídas ===")

            data_inicial = input("Data inicial (DD/MM/AAAA ou 'cancelar'): ")
            if data_inicial.lower() == 'cancelar':
                return

            data_final = input("Data final (DD/MM/AAAA ou 'cancelar'): ")
            if data_final.lower() == 'cancelar':
                return

            # Valida formato das datas
            try:
                datetime.strptime(data_inicial, "%d/%m/%Y")
                datetime.strptime(data_final, "%d/%m/%Y")
            except ValueError:
                print("Erro: Use o formato DD/MM/AAAA!")
                continue

            # Verifica se a pasta de relatórios existe/pode ser criada
            if not criar_pasta_relatorios():
                print("Erro: Não foi possível criar/acessar a pasta de relatórios")
                return

            caminho = gerar_relatorio_saidas(data_inicial, data_final)

            if caminho:
                print(f"\nRelatório gerado com sucesso!")
                print("Deseja abrir a pasta de relatórios? (s/n): ")
                if input().lower() == 's':
                    abrir_pasta_relatorios()
                return

            retry = input("\nDeseja tentar novamente? (s/n): ")
            if retry.lower() != 's':
                break

        except Exception as e:
            print(f"\nErro inesperado: {str(e)}")
            break


def abrir_pasta_relatorios():
    """
    Abre a pasta de relatórios no explorador de arquivos do sistema
    """
    try:
        # Cria/obtém o caminho da pasta de relatórios
        caminho_relatorios = criar_pasta_relatorios()
        if not caminho_relatorios:
            return False

        try:
            # Tenta abrir a pasta de acordo com o sistema operacional
            if os.name == 'nt':  # Windows
                os.startfile(os.path.normpath(caminho_relatorios))
            elif sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', caminho_relatorios])
            else:  # linux/unix
                subprocess.Popen(['xdg-open', caminho_relatorios])

            print(f"Pasta de relatórios aberta: {caminho_relatorios}")
            return True

        except Exception as e:
            print(f"Não foi possível abrir a pasta automaticamente.")
            print(f"Você pode acessar a pasta manualmente em: {
                  caminho_relatorios}")
            print(f"Erro: {str(e)}")
            return False

    except Exception as e:
        print(f"Erro ao acessar a pasta de relatórios: {str(e)}")
        return False


if __name__ == "__main__":
    executar_relatorio()


@verificar_cancelamento
def buscar_saida_por_pn():
    """
    Busca saídas de peças por Part Number ou Prefixo de Aeronave a partir de uma data inicial
    """
    limpar_tela()
    print("\n=== Busca de Saídas ===")
    print("1. Buscar por Part Number")
    print("2. Buscar por Prefixo de Aeronave")

    opcao = input("Escolha uma opção (1-2): ").strip()
    if opcao.lower() == 'cancelar':
        return

    try:
        data_inicial = input(
            "A partir de qual data deseja buscar (DD/MM/AAAA): ")
        if data_inicial.lower() == 'cancelar':
            return

        try:
            with open('backup/estoque_saidas.json', 'r') as f:
                saidas = json.load(f)
        except FileNotFoundError:
            print("Arquivo de saídas não encontrado!")
            input("\nPressione Enter para continuar...")
            return

        try:
            data_inicial_dt = datetime.strptime(data_inicial, "%d/%m/%Y")
        except ValueError:
            print("Formato de data inválido! Use DD/MM/AAAA")
            input("\nPressione Enter para continuar...")
            return

        # Filtra saídas com base na opção escolhida
        if opcao == '1':
            termo_busca = input("Digite o Part Number: ").strip()
            if termo_busca.lower() == 'cancelar':
                return

            saidas_filtradas = [
                saida for saida in saidas
                if saida.get('partNumber') and saida['partNumber'].lower() == termo_busca.lower()
                and datetime.strptime(saida['data'], "%d/%m/%Y %H:%M:%S") >= data_inicial_dt
            ]
            filtro_texto = f"PN {termo_busca}"

        elif opcao == '2':
            termo_busca = input("Digite o Prefixo da Aeronave: ").strip()
            if termo_busca.lower() == 'cancelar':
                return

            saidas_filtradas = [
                saida for saida in saidas
                if saida.get('prefixo_aviao') and saida['prefixo_aviao'].lower() == termo_busca.lower()
                and datetime.strptime(saida['data'], "%d/%m/%Y %H:%M:%S") >= data_inicial_dt
            ]
            filtro_texto = f"Prefixo {termo_busca}"
        else:
            print("Opção inválida!")
            input("\nPressione Enter para continuar...")
            return

        limpar_tela()

        if not saidas_filtradas:
            print(f"Nenhuma saída encontrada para {
                  filtro_texto} a partir de {data_inicial}")
            input("\nPressione Enter para continuar...")
            return

        # Imprime resultados
        print(f"\n=== Saídas de {filtro_texto} ===")
        print("=" * 50)

        for saida in saidas_filtradas:
            print(f"Data/Hora: {saida['data']}")
            print(f"Nome: {saida['nome']}")
            print(f"Modelo: {saida['modelo']}")
            print(f"Part Number: {saida.get('partNumber', 'N/A')}")
            print(f"Serial Number: {saida.get('serialNumber', 'N/A')}")
            print(f"Quantidade: {saida['quantidade']}")
            print(f"Valor Unitário: R$ {saida['valor']:.2f}")
            print(f"Prefixo Avião: {saida.get('prefixo_aviao', 'N/A')}")
            print("=" * 50)

        # Estatísticas
        total_saidas = len(saidas_filtradas)
        total_quantidade = sum(saida['quantidade']
                               for saida in saidas_filtradas)
        total_valor = sum(saida['quantidade'] * saida['valor']
                          for saida in saidas_filtradas)

        # Coleta de Part Numbers únicos
        pns_unicos = sorted(set(saida.get('partNumber', 'N/A')
                            for saida in saidas_filtradas if saida.get('partNumber')))

        print("\n=== Resumo ===")
        print(f"Total de Saídas: {total_saidas}")
        print(f"Quantidade Total: {total_quantidade}")
        print(f"Valor Total: R$ {total_valor:.2f}")
        print(f"Part Numbers Utilizados: {', '.join(pns_unicos)}")

        input("\nPressione Enter para continuar...")

    except Exception as e:
        print(f"Erro inesperado: {e}")
        input("\nPressione Enter para continuar...")
        print(f"Erro inesperado: {e}")
        input("\nPressione Enter para continuar...")
