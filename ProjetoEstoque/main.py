import os
from estoque import banco, operacoes
from estoque import backup


def main():
    # Carregar dados do estoque, entradas, saídas e descartes
    banco.carregar_dados()

    while True:
        # Menu de opções para o usuário
        print("\n=================================")
        print("Bem-Vindo ao sistema de estoque! ")
        print("=================================")
        print("\nEscolha uma operação: ")
        print("1. Adicionar produto ao estoque")
        print("2. Registrar saída de produto")
        print("3. Registrar descarte de produto")
        print("4. Mostrar estoque")
        print("5. Editar produto")
        print("6. Buscar produto")
        print("7. Excluir produto")
        print("8. Fazer backup")
        print("9. Sair\n")

        escolha = input("Escolha a opção (1-9): ")

        if escolha == '1':
            operacoes.adicionar_produto()
        elif escolha == '2':
            operacoes.registrar_saida()
        elif escolha == '3':
            operacoes.registrar_descarte()
        elif escolha == '4':
            operacoes.mostrar_estoque()
        elif escolha == '5':
            operacoes.editar_produto()
        elif escolha == '6':
            operacoes.buscar_produto()
        elif escolha == '7':
            operacoes.excluir_produto()
        elif escolha == '8':
            backup.salvar_backup()
        elif escolha == '9':
            print("Saindo...")
            backup.salvar_backup()  # Salva backup antes de sair
            break
        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    main()
