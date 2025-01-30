# imports

import keyboard
import os
from datetime import datetime
import json
from estoque import banco

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

# verificar cancelamento

def verificar_cancelamento(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, str) and result.strip().lower() == 'cancelar':
            limpar_tela()
            print("Processo cancelado.")
        return result
    return wrapper

# selecionar classificação

@verificar_cancelamento
def selecionar_classificacao():
    while True:
        print("\nSelecione a classificação do produto:")
        print("1. Produto Aero")
        print("2. Produto Auto")
        print("3. EPI")
        opcao = input("Escolha a opção (1-3): ").strip()

        if opcao == "1":
            return "AERO"
        elif opcao == "2":
            return "AUTO"
        elif opcao == "3":
            return "EPI"
        else:
            print("Opção inválida! Tente novamente.")

# adicionar produto

@verificar_cancelamento
def adicionar_produto():
    limpar_tela()
    print("===========================================================")
    print("Entrada ao estoque, sobre o produto, digite o que se pede: ")
    print("===========================================================")

    classificacao = selecionar_classificacao()
    if classificacao.lower() == 'cancelar':
        return

    produto = {
        'classificacao': classificacao,
        'nome': '',
        'modelo': '',
        'valor': 0,
        'quantidade': 0,
        'origem': '',
        'data': datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }

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
        produto['partNumber'] = input("PartNumber----> ")
        if produto['partNumber'].lower() == 'cancelar':
            return
        produto['serialNumber'] = input("SerialNumber--> ")
        if produto['serialNumber'].lower() == 'cancelar':
            return

    # Verificar se o produto já existe no estoque
    produto_existente = None
    for p in banco.estoque:
        match_basico = (p['nome'] == produto['nome'] and 
                       p['modelo'] == produto['modelo'] and 
                       p['classificacao'] == produto['classificacao'])
        
        if classificacao == "AERO":
            if match_basico and p.get('partNumber') == produto.get('partNumber'):
                produto_existente = p
                break
        else:
            if match_basico:
                produto_existente = p
                break

    if produto_existente:
        produto_existente['quantidade'] += produto['quantidade']
        print(f"Quantidade do produto {produto['nome']} atualizada com sucesso!")
    else:
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

@verificar_cancelamento
def registrar_saida():
    limpar_tela()
    print("===========================================================")
    print("Saída de produto do estoque. Escolha uma opção de busca: ")
    print("1 - Buscar por Nome")
    print("2 - Buscar por Modelo")
    print("===========================================================")

    opcao_busca = input("Digite a opção desejada (1/2): ")
    if opcao_busca.lower() == "cancelar":
        return

    termo_busca = input("Digite o termo de busca: ")
    if termo_busca.lower() == "cancelar":
        return

    # Filtra os produtos com base na opção selecionada
    resultados = []
    if opcao_busca == "1":
        resultados = [p for p in banco.estoque if termo_busca.lower() in p['nome'].lower()]
    elif opcao_busca == "2":
        resultados = [p for p in banco.estoque if termo_busca.lower() in p['modelo'].lower()]
    else:
        print("Opção inválida! Tente novamente.")
        return

    if not resultados:
        print("Nenhum produto encontrado com o termo de busca informado.")
        return

    limpar_tela()
    print("\nProdutos encontrados:")
    for i, produto in enumerate(resultados):
        print(f"{i + 1} - Nome: {produto['nome']}, Modelo: {produto['modelo']}, "
              f"Quantidade: {produto['quantidade']}")

    try:
        escolha = int(input("\nSelecione o número do produto que deseja registrar a saída: ")) - 1
        produto_selecionado = resultados[escolha]
    except (ValueError, IndexError):
        print("Seleção inválida! Tente novamente.")
        return

    limpar_tela()
    print("\nProduto selecionado:")
    for chave, valor in produto_selecionado.items():
        print(f"{chave.capitalize()}: {valor}")

    try:
        limpar_tela()
        quantidade_saida = int(input("\nDigite a quantidade a ser retirada: "))
        if quantidade_saida > produto_selecionado['quantidade']:
            print("Quantidade insuficiente no estoque!")
            return

        prefixo_aviao = input("Digite o prefixo do avião: ")
        if prefixo_aviao.lower() == "cancelar":
            return

        # Define a pasta de destino geral do avião
        pasta_destino = f"backup/{prefixo_aviao}"

        # Prepara o registro de saída
        saida = {
            'data_hora': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'nome': produto_selecionado['nome'],
            'modelo': produto_selecionado['modelo'],
            'quantidade': quantidade_saida,
            'valor': produto_selecionado['valor'],
            'classificacao': produto_selecionado['classificacao'],
            'prefixo_aviao': prefixo_aviao
        }

        # Adiciona campos específicos por classificação
        if produto_selecionado['classificacao'] == "AERO":
            saida['partNumber'] = produto_selecionado.get('partNumber')
            saida['serialNumber'] = produto_selecionado.get('serialNumber')

        # Atualiza a quantidade no estoque
        produto_selecionado['quantidade'] -= quantidade_saida

        # Se a quantidade chegar a 0, remove o produto do estoque
        if produto_selecionado['quantidade'] == 0:
            banco.estoque.remove(produto_selecionado)
            print(f"Produto {produto_selecionado['nome']} removido do estoque por atingir quantidade 0.")

        banco.salvar_dados()

        # Cria pasta de destino se não existir
        if not os.path.exists(pasta_destino):
            os.makedirs(pasta_destino)

        # Salva no arquivo de log de saídas (estoque_saidas.json)
        arquivo_log = 'backup/estoque_saidas.json'
        if not os.path.exists(arquivo_log):
            with open(arquivo_log, 'w') as f:
                json.dump([], f)

        with open(arquivo_log, 'r+') as f:
            dados = json.load(f)
            dados.append(saida)
            f.seek(0)
            json.dump(dados, f, indent=4)

        # Salva todas as saídas dentro do saidas.json do avião
        arquivo_aviao = f"{pasta_destino}/saidas.json"
        if not os.path.exists(arquivo_aviao):
            with open(arquivo_aviao, 'w') as f:
                json.dump([], f)

        with open(arquivo_aviao, 'r+') as f:
            dados = json.load(f)
            dados.append(saida)
            f.seek(0)
            json.dump(dados, f, indent=4)

        limpar_tela()
        print("\nSaída registrada com sucesso!")

    except ValueError:
        print("Quantidade inválida! Tente novamente.")

# Função para registrar o descarte de um produto

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
        return

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
            print(f"Placa        : {produto.get('placa_camionete', 'N/A')}")
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

# função de busca de produto

@verificar_cancelamento
def buscar_produto():
    limpar_tela()
    print("\nBuscar produto no estoque:")
    print("1. Buscar por Nome")
    print("2. Buscar por Modelo")
    print("3. Buscar por Classificação")
    opcao = input("Escolha uma opção (1-3): ")

    if opcao.lower() == "cancelar":
        return

    if opcao == "3":
        classificacao = selecionar_classificacao()
        resultados = [
            p for p in banco.estoque if p['classificacao'] == classificacao]
    else:
        termo_busca = input("Digite o termo de busca: ").strip()
        if termo_busca.lower() == "cancelar":
            return

        if opcao == "1":
            resultados = [
                p for p in banco.estoque if termo_busca.lower() in p['nome'].lower()]
        elif opcao == "2":
            resultados = [
                p for p in banco.estoque if termo_busca.lower() in p['modelo'].lower()]
        else:
            print("Opção inválida.")
            return

    if resultados:
        print("\nProdutos encontrados:")
        for produto in resultados:
            print("\n" + "=" * 40)
            for chave, valor in produto.items():
                print(f"{chave.capitalize()}: {valor}")
    else:
        print("Nenhum produto encontrado.")

# editar produto

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
