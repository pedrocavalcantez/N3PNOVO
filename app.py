from app import create_app

app = create_app()


# TODO: formula of height,calores,weight
# TODO: Quando o identificador tem um numero da bug
# BUG : se colcoar uma dieta e depois colcoar outra com nome diferente ele nao atualzia

if __name__ == "__main__":
    app.run(debug=True)
