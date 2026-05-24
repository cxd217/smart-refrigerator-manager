"""
Small optional tests for Smart Refrigerator Manager.

Run with:
python test_smart_refrigerator_manager.py
"""

import os
import tempfile
import builtins
from datetime import date

from smart_refrigerator_manager import (
    FOOD_TYPES,
    add_or_update_shelf_life_rule,
    apply_custom_shelf_life,
    calculate_expiry,
    calculate_expiry_from_production,
    choose_custom_expiry_date,
    choose_food_type,
    delete_shelf_life_rule,
    get_expiry_reminder_groups,
    get_shelf_life_source,
    load_inventory,
    load_custom_shelf_life,
    reset_shelf_life_guide,
    save_inventory,
    sort_items_by_expiry,
)


def test_expiry_calculation():
    assert str(calculate_expiry(date(2026, 5, 1), "pork", "fridge")) == "2026-05-04"
    assert str(calculate_expiry(date(2026, 5, 1), "pork", "freezer")) == "2026-07-30"
    assert str(calculate_expiry_from_production(date(2026, 5, 1), 30)) == "2026-05-31"


def test_sorting():
    items = [
        {
            "id": 1,
            "name": "Milk",
            "food_type": "milk",
            "location": "fridge",
            "quantity": "1 bottle",
            "added_date": "2026-05-01",
            "expiry_date": "2026-05-08",
        },
        {
            "id": 2,
            "name": "Chicken",
            "food_type": "chicken",
            "location": "fridge",
            "quantity": "300g",
            "added_date": "2026-05-01",
            "expiry_date": "2026-05-03",
        },
    ]
    sorted_items = sort_items_by_expiry(items)
    assert sorted_items[0]["name"] == "Chicken"
    assert sorted_items[1]["name"] == "Milk"


def test_same_food_type_can_have_multiple_records():
    items = [
        {
            "id": 1,
            "name": "Pork mince",
            "food_type": "pork",
            "location": "fridge",
            "quantity": "500g",
            "added_date": "2026-05-01",
            "expiry_date": "2026-05-04",
        },
        {
            "id": 2,
            "name": "Pork ribs",
            "food_type": "pork",
            "location": "freezer",
            "quantity": "1kg",
            "added_date": "2026-05-02",
            "expiry_date": "2026-07-31",
        },
    ]

    assert len(items) == 2
    assert items[0]["food_type"] == items[1]["food_type"]
    assert items[0]["id"] != items[1]["id"]
    assert items[0]["expiry_date"] != items[1]["expiry_date"]


def run_with_inputs(function, inputs):
    original_input = builtins.input
    answers = iter(inputs)
    builtins.input = lambda prompt="": next(answers)

    try:
        return function()
    finally:
        builtins.input = original_input


def test_choose_food_type_from_numbered_list():
    pork_number = str(FOOD_TYPES.index("pork") + 1)
    selected_food_type = run_with_inputs(choose_food_type, [pork_number])

    assert selected_food_type == "pork"


def test_choose_custom_food_type():
    selected_food_type = run_with_inputs(choose_food_type, ["c", "kimchi"])

    assert selected_food_type == "kimchi"


def test_choose_custom_expiry_date_directly():
    expiry_date = run_with_inputs(choose_custom_expiry_date, ["1", "2026-06-15"])

    assert str(expiry_date) == "2026-06-15"


def test_choose_custom_expiry_date_by_calculation():
    expiry_date = run_with_inputs(
        choose_custom_expiry_date,
        ["2", "2026-05-01", "45"],
    )

    assert str(expiry_date) == "2026-06-15"


def test_past_custom_expiry_date_can_be_confirmed():
    expiry_date = run_with_inputs(
        choose_custom_expiry_date,
        ["1", "2000-01-01", "y"],
    )

    assert str(expiry_date) == "2000-01-01"


def test_past_custom_expiry_date_can_be_reentered():
    expiry_date = run_with_inputs(
        choose_custom_expiry_date,
        ["1", "2000-01-01", "n", "1", "2026-06-15"],
    )

    assert str(expiry_date) == "2026-06-15"


def test_custom_shelf_life_guide_round_trip():
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    temp_path = temp_file.name
    temp_file.close()

    try:
        add_or_update_shelf_life_rule("kimchi", 30, 90, temp_path)
        custom_rules = load_custom_shelf_life(temp_path)
        apply_custom_shelf_life(custom_rules)

        assert custom_rules["kimchi"]["fridge"] == 30
        assert custom_rules["kimchi"]["freezer"] == 90
        assert str(calculate_expiry(date(2026, 5, 1), "kimchi", "fridge")) == "2026-05-31"
    finally:
        os.remove(temp_path)
        reset_shelf_life_guide()


def test_built_in_shelf_life_can_be_adjusted():
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    temp_path = temp_file.name
    temp_file.close()

    try:
        add_or_update_shelf_life_rule("pork", 2, 60, temp_path)
        custom_rules = load_custom_shelf_life(temp_path)
        apply_custom_shelf_life(custom_rules)

        assert custom_rules["pork"]["fridge"] == 2
        assert custom_rules["pork"]["freezer"] == 60
        assert get_shelf_life_source("pork") == "adjusted"
        assert str(calculate_expiry(date(2026, 5, 1), "pork", "fridge")) == "2026-05-03"
    finally:
        os.remove(temp_path)
        reset_shelf_life_guide()


def test_custom_shelf_life_can_be_deleted():
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    temp_path = temp_file.name
    temp_file.close()

    try:
        add_or_update_shelf_life_rule("kimchi", 30, 90, temp_path)
        delete_shelf_life_rule("kimchi", temp_path)
        custom_rules = load_custom_shelf_life(temp_path)

        assert "kimchi" not in custom_rules
    finally:
        os.remove(temp_path)
        reset_shelf_life_guide()


def test_adjusted_built_in_shelf_life_can_be_reset():
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    temp_path = temp_file.name
    temp_file.close()

    try:
        add_or_update_shelf_life_rule("pork", 2, 60, temp_path)
        delete_shelf_life_rule("pork", temp_path)
        custom_rules = load_custom_shelf_life(temp_path)

        assert "pork" not in custom_rules
        assert get_shelf_life_source("pork") == "default"
        assert str(calculate_expiry(date(2026, 5, 1), "pork", "fridge")) == "2026-05-04"
    finally:
        os.remove(temp_path)
        reset_shelf_life_guide()


def test_expiry_reminder_groups():
    items = [
        {
            "id": 1,
            "name": "Old milk",
            "food_type": "milk",
            "location": "fridge",
            "quantity": "1 bottle",
            "added_date": "2026-05-15",
            "expiry_date": "2026-05-23",
        },
        {
            "id": 2,
            "name": "Today tofu",
            "food_type": "tofu",
            "location": "fridge",
            "quantity": "1 box",
            "added_date": "2026-05-21",
            "expiry_date": "2026-05-24",
        },
        {
            "id": 3,
            "name": "Tomorrow pork",
            "food_type": "pork",
            "location": "fridge",
            "quantity": "500g",
            "added_date": "2026-05-22",
            "expiry_date": "2026-05-25",
        },
        {
            "id": 4,
            "name": "Safe salmon",
            "food_type": "fish",
            "location": "freezer",
            "quantity": "2 pieces",
            "added_date": "2026-05-24",
            "expiry_date": "2026-08-22",
        },
    ]

    reminders = get_expiry_reminder_groups(items, date(2026, 5, 24))

    assert len(reminders["expired"]) == 1
    assert len(reminders["today"]) == 1
    assert len(reminders["tomorrow"]) == 1
    assert reminders["expired"][0]["name"] == "Old milk"
    assert reminders["today"][0]["name"] == "Today tofu"
    assert reminders["tomorrow"][0]["name"] == "Tomorrow pork"


def test_file_io_round_trip():
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
    temp_path = temp_file.name
    temp_file.close()

    try:
        items = [
            {
                "id": 1,
                "name": "Tofu",
                "food_type": "tofu",
                "location": "fridge",
                "quantity": "1 box",
                "added_date": "2026-05-01",
                "expiry_date": "2026-05-04",
            }
        ]
        save_inventory(items, temp_path)
        loaded_items = load_inventory(temp_path)

        assert len(loaded_items) == 1
        assert loaded_items[0]["id"] == 1
        assert loaded_items[0]["name"] == "Tofu"
    finally:
        os.remove(temp_path)


def run_tests():
    test_expiry_calculation()
    test_sorting()
    test_same_food_type_can_have_multiple_records()
    test_choose_food_type_from_numbered_list()
    test_choose_custom_food_type()
    test_choose_custom_expiry_date_directly()
    test_choose_custom_expiry_date_by_calculation()
    test_past_custom_expiry_date_can_be_confirmed()
    test_past_custom_expiry_date_can_be_reentered()
    test_custom_shelf_life_guide_round_trip()
    test_built_in_shelf_life_can_be_adjusted()
    test_custom_shelf_life_can_be_deleted()
    test_adjusted_built_in_shelf_life_can_be_reset()
    test_expiry_reminder_groups()
    test_file_io_round_trip()
    print("All tests passed.")


if __name__ == "__main__":
    run_tests()
