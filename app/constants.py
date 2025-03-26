"""
Constants used throughout the application
"""

MEAL_TYPES = {
    "cafe_da_manha": "Café da Manhã",
    "lanche_manha": "Lanche da Manhã",
    "almoco": "Almoço",
    "lanche_tarde": "Lanche da Tarde",
    "janta": "Jantar",
    "ceia": "Ceia",
}

ACTIVITY_FACTORS = {
    "sedentario": 1.2,
    "leve": 1.375,
    "moderado": 1.55,
    "muito_ativo": 1.725,
    "extremamente_ativo": 1.9,
}

OBJECTIVES = {
    "perder_peso": 0.85,  # 15% deficit
    "manter_peso": 1.0,  # no change
    "ganhar_peso": 1.15,  # 15% surplus
    "ganhar_massa": 1.15,  # 15% surplus
}

GENDER_CHOICES = {"M": "Masculino", "F": "Feminino"}

# Nutritional Constants
CALORIES_PER_PROTEIN = 4
CALORIES_PER_CARB = 4
CALORIES_PER_FAT = 9

# Default values
DEFAULT_PORTION_SIZE = 100  # in grams
