ANIMAL_TYPES = {
    "pig": {
        "name": "Porco",
        "hp": 30,
        "speed": 44,
        "color": (203, 129, 139),
        "drops": {
            "raw_pork": (1.0, 1, 2),
            "hide": (0.25, 1, 1),
        },
    },
    "cow": {
        "name": "Vaca",
        "hp": 46,
        "speed": 34,
        "color": (221, 214, 196),
        "drops": {
            "raw_beef": (1.0, 1, 2),
            "leather": (0.50, 1, 1),
        },
    },
    "chicken": {
        "name": "Galinha",
        "hp": 18,
        "speed": 58,
        "color": (238, 232, 205),
        "drops": {
            "raw_chicken": (1.0, 1, 1),
            "feather": (0.75, 1, 3),
            "egg": (0.35, 1, 1),
        },
    },
}


ANIMAL_ORDER = ["pig", "cow", "chicken"]
