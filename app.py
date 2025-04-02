from app import create_app

app = create_app()


# TODO: formula of height,calores,weight
# TODO: tem um negocio aí do dashboard que excluir e remover sao diferentes na parte do banco de dados
# TODO: quero que ao adicionar fique bonitinho que nem quando atualiza
# TODO: Quando o identificador tem um numero da bug
if __name__ == "__main__":
    app.run(debug=True)
