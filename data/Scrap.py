import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import numpy as np


def get_table(url):
    # url_item=urls[5]
    # url_item="https://www.fatsecret.com.br"+url_item
    # url=url_item
    # url = "https://www.fatsecret.com.br/calorias-nutri%C3%A7%C3%A3o/gen%C3%A9rico/p%C3%A3o-com-manteiga"
    response = requests.get(url)
    while response.status_code == 429:
        time.sleep(1)
        response = requests.get(url)

    soup = BeautifulSoup(response.content, "html.parser")
    # Extract the div with class 'nutrition_facts international'
    nutrition_facts = soup.find("div", {"class": "nutrition_facts international"})
    data = []
    # Find all the nutrients and their values
    nutrients = nutrition_facts.find_all(
        "div", {"class": ["nutrient black left", "nutrient sub left"]}
    )
    values = nutrition_facts.find_all(
        "div", {"class": ["nutrient black right tRight", "nutrient right tRight"]}
    )
    for nutrient, value in zip(nutrients, values):
        data.append([nutrient.text.strip(), value.text.strip()])
    qtd = soup.find("div", {"class": "serving_size black serving_size_value"}).text
    data.append(["Quantidade", re.search(r"(\d+)\s*[gml]+", qtd).group(1)])
    data.append(["Nome", soup.find("h1", {"style": "text-transform:none"}).text])

    manufacturer = soup.find("h2", {"class": "manufacturer"})

    if manufacturer is None:
        manufacturer = "Nenhum"
    else:
        manufacturer = manufacturer.text

    data.append(["Marca", manufacturer])

    # Create a DataFrame
    df = pd.DataFrame(data, columns=["Nutrient", "Value"])

    df = df.transpose()
    df.columns = df.iloc[0, :]
    df = df.iloc[1:, :]

    if df.loc[:, "Marca"][0] != "Nenhum":
        df.loc[:, "identificador"] = df.loc[:, "Nome"] + "-" + df.loc[:, "Marca"]
    else:
        df.loc[:, "identificador"] = df.loc[:, "Nome"]

    columns_order = ["identificador", "Nome", "Quantidade", "Marca"] + [
        col
        for col in df.columns
        if col not in ["identificador", "Nome", "Quantidade", "Marca"]
    ]
    df = df[columns_order]
    df.reset_index(inplace=True, drop=True)
    return df
    # df.pivot(index='Nutrient', columns='Value', values='Value')
    # Display the DataFrame


# url_search = "https://www.fatsecret.com.br/calorias-nutri%C3%A7%C3%A3o/search?q=coca+cola"
df_x = pd.DataFrame()
urls_possiveis = []


alimentos = [
    "abacate",
    "abacaxi",
    "abadejo",
    "abiu",
    "abóbora",
    "abobrinha",
    "açai",
    "açaí",
    "acelga",
    "acerola",
    "achocolatado",
    "açucar",
    "açúcar",
    "agrião",
    "aipo",
    "alface",
    "alfavaca",
    "alho",
    "alho-poró",
    "almeirão",
    "ameixa",
    "amêndoa",
    "amendoim",
    "amido de milho",
    "arroz",
    "atemóia",
    "atum",
    "aveia",
    "azeite",
    "azeitona",
    "bacalhau",
    "baião de dois",
    "banana",
    "barra de cereal",
    "batata",
    "batata doce",
    "bebida isotônica",
    "bebida láctea",
    "berinjela",
    "beterraba",
    "bife à cavalo",
    "biscoito",
    "bolacha",
    "bolacha maria",
    "bolo",
    "brócolis",
    "cação",
    "cacau",
    "café",
    "cajá",
    "cajá-manga",
    "caju",
    "caldo de carne",
    "caldo de galinha",
    "camarão",
    "cana",
    "canjica",
    "capuccino",
    "caqui",
    "cará",
    "carambola",
    "caranguejo",
    "carne",
    "caruru",
    "castanha-de-caju",
    "castanha-do-brasil",
    "catalonha",
    "cebola",
    "cebolinha",
    "cenoura",
    "cereais",
    "cereal matinal",
    "cerveja",
    "chá",
    "chantilly",
    "charuto",
    "chia",
    "chicória",
    "chocolate",
    "chuchu",
    "ciriguela",
    "coca cola",
    "coco",
    "coentro",
    "corimba",
    "corimbatá",
    "corvina de água doce",
    "corvina do mar",
    "corvina grande",
    "couve",
    "couve-flor",
    "coxinha de frango",
    "creme de arroz",
    "creme de milho",
    "croquete",
    "cupuaçu",
    "curau",
    "cuscuz",
    "cuscuzarroz",
    "cuxá",
    "doce",
    "doce de leite",
    "dourada de água doce",
    "empada",
    "empada de frango",
    "ervas finas",
    "ervilha",
    "espinafre",
    "farinha",
    "fécula",
    "feijão",
    "fermento",
    "fermento em pó",
    "figo",
    "frango",
    "frango desfiado",
    "gelatina",
    "geléia",
    "gergelim",
    "goiaba",
    "granola tradicional",
    "grão de bico",
    "grão-de-bico",
    "graviola",
    "guandu",
    "hambúrguer",
    "inhame",
    "iogurte",
    "iogurte danoninho",
    "iorgute",
    "jabuticaba",
    "jaca",
    "jambo",
    "jamelão",
    "jiló",
    "jurubeba",
    "kitkat",
    "kiwi",
    "lambari",
    "laranja",
    "lasanha",
    "legumes",
    "leite",
    "leite de coco",
    "leite de soja",
    "leite de vaca",
    "leite fermentado",
    "leite ninho",
    "lentilha",
    "limão",
    "lingüiça",
    "linhaça",
    "maçã",
    "macarrão",
    "macaúba",
    "macaxeira",
    "maionese",
    "mamão",
    "mamão verde",
    "mandioca",
    "manga",
    "manjericão",
    "manjuba",
    "manteiga",
    "maracujá",
    "margarina",
    "maria mole",
    "maxi",
    "maxixe",
    "mel",
    "melancia",
    "melão",
    "merluza",
    "mexerica",
    "milho",
    "mingau tradicional",
    "morango",
    "mostarda",
    "nabo",
    "nêspera",
    "nhoque",
    "noz",
    "nutriday",
    "óleo",
    "omelete",
    "ovo",
    "paçoca",
    "paçoquita ",
    "palmito",
    "pamonha",
    "pao",
    "pão",
    "pão árabe",
    "pão integral",
    "partel",
    "pasta de amendoim",
    "pastel",
    "patinho",
    "pé-de-moleque",
    "peixe",
    "pepino",
    "pequi",
    "pêra",
    "peru",
    "pescada",
    "pescadinha",
    "pêssego",
    "pimentão",
    "pinha",
    "pinhão",
    "pintado",
    "pipoca",
    "pitanga",
    "polenta",
    "polvilho",
    "porco",
    "porquinho",
    "presunto",
    "PTS",
    "pupunha",
    "queijo",
    "quejio",
    "quiabo",
    "quibe",
    "rabanete",
    "rap10",
    "refrigerante",
    "repolho",
    "romã",
    "rúcula",
    "sal",
    "salada",
    "salmão",
    "salpicão",
    "salsa",
    "sardinha",
    "seleta de legumes",
    "serenata de amor",
    "serralha",
    "snickers",
    "soja",
    "sonho de valsa",
    "sopa de legumes",
    "sushi",
    "sustagem",
    "taioba",
    "tamarindo",
    "tangerina",
    "tapioca",
    "tofu",
    "tomate",
    "torrada",
    "toucinho",
    "tremoço",
    "tucumã",
    "tucunaré",
    "tucupi",
    "umbu",
    "uva",
    "vagem",
    "whey",
]
alimentos = ["macarrão barilla"]
alimentos = list(set(alimentos))

alimentos = [
    "chocolate sicao",
    "pao frances sem miolo",
    "requeijão light",
    "escondidinho",
    "trufa",
]


for alimento in alimentos:
    palavra_chave = alimento.replace(" ", "+")
    time.sleep(2)
    url_search = (
        "https://www.fatsecret.com.br/calorias-nutri%C3%A7%C3%A3o/search?q="
        + palavra_chave
    )
    response = requests.get(url_search)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all links
    links = soup.find_all("a")

    # Extract href attributes that start with '/calorias-nutri'
    urls = [
        link.get("href")
        for link in links
        if link.get("href") and link.get("href").startswith("/calorias-nutri")
    ]
    urls = urls[1:]
    # Print the filtered links
    print(len(urls))

    for url_item in urls:
        # time.sleep(0.05)
        try:
            # url_item=urls[4]
            url_item = "https://www.fatsecret.com.br" + url_item
            df_item = get_table(url_item)
            df_item.loc[:, "alimento"] = alimento
            urls_possiveis.append(url_item)
            df_x = pd.concat([df_x, df_item], axis=0, ignore_index=True)

        except:
            pass


df = df_x.copy()
# df_x=df.copy()


df_x.reset_index(inplace=True, drop=True)
df_x.drop(["Energia"], axis=1, inplace=True)
df_x.rename({"": "Calorias"}, axis=1, inplace=True)
df_x["Calorias"] = (
    df_x["Calorias"].str.replace(" kcal", "").str.replace(",", ".").astype(float)
)


for col in df_x.columns:
    if df_x[col].dtype == "object" and not (
        col in ["identificador", "Nome", "Marca", "alimento"]
    ):
        df_x[col] = (
            df_x[col]
            .str.replace("g", "")
            .str.replace(",", ".")
            .astype("float", errors="ignore")
        )

df_x.drop_duplicates(subset="identificador", inplace=True)


# def normalize_row(row):
#     for col in df_x.columns:
#         if not(col in ['identificador', 'Nome', 'Quantidade', 'Marca','alimento']):
#             if row['Quantidade'] > 3:
#                 row[col] = 100 * row[col] / row['Quantidade']
#             elif row['Quantidade'] < 3:
#                 row[col] = row[col] / row['Quantidade']
#     return row

# # Apply the function to each row
# df_x = df_x.apply(normalize_row, axis=1)

# df_x['Quantidade']=np.where(df_x['Quantidade']>3,100,1)
df_x[["identificador", "Nome", "Marca"]] = df_x[
    ["identificador", "Nome", "Marca"]
].apply(lambda x: x.str.strip())


desired_order = [
    "identificador",
    "Nome",
    "alimento",
    "Quantidade",
    "Marca",
    "Calorias",
    "Carboidratos",
    "Açúcar",
    "Proteínas",
    "Gorduras",
    "Gordura Saturada",
    "Gordura Trans",
    "Gordura Monoinsaturada",
    "Gordura Poliinsaturada",
]


# Reindex the DataFrame to match the desired order
df_x = df_x.reindex(columns=desired_order)

df_x.to_excel("export.xlsx")
