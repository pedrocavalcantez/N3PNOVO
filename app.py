from app import create_app

app = create_app()


# TODO: formula of height,calores,weight
# TODO: Quando o identificador tem um numero da bug
# BUG : se colcoar uma dieta e depois colcoar outra com nome diferente ele nao atualzia


# TODO

# Criar um Alimetno Novo (só para pessoa que cadastrou)
# Alimentos favoritos
# VERIFICACAO por email
# Adicionar mais comidas que nao tem no banco de dados


# Fazer um slider para as calorias
# BUGSS
#Nao ta Exxportando excel 


if __name__ == "__main__":
    app.run(debug=True)
