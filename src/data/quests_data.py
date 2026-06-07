QUESTS = {
    "first_shelter": {
        "title": "Primeiro Abrigo",
        "description": "Junte recursos e construa uma fogueira para sobreviver a primeira noite.",
        "objectives": [
            {"type": "collect", "item": "wood", "amount": 10, "label": "Coletar 10 madeiras"},
            {"type": "collect", "item": "stone", "amount": 5, "label": "Coletar 5 pedras"},
            {"type": "build", "building": "campfire", "amount": 1, "label": "Construir uma fogueira"},
        ],
        "rewards": {
            "xp": 50,
            "coins": 100,
            "items": {"small_chest": 1},
            "unlock_recipe": "small_chest",
        },
    }
}
