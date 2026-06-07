from src.data.food_data import food_shop_stock


SHOP_STOCK = [
    {
        "id": "stone_hoe",
        "price": 120,
        "required_level": 1,
        "stock": 4,
    },
    {
        "id": "stone_axe",
        "price": 150,
        "required_level": 1,
        "stock": 4,
    },
    {
        "id": "stone_pickaxe",
        "price": 160,
        "required_level": 1,
        "stock": 4,
    },
    {
        "id": "stone_shovel",
        "price": 100,
        "required_level": 1,
        "stock": 4,
    },
    {
        "id": "apple",
        "price": 15,
        "required_level": 1,
        "stock": 25,
    },
    {
        "id": "water_cup",
        "price": 4,
        "required_level": 1,
        "stock": 30,
    },
    {
        "id": "empty_cup",
        "price": 2,
        "required_level": 1,
        "stock": 30,
    },
    {
        "id": "basic_seed",
        "price": 25,
        "required_level": 1,
        "stock": 20,
    },
    {
        "id": "torch",
        "price": 35,
        "required_level": 1,
        "stock": 15,
    },
    {
        "id": "small_health_potion",
        "price": 75,
        "required_level": 1,
        "stock": 8,
    },
    {
        "id": "stone_sword",
        "price": 190,
        "required_level": 2,
        "stock": 2,
    },
    {
        "id": "simple_fishing_rod",
        "price": 140,
        "required_level": 2,
        "stock": 3,
    },
    {
        "id": "workbench",
        "price": 140,
        "required_level": 2,
        "stock": 3,
    },
    {
        "id": "small_chest",
        "price": 110,
        "required_level": 2,
        "stock": 4,
    },
    {
        "id": "small_energy_potion",
        "price": 95,
        "required_level": 2,
        "stock": 8,
    },
    {
        "id": "simple_bow",
        "price": 240,
        "required_level": 3,
        "stock": 2,
    },
    {
        "id": "fence",
        "price": 18,
        "required_level": 4,
        "stock": 30,
    },
    {
        "id": "small_shelter",
        "price": 260,
        "required_level": 5,
        "stock": 2,
    },
]


_existing_stock = {entry["id"] for entry in SHOP_STOCK}
SHOP_STOCK.extend(entry for entry in food_shop_stock() if entry["id"] not in _existing_stock)
