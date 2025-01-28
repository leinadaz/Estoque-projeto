import keyboard
import os
from datetime import datetime
import json
from estoque import banco


def limpar_tela():
    """Função para limpar a tela do terminal."""
    sistema = os.name
    if sistema == "nt":  # Para Windows
        os.system("cls")
    else:  # Para sistemas Unix (Linux, MacOS)
        os.system("clear")

# Função para adicionar um produto ao estoque


def adicionar_produto():
    limpar_tela()
    print("\n===========================================================")
    print("Entrada ao estoque, sobre o produto, digite o que se pede: ")
    print("Digite 'cancelar' a qualquer momento para voltar ao menu.")
    print("===========================================================")

    partNumber = input("PartNumber----> ")
    if partNumber.lower() == 'cancelar':  # Se digitar "cancelar", volta ao menu
        print("Operação cancelada.")
        return

    nome = input("Nome----------> ")
    if nome.lower() == 'cancelar':  # Se digitar "cancelar", volta ao menu
        print("Operação cancelada.")
        return

    modelo = input("Modelo--------> ")
    if modelo.lower() == 'cancelar':  # Se digitar "cancelar", volta ao menu
        print("Operação cancelada.")
        return

    serialNumber = input("SerialNumber--> ")
    if serialNumber.lower() == 'cancelar':  # Se digitar "cancelar", volta ao menu
        print("Operação cancelada.")
        return

    quantidade = input("Quantidade----> ")
    if quantidade.lower() == 'cancelar':  # Se digitar "cancelar", volta ao menu
        print("Operação cancelada.")
        return
    quantidade = int(quantidade)

    valor = input("Valor Unidade-> ")
    if valor.lower() == 'cancelar':  # Se digitar "cancelar", volta ao menu
        print("Operação cancelada.")
        return
    valor = float(valor)

    origem = input("Origem--------> ")
    if origem.lower() == 'cancelar':  # Se digitar "cancelar", volta ao menu
        print("Operação cancelada.")
        return

    print("================================")
    print("Produto adicionado com sucesso! ")
    print("================================")

    produto = {
        'partNumber': partNumber,
        'nome': nome,
        'modelo': modelo,
        'serialNumber': serialNumber,
        'quantidade': quantidade,
        'valor': valor,
        'origem': origem
    }

    # Verifica se o produto já existe no estoque
    produto_existente = None
    for p in banco.estoque:
        if p['partNumber'] == produto['partNumber'] and p['nome'] == produto['nome'] and p['modelo'] == produto['modelo']:
            produto_existente = p
            break

    if produto_existente:
        # Se o produto já existir, soma a quantidade
        produto_existente['quantidade'] += produto['quantidade']
        print(f"Quantidade do produto {
              produto['nome']} atualizada com sucesso!")
    else:
        # Caso não exista, adiciona o produto normalmente
        banco.estoque.append(produto)
        print(f"Produto {produto['nome']} adicionado com sucesso!")

    banco.salvar_dados()

    # Registro do log de entrada
    log = {
        'data': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'partNumber': partNumber,
        'nome': nome,
        'modelo': modelo,
        'serialNumber': serialNumber,
        'quantidade': quantidade,
        'valor': valor,
        'origem': origem
    }

    arquivo_log = 'backup/estoque_entradas.json'

    # Verifica se o diretório 'backup' existe, se não, cria
    if not os.path.exists('backup'):
        os.makedirs('backup')

    # Verifica se o arquivo de log existe, se não, cria
    if not os.path.exists(arquivo_log):
        with open(arquivo_log, 'w') as file:
            json.dump([], file)

    with open(arquivo_log, 'r+') as file:
        logs = json.load(file)
        logs.append(log)
        file.seek(0)
        json.dump(logs, file, indent=4)


# Função para registrar a saída de um produto


def registrar_saida():
    limpar_tela()
    print("\n===========================================================")
    print("Saída de produto do estoque. Escolha uma opção de busca: ")
    print("1 - Buscar por PartNumber")
    print("2 - Buscar por Nome")
    print("3 - Buscar por Modelo")
    print("===========================================================")

    opcao_busca = input("Digite a opção desejada (1/2/3): ")
    if opcao_busca.lower() == "cancelar":
        print("Operação de saída cancelada.")
        return
    termo_busca = input("Digite o termo de busca: ")
    if termo_busca.lower() == "cancelar":
        print("Operação de saída cancelada.")
        return

    # Filtra os produtos com base na opção selecionada
    if opcao_busca == "1":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['partNumber'].lower()]
    elif opcao_busca == "2":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['nome'].lower()]
    elif opcao_busca == "3":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['modelo'].lower()]
    else:
        print("Opção inválida! Tente novamente.")
        return

    if not resultados:
        print("Nenhum produto encontrado com o termo de busca informado.")
        return

    # Exibe os resultados encontrados
    print("\nProdutos encontrados:")
    for i, produto in enumerate(resultados):
        print(f"{i + 1} - PartNumber: {produto['partNumber']}, Nome: {produto['nome']}, Modelo: {produto['modelo']}, Quantidade: {produto['quantidade']}")

    # Seleciona o produto desejado
    try:
        escolha = int(input("Selecione o número do produto que deseja registrar a saída: ")) - 1
        if escolha == "cancelar":
            print("Operação de saída cancelada.")
            return
        produto_selecionado = resultados[escolha]
    except (ValueError, IndexError):
        print("Seleção inválida! Tente novamente.")
        return

    # Exibe os detalhes do produto antes de registrar a saída
    print("\nProduto selecionado:")
    for chave, valor in produto_selecionado.items():
        print(f"{chave.capitalize()}: {valor}")

    # Registra a saída
    try:
        quantidade_saida_str = input("\nDigite a quantidade a ser retirada: ")
        if quantidade_saida_str.lower() == "cancelar":
            print("Operação de saída cancelada.")
            return

        quantidade_saida = int(quantidade_saida_str)

        if quantidade_saida > produto_selecionado['quantidade']:
            print("Quantidade insuficiente no estoque!")
            return

        prefixo_aviao = input("Digite o prefixo do avião para o qual a peça está sendo enviada: ")
        if prefixo_aviao.lower() == "cancelar":
            print("Operação de saída cancelada.")
            return
        
        # Se o usuário não inserir uma data/hora, usar a atual
        data_hora_str = input("Digite a data e hora (ou pressione Enter para usar a atual): ")

        if data_hora_str.strip():
            data_hora = data_hora_str
        else:
            data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        # Atualiza a quantidade no estoque
        produto_selecionado['quantidade'] -= quantidade_saida

        # Se a quantidade chegar a 0, remove o produto do estoque
        if produto_selecionado['quantidade'] == 0:
            banco.estoque.remove(produto_selecionado)
            print(f"Produto {produto_selecionado['nome']} removido do estoque por atingir quantidade 0.")

        # Registra no log de saídas
        banco.saidas.append({
            'data_hora': data_hora,
            'partNumber': produto_selecionado['partNumber'],
            'nome': produto_selecionado['nome'],
            'modelo': produto_selecionado['modelo'],
            'quantidade': quantidade_saida,
            'prefixo_aviao': prefixo_aviao
        })

        # Salvar no arquivo estoque_saidas.json (na pasta backup)
        backup_path = "backup/estoque_saidas.json"
        if not os.path.exists("backup"):
            os.makedirs("backup")

        if not os.path.exists(backup_path):
            with open(backup_path, 'w') as f:
                json.dump([], f)  # Cria um arquivo vazio se não existir

        # Atualizar estoque_saidas.json com a nova saída
        with open(backup_path, 'r+') as f:
            dados_estoque = json.load(f)
            dados_estoque.append({
                'data_hora': data_hora,
                'partNumber': produto_selecionado['partNumber'],
                'nome': produto_selecionado['nome'],
                'modelo': produto_selecionado['modelo'],
                'quantidade': quantidade_saida,
                'prefixo_aviao': prefixo_aviao
            })
            f.seek(0)
            json.dump(dados_estoque, f, indent=4)

        # Criar pasta do avião, se não existir
        pasta_aviao = f"backup/{prefixo_aviao}"
        if not os.path.exists(pasta_aviao):
            os.makedirs(pasta_aviao)

        # Salva no arquivo do avião
        arquivo_log_saida_aviao = f"{pasta_aviao}/saidas_{prefixo_aviao}.json"
        if not os.path.exists(arquivo_log_saida_aviao):
            with open(arquivo_log_saida_aviao, 'w') as file:
                json.dump([], file)

        # Salva a saída no arquivo do avião
        with open(arquivo_log_saida_aviao, 'r+') as file:
            logs = json.load(file)
            logs.append({
                'data_hora': data_hora,
                'partNumber': produto_selecionado['partNumber'],
                'nome': produto_selecionado['nome'],
                'modelo': produto_selecionado['modelo'],
                'quantidade': quantidade_saida,
                'prefixo_aviao': prefixo_aviao
            })
            file.seek(0)
            json.dump(logs, file, indent=4)

        print("\nSaída registrada com sucesso!")

    except ValueError:
        print("Quantidade inválida! Tente novamente.")




# Função para registrar o descarte de um produto

def registrar_descarte():
    limpar_tela()
    print("===========================================")
    print("Descarte de produto. Escolha uma opção de busca:")
    print("1 - Buscar por PartNumber")
    print("2 - Buscar por Nome")
    print("3 - Buscar por Modelo")
    print("===========================================")

    opcao_busca = input("Digite a opção desejada (1/2/3): ")
    if opcao_busca.lower() == "cancelar":
        print("Operação cancelada.")
        return

    termo_busca = input("Digite o termo de busca: ")
    if termo_busca.lower() == "cancelar":
        print("Operação cancelada.")
        return

    # Filtra os produtos com base na opção selecionada
    if opcao_busca == "1":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['partNumber'].lower()]
    elif opcao_busca == "2":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['nome'].lower()]
    elif opcao_busca == "3":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['modelo'].lower()]
    else:
        print("Opção inválida! Tente novamente.")
        return

    if not resultados:
        print("Nenhum produto encontrado com o termo de busca informado.")
        return

    # Exibe os resultados encontrados
    print("\nProdutos encontrados:")
    for i, produto in enumerate(resultados):
        print(f"{i + 1} - PartNumber: {produto['partNumber']}, Nome: {
              produto['nome']}, Modelo: {produto['modelo']}, Quantidade: {produto['quantidade']}")

    try:
        escolha = int(
            input("Selecione o número do produto que deseja registrar o descarte: ")) - 1
        if escolha < 0 or escolha >= len(resultados):
            print("Seleção inválida! Operação cancelada.")
            return
        produto_selecionado = resultados[escolha]
    except (ValueError, IndexError):
        print("Seleção inválida! Tente novamente.")
        return

    # Exibe os detalhes do produto selecionado
    print("\nProduto selecionado:")
    for chave, valor in produto_selecionado.items():
        print(f"{chave.capitalize()}: {valor}")

    # Solicita a quantidade
    try:
        quantidade = int(input("\nDigite a quantidade a ser descartada: "))
        if str(quantidade).lower() == "cancelar":
            print("Operação cancelada.")
            return
        if quantidade > produto_selecionado['quantidade']:
            print("Quantidade insuficiente para descarte!")
            return
    except ValueError:
        print("Quantidade inválida! Tente novamente.")
        return

    # Solicita o motivo do descarte
    motivo = input("Motivo do descarte-> ")
    if motivo.lower() == "cancelar":
        print("Operação cancelada.")
        return

    # Atualiza a quantidade no estoque
    produto_selecionado['quantidade'] -= quantidade

    # Se a quantidade chegar a 0, remove o produto do estoque
    if produto_selecionado['quantidade'] == 0:
        banco.estoque.remove(produto_selecionado)
        print(f"Produto {
              produto_selecionado['nome']} removido do estoque por atingir quantidade 0.")

    # Registra o descarte no banco
    descarte_item = {
        'data': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'produto': produto_selecionado['nome'],
        'modelo': produto_selecionado['modelo'],
        'quantidade': quantidade,
        'motivo': motivo
    }

    banco.descarte.append(descarte_item)
    banco.salvar_dados()

    print("Descarte registrado com sucesso!")


# Função para mostrar o estoque

def mostrar_estoque():
    limpar_tela()
    print("\nEstoque atual:\n")
    if not banco.estoque:
        print("O estoque está vazio.")
        return

    for produto in banco.estoque:
        # Só mostrar produtos com quantidade maior que 0
        if produto['quantidade'] > 0:
            print("=" * 40)  # Linha de separação
            print(f"PartNumber   : {produto['partNumber']}")
            print(f"Nome         : {produto['nome']}")
            print(f"Modelo       : {produto['modelo']}")
            print(f"SerialNumber : {produto['serialNumber']}")
            print(f"Quantidade   : {produto['quantidade']}")
            print(f"Valor        : R${produto['valor']:.2f}")
            print(f"Origem       : {produto['origem']}")
            print("=" * 40)  # Linha de separação
    print("\nFim do estoque.")

# Função para editar produto


def editar_produto():
    limpar_tela()
    print("\nEditar produto no estoque:")
    print("1. Buscar por PartNumber")
    print("2. Buscar por Nome")
    print("3. Buscar por Modelo")
    opcao = input("Escolha uma opção (1-3): ").strip()

    if opcao.lower() == "cancelar":
        print("Edição cancelada.")
        return

    termo_busca = input("Digite o termo de busca: ").strip()
    if termo_busca.lower() == "cancelar":
        print("Edição cancelada.")
        return

    resultados = []

    # Busca pelo critério selecionado
    if opcao == "1":
        resultados = [produto for produto in banco.estoque if str(
            produto['partNumber']) == termo_busca]
    elif opcao == "2":
        resultados = [produto for produto in banco.estoque if termo_busca.lower(
        ) in produto['nome'].lower()]
    elif opcao == "3":
        resultados = [produto for produto in banco.estoque if termo_busca.lower(
        ) in produto['modelo'].lower()]
    else:
        print("Opção inválida.")
        return

    # Exibe os resultados encontrados
    if resultados:
        print("\nProdutos encontrados:")
        for idx, produto in enumerate(resultados):
            print(f"{idx + 1}. PartNumber: {produto['partNumber']} | Nome: {
                  produto['nome']} | Modelo: {produto['modelo']}")

        escolha = input(
            "Escolha o número do produto para editar (0 para cancelar): ").strip()
        if escolha.lower() == "cancelar":
            print("Edição cancelada.")
            return

        try:
            escolha = int(escolha)
            if escolha == 0:
                print("Edição cancelada.")
                return

            produto_selecionado = resultados[escolha - 1]

            # Mostra todos os valores do produto
            print("\nDados do produto selecionado:")
            for key, value in produto_selecionado.items():
                print(f"- {key}: {value}")

            # Seleciona qual campo editar
            print("\nCampos disponíveis para edição:")
            print("1. PartNumber")
            print("2. Nome")
            print("3. Modelo")
            print("4. SerialNumber")
            print("5. Quantidade")
            print("6. Valor Unidade")
            print("7. Origem")

            campo = input("Escolha o campo para editar (1-7): ").strip()
            if campo.lower() == "cancelar":
                print("Edição cancelada.")
                return

            novo_valor = input("Digite o novo valor: ").strip()
            if novo_valor.lower() == "cancelar":
                print("Edição cancelada.")
                return

            # Atualiza o campo selecionado
            if campo == "1":
                produto_selecionado['partNumber'] = novo_valor
            elif campo == "2":
                produto_selecionado['nome'] = novo_valor
            elif campo == "3":
                produto_selecionado['modelo'] = novo_valor
            elif campo == "4":
                produto_selecionado['serialNumber'] = novo_valor
            elif campo == "5":
                produto_selecionado['quantidade'] = int(novo_valor)
            elif campo == "6":
                produto_selecionado['valor'] = float(novo_valor)
            elif campo == "7":
                produto_selecionado['origem'] = novo_valor
            else:
                print("Campo inválido.")
                return

            # Salva as alterações no estoque
            banco.salvar_dados()
            print("Produto atualizado com sucesso!")
        except ValueError:
            print("Seleção inválida ou erro ao processar os dados. Tente novamente.")
    else:
        print("Nenhum produto encontrado com o termo informado.")

# Função que faz buscas no estoque


def buscar_produto():
    limpar_tela()
    print("\nBuscar produto no estoque:")
    print("1. Buscar por PartNumber")
    print("2. Buscar por Nome")
    print("3. Buscar por Modelo")
    opcao = input("Escolha uma opção (1-3): ")

    if opcao.lower() == "cancelar":
        print("Operação cancelada.")
        return

    termo_busca = input("Digite o termo de busca: ").strip()
    if termo_busca.lower() == "cancelar":
        print("Operação cancelada.")
        return

    resultados = []

    # Busca baseada na opção escolhida
    if opcao == "1":
        resultados = [
            produto for produto in banco.estoque if produto['partNumber'] == termo_busca]
    elif opcao == "2":
        resultados = [produto for produto in banco.estoque if termo_busca.lower(
        ) in produto['nome'].lower()]
    elif opcao == "3":
        resultados = [produto for produto in banco.estoque if termo_busca.lower(
        ) in produto['modelo'].lower()]
    else:
        print("Opção inválida.")
        return

    # Exibe os resultados
    if resultados:
        print("\nProdutos encontrados:")
        for produto in resultados:
            print(f"- PartNumber: {produto['partNumber']}")
            print(f"  Nome: {produto['nome']}")
            print(f"  Modelo: {produto['modelo']}")
            print(f"  SerialNumber: {produto['serialNumber']}")
            print(f"  Quantidade: {produto['quantidade']}")
            print(f"  Valor: {produto['valor']}")
            print(f"  Origem: {produto['origem']}\n")
    else:
        print("Nenhum produto encontrado.")

# Função para excluir produto do estoque


def excluir_produto():
    limpar_tela()
    print("\n===========================================================")
    print("Exclusão de produto do estoque. Escolha uma opção de busca: ")
    print("1 - Buscar por PartNumber")
    print("2 - Buscar por Nome")
    print("3 - Buscar por Modelo")
    print("===========================================================")

    opcao_busca = input("Digite a opção desejada (1/2/3): ").strip()
    if opcao_busca.lower() == "cancelar":
        print("Operação cancelada.")
        return

    termo_busca = input("Digite o termo de busca: ").strip()
    if termo_busca.lower() == "cancelar":
        print("Operação cancelada.")
        return

    # Filtra os produtos com base na opção selecionada
    if opcao_busca == "1":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['partNumber'].lower()]
    elif opcao_busca == "2":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['nome'].lower()]
    elif opcao_busca == "3":
        resultados = [p for p in banco.estoque if termo_busca.lower()
                      in p['modelo'].lower()]
    else:
        print("Opção inválida! Tente novamente.")
        return

    if not resultados:
        print("Nenhum produto encontrado com o termo de busca informado.")
        return

    # Exibe os resultados encontrados
    print("\nProdutos encontrados:")
    for i, produto in enumerate(resultados):
        print(f"{i + 1} - PartNumber: {produto['partNumber']}, Nome: {
              produto['nome']}, Modelo: {produto['modelo']}, Quantidade: {produto['quantidade']}")

    # Seleciona o produto desejado
    try:
        escolha = input(
            "Selecione o número do produto que deseja excluir (ou digite 'cancelar' para cancelar): ").strip()
        if escolha.lower() == "cancelar":
            print("Operação cancelada.")
            return

        escolha = int(escolha) - 1
        produto_selecionado = resultados[escolha]
    except (ValueError, IndexError):
        print("Seleção inválida! Tente novamente.")
        return

    # Exibe os detalhes do produto antes de excluir
    print("\nProduto selecionado para exclusão:")
    for chave, valor in produto_selecionado.items():
        print(f"{chave.capitalize()}: {valor}")

    # Confirmação de exclusão
    confirmar = input(
        "\nVocê tem certeza que deseja excluir este produto? (S/N ou 'cancelar' para cancelar): ").strip().lower()
    if confirmar == "cancelar":
        print("Operação cancelada.")
        return
    if confirmar != "s":
        print("Exclusão cancelada.")
        return

    # Remove o produto do estoque
    banco.estoque.remove(produto_selecionado)
    banco.salvar_dados()
    print(f"Produto {produto_selecionado['nome']
                     } removido do estoque com sucesso!")

    # Registro da exclusão no log (backup)
    log_exclusao = {
        'data_hora': datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        'acao': 'Exclusão',
        'partNumber': produto_selecionado['partNumber'],
        'nome': produto_selecionado['nome'],
        'modelo': produto_selecionado['modelo'],
        'quantidade': produto_selecionado['quantidade'],
    }

    arquivo_log_exclusao = 'backup/estoque_exclusoes.json'

    # Verifica se o diretório 'backup' existe, se não, cria
    if not os.path.exists('backup'):
        os.makedirs('backup')

    # Verifica se o arquivo de log existe, se não, cria
    if not os.path.exists(arquivo_log_exclusao):
        with open(arquivo_log_exclusao, 'w') as file:
            json.dump([], file)

    with open(arquivo_log_exclusao, 'r+') as file:
        logs = json.load(file)
        logs.append(log_exclusao)
        file.seek(0)
        json.dump(logs, file, indent=4)

    print(f"Exclusão registrada no backup de log.")
