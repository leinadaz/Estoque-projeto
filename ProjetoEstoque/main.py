import os
import sys
from estoque import banco, operacoes, backup


def exibir_menu():
    print("\n" + "=" * 40)
    print("Gerenciador de Estoque".center(40))
    print("=" * 40)
    print("\nSelecione uma ação: ")
    opcoes = [
        "Inserir novo produto",
        "Registrar expedição",
        "Realizar descarte",
        "Visualizar estoque",
        "Editar produto",
        "Localizar produto",
        "Consultar expedições por P. Number",
        "Remover produto",
        "Gerar relatório",
        "Explorar pasta de relatórios",
        "Salvar e encerrar sistema..."
    ]

    for i, opcao in enumerate(opcoes, 1):
        print(f"{i}. {opcao}")


def main():
    banco.carregar_dados()

    while True:
        exibir_menu()

        try:
            escolha = int(input("\nEscolha a opção (1-11): "))

            acoes = {
                1: operacoes.adicionar_produto,
                2: operacoes.registrar_saida,
                3: operacoes.registrar_descarte,
                4: operacoes.mostrar_estoque,
                5: operacoes.editar_produto,
                6: operacoes.buscar_produto,
                7: operacoes.buscar_saida_por_pn,
                8: operacoes.excluir_produto,
                9: operacoes.executar_relatorio,
                10: operacoes.abrir_pasta_relatorios,
                11: lambda: (print("Encerrando sistema..."), backup.salvar_backup(), exit())
            }

            if escolha in acoes:
                acoes[escolha]()
            else:
                print("Opção inválida. Por favor, tente novamente inserindo um número válido...")

        except ValueError:
            print("Entrada inválida. Digite um número de 1 a 11.")


if __name__ == "__main__":
    main()
