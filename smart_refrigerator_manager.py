"""
Smart Refrigerator Manager

A simple command-line program for tracking refrigerator/freezer inventory.
It stores data in a CSV file, estimates expiry dates, and warns the user
about food that should be used soon.
"""

import csv
import os
from datetime import date, datetime, timedelta


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "inventory.csv")
CUSTOM_GUIDE_FILE = os.path.join(BASE_DIR, "shelf_life_guide.csv")
DATE_FORMAT = "%Y-%m-%d"

CSV_FIELDS = [
    "id",
    "name",
    "food_type",
    "location",
    "quantity",
    "added_date",
    "expiry_date",
]

GUIDE_FIELDS = [
    "food_type",
    "fridge_days",
    "freezer_days",
]

LOCATIONS = {
    "1": "fridge",
    "2": "freezer",
}

LOCATION_NAMES = {
    "fridge": "Fresh layer",
    "freezer": "Freezer layer",
}

# Rough default shelf life values, measured in days.
# These can be adjusted from the program if the user's fridge works differently.
DEFAULT_SHELF_LIFE = {
    "pork": {"fridge": 3, "freezer": 90},
    "beef": {"fridge": 4, "freezer": 120},
    "chicken": {"fridge": 2, "freezer": 90},
    "fish": {"fridge": 2, "freezer": 90},
    "shrimp": {"fridge": 2, "freezer": 90},
    "milk": {"fridge": 7, "freezer": 30},
    "yoghurt": {"fridge": 10, "freezer": 30},
    "egg": {"fridge": 21, "freezer": 0},
    "vegetable": {"fridge": 5, "freezer": 30},
    "fruit": {"fridge": 7, "freezer": 30},
    "tofu": {"fridge": 3, "freezer": 30},
    "leftover": {"fridge": 3, "freezer": 30},
    "rice": {"fridge": 3, "freezer": 30},
    "bread": {"fridge": 7, "freezer": 90},
}

SHELF_LIFE = {}
FOOD_TYPES = []


def reset_shelf_life_guide():
    """Reset the in-memory guide to the default shelf-life rules."""
    SHELF_LIFE.clear()
    for food_type, shelf_life in DEFAULT_SHELF_LIFE.items():
        SHELF_LIFE[food_type] = shelf_life.copy()
    refresh_food_types()


def refresh_food_types():
    """Refresh the food type list after guide changes."""
    FOOD_TYPES.clear()
    FOOD_TYPES.extend(sorted(SHELF_LIFE.keys()))


reset_shelf_life_guide()


def ensure_data_file(file_path=DATA_FILE):
    """Create the CSV file with a header if it does not exist yet."""
    if os.path.exists(file_path):
        return

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()


def ensure_custom_guide_file(file_path=CUSTOM_GUIDE_FILE):
    """Create the custom shelf-life CSV file if it does not exist yet."""
    if os.path.exists(file_path):
        return

    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=GUIDE_FIELDS)
        writer.writeheader()


def load_custom_shelf_life(file_path=CUSTOM_GUIDE_FILE):
    """Read custom shelf-life rules from the CSV file."""
    ensure_custom_guide_file(file_path)
    custom_rules = {}

    with open(file_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                food_type = row["food_type"].strip().lower()
                fridge_days = int(row["fridge_days"])
                freezer_days = int(row["freezer_days"])

                if food_type == "":
                    raise ValueError("Food type cannot be empty.")
                if fridge_days < 0 or freezer_days < 0:
                    raise ValueError("Shelf life cannot be negative.")
                if fridge_days == 0 and freezer_days == 0:
                    raise ValueError("At least one storage location must be suitable.")

                custom_rules[food_type] = {
                    "fridge": fridge_days,
                    "freezer": freezer_days,
                }
            except (KeyError, ValueError):
                print("Warning: one damaged shelf-life guide row was skipped.")
                continue

    return custom_rules


def save_custom_shelf_life(custom_rules, file_path=CUSTOM_GUIDE_FILE):
    """Write custom shelf-life rules to the CSV file."""
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=GUIDE_FIELDS)
        writer.writeheader()
        for food_type in sorted(custom_rules.keys()):
            writer.writerow(
                {
                    "food_type": food_type,
                    "fridge_days": custom_rules[food_type]["fridge"],
                    "freezer_days": custom_rules[food_type]["freezer"],
                }
            )


def apply_custom_shelf_life(custom_rules):
    """Merge custom rules into the active shelf-life guide."""
    reset_shelf_life_guide()
    for food_type, shelf_life in custom_rules.items():
        SHELF_LIFE[food_type] = shelf_life.copy()
    refresh_food_types()


def add_or_update_shelf_life_rule(
    food_type,
    fridge_days,
    freezer_days,
    file_path=CUSTOM_GUIDE_FILE,
):
    """Save one custom or adjusted shelf-life rule and update the guide."""
    if food_type.strip() == "":
        raise ValueError("Food type cannot be empty.")
    if fridge_days < 0 or freezer_days < 0:
        raise ValueError("Shelf life cannot be negative.")
    if fridge_days == 0 and freezer_days == 0:
        raise ValueError("At least one storage location must be suitable.")

    food_type = food_type.strip().lower()
    custom_rules = load_custom_shelf_life(file_path)
    custom_rules[food_type] = {
        "fridge": fridge_days,
        "freezer": freezer_days,
    }
    save_custom_shelf_life(custom_rules, file_path)
    SHELF_LIFE[food_type] = custom_rules[food_type].copy()
    refresh_food_types()


def delete_shelf_life_rule(food_type, file_path=CUSTOM_GUIDE_FILE):
    """Delete a custom rule or remove an adjusted override."""
    food_type = food_type.strip().lower()
    if food_type == "":
        raise ValueError("Food type cannot be empty.")

    custom_rules = load_custom_shelf_life(file_path)
    if food_type not in custom_rules:
        raise ValueError("Only custom or adjusted rules can be deleted.")

    del custom_rules[food_type]
    save_custom_shelf_life(custom_rules, file_path)
    apply_custom_shelf_life(custom_rules)


def get_shelf_life_source(food_type):
    """Return whether a shelf-life rule is default, adjusted, or custom."""
    if food_type not in DEFAULT_SHELF_LIFE:
        return "custom"
    if SHELF_LIFE[food_type] == DEFAULT_SHELF_LIFE[food_type]:
        return "default"
    return "adjusted"


def parse_date(date_text):
    """Convert a YYYY-MM-DD string into a date object."""
    return datetime.strptime(date_text, DATE_FORMAT).date()


def load_inventory(file_path=DATA_FILE):
    """Read inventory data from the CSV file."""
    ensure_data_file(file_path)
    inventory = []

    with open(file_path, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                row["id"] = int(row["id"])
                parse_date(row["added_date"])
                parse_date(row["expiry_date"])
                inventory.append(row)
            except (KeyError, ValueError):
                print("Warning: one damaged inventory row was skipped.")
                continue

    return inventory


def save_inventory(inventory, file_path=DATA_FILE):
    """Write the current inventory list into the CSV file."""
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for item in inventory:
            writer.writerow(item)


def calculate_expiry(added_date, food_type, location):
    """Calculate the expiry date from food type and storage location."""
    if food_type not in SHELF_LIFE:
        raise ValueError("This food type is not in the built-in shelf-life table.")

    if location not in SHELF_LIFE[food_type]:
        raise ValueError("This storage location is not supported.")

    shelf_days = SHELF_LIFE[food_type][location]
    if shelf_days <= 0:
        raise ValueError("This food is not suitable for the selected storage location.")

    return added_date + timedelta(days=shelf_days)


def calculate_expiry_from_production(production_date, shelf_life_days):
    """Calculate expiry date from production date and shelf life."""
    if shelf_life_days <= 0:
        raise ValueError("Shelf life must be greater than 0.")
    return production_date + timedelta(days=shelf_life_days)


def sort_items_by_expiry(items):
    """Return items sorted by expiry date, then by name."""
    return sorted(
        items,
        key=lambda item: (parse_date(item["expiry_date"]), item["name"].lower()),
    )


def get_next_id(inventory):
    """Find the next available item ID."""
    if len(inventory) == 0:
        return 1
    return max(item["id"] for item in inventory) + 1


def input_non_empty(prompt):
    """Keep asking until the user enters a non-empty value."""
    while True:
        text = input(prompt).strip()
        try:
            if text == "":
                raise ValueError("This field cannot be empty.")
            return text
        except ValueError as error:
            print(f"Input error: {error}")
            continue


def input_positive_int(prompt):
    """Keep asking until the user enters a positive integer."""
    while True:
        text = input(prompt).strip()
        try:
            number = int(text)
            if number <= 0:
                raise ValueError("Please enter a number greater than 0.")
            return number
        except ValueError as error:
            print(f"Input error: {error}")
            continue


def input_non_negative_int(prompt):
    """Keep asking until the user enters zero or a positive integer."""
    while True:
        text = input(prompt).strip()
        try:
            number = int(text)
            if number < 0:
                raise ValueError("Please enter 0 or a positive number.")
            return number
        except ValueError as error:
            print(f"Input error: {error}")
            continue


def input_date_or_today(prompt):
    """Read a date from the user, or use today's date when input is blank."""
    while True:
        text = input(prompt).strip()
        try:
            if text == "":
                return date.today()
            return parse_date(text)
        except ValueError:
            print(f"Input error: please use the format {DATE_FORMAT}, for example 2026-05-24.")
            continue


def input_date(prompt):
    """Keep asking until the user enters a valid date."""
    while True:
        text = input(prompt).strip()
        try:
            if text == "":
                raise ValueError("Date cannot be empty.")
            return parse_date(text)
        except ValueError as error:
            if str(error) == "Date cannot be empty.":
                print(f"Input error: {error}")
            else:
                print(f"Input error: please use the format {DATE_FORMAT}, for example 2026-05-24.")
            continue


def choose_location():
    """Ask the user to choose fresh layer or freezer layer."""
    while True:
        print("1. Fresh layer")
        print("2. Freezer layer")
        choice = input("Choose storage location (1-2): ").strip()
        try:
            if choice not in LOCATIONS:
                raise ValueError("Please choose 1 or 2.")
            return LOCATIONS[choice]
        except ValueError as error:
            print(f"Input error: {error}")
            continue


def print_food_types():
    """Display supported food types."""
    print("\nFood types in shelf-life guide:")
    for index, food_type in enumerate(FOOD_TYPES, start=1):
        print(f"{index:>2}. {food_type}")
    print(" C. Custom food type")


def choose_food_type():
    """Ask the user to choose a food type from the list or enter a custom one."""
    while True:
        print_food_types()
        choice = input("Choose food type number, or C for custom: ").strip().lower()

        try:
            if choice in ["c", "custom"]:
                return input_non_empty("Custom food type: ").lower()

            food_index = int(choice)
            if food_index < 1 or food_index > len(FOOD_TYPES):
                raise ValueError("Please choose a number from the food list.")
            return FOOD_TYPES[food_index - 1]
        except ValueError as error:
            print(f"Input error: {error}")
            continue


def choose_custom_expiry_date():
    """Let the user enter a custom expiry date directly or calculate one."""
    while True:
        print("1. Enter expiry date directly")
        print("2. Calculate from production date and shelf life")
        choice = input("Choose custom expiry method (1-2): ").strip()

        try:
            if choice == "1":
                expiry_date = input_date("Expiry date (YYYY-MM-DD): ")
                if confirm_expiry_date(expiry_date):
                    return expiry_date
                continue
            if choice == "2":
                production_date = input_date("Production date (YYYY-MM-DD): ")
                shelf_life_days = input_positive_int("Shelf life in days: ")
                expiry_date = calculate_expiry_from_production(
                    production_date,
                    shelf_life_days,
                )
                print(f"Calculated expiry date: {expiry_date.strftime(DATE_FORMAT)}")
                if confirm_expiry_date(expiry_date):
                    return expiry_date
                continue
            raise ValueError("Please choose 1 or 2.")
        except ValueError as error:
            print(f"Input error: {error}")
            continue


def input_yes_or_no(prompt):
    """Read a yes/no answer from the user."""
    while True:
        choice = input(prompt).strip().lower()
        try:
            if choice in ["y", "yes"]:
                return True
            if choice in ["n", "no"]:
                return False
            raise ValueError("Please enter Y or N.")
        except ValueError as error:
            print(f"Input error: {error}")
            continue


def confirm_expiry_date(expiry_date):
    """Confirm with the user if the expiry date is already in the past."""
    if expiry_date >= date.today():
        return True

    print(f"Warning: {expiry_date.strftime(DATE_FORMAT)} is already in the past.")
    return input_yes_or_no("Save this item as already expired? (Y/N): ")


def add_custom_shelf_life_rule(food_type=None):
    """Let the user add or update a shelf-life guide rule."""
    print("\nAdd or update shelf-life rule")
    if food_type is None:
        food_type = input_non_empty("Food type: ").lower()
    else:
        print(f"Food type: {food_type}")

    if food_type in SHELF_LIFE:
        current_rule = SHELF_LIFE[food_type]
        print(
            f"Current rule: fresh layer {current_rule['fridge']} day(s), "
            f"freezer layer {current_rule['freezer']} day(s)."
        )
        if food_type in DEFAULT_SHELF_LIFE:
            default_rule = DEFAULT_SHELF_LIFE[food_type]
            print(
                f"Built-in default: fresh layer {default_rule['fridge']} day(s), "
                f"freezer layer {default_rule['freezer']} day(s)."
            )
            print("You can enter shorter values for an older refrigerator.")

    print("Enter 0 if a food is not suitable for that storage location.")
    fridge_days = input_non_negative_int("Fresh layer shelf life in days: ")
    freezer_days = input_non_negative_int("Freezer layer shelf life in days: ")

    try:
        add_or_update_shelf_life_rule(food_type, fridge_days, freezer_days)
        print(f"Saved shelf-life rule for {food_type}.")
    except ValueError as error:
        print(f"Input error: {error}")


def delete_shelf_life_rule_prompt():
    """Let the user delete a custom rule or reset an adjusted rule."""
    print("\nDelete shelf-life rule")
    food_type = input_non_empty("Food type to delete or reset: ").lower()

    try:
        delete_shelf_life_rule(food_type)
        if food_type in DEFAULT_SHELF_LIFE:
            print(f"Removed adjusted rule for {food_type}. It now uses the built-in default.")
        else:
            print(f"Deleted custom shelf-life rule for {food_type}.")
    except ValueError as error:
        print(f"Input error: {error}")


def offer_to_save_custom_rule(food_type):
    """Ask whether a custom item should be saved into the shelf-life guide."""
    should_save = input_yes_or_no(
        f"Save or update {food_type} in the shelf-life guide for next time? (Y/N): "
    )
    if should_save:
        add_custom_shelf_life_rule(food_type)


def add_item(inventory):
    """Add a new food item to the inventory."""
    print("\nAdd food")

    name = input_non_empty("Food name: ")
    food_type = choose_food_type()
    location = choose_location()
    quantity = input_non_empty("Quantity or note (for example '500g' or '2 boxes'): ")
    added_date = input_date_or_today("Added date (YYYY-MM-DD, blank for today): ")

    try:
        expiry_date = calculate_expiry(added_date, food_type, location)
    except ValueError as error:
        print(f"Notice: {error}")
        expiry_date = choose_custom_expiry_date()
        offer_to_save_custom_rule(food_type)

    item = {
        "id": get_next_id(inventory),
        "name": name,
        "food_type": food_type,
        "location": location,
        "quantity": quantity,
        "added_date": added_date.strftime(DATE_FORMAT),
        "expiry_date": expiry_date.strftime(DATE_FORMAT),
    }

    inventory.append(item)
    save_inventory(inventory)
    print(f"Added {name}. Estimated expiry date: {item['expiry_date']}")


def get_expiry_status(expiry_date_text):
    """Return a short warning message for an expiry date."""
    days_left = (parse_date(expiry_date_text) - date.today()).days

    if days_left < 0:
        return f"EXPIRED {-days_left} day(s) ago"
    if days_left == 0:
        return "EXPIRES TODAY"
    if days_left <= 2:
        return f"USE SOON: {days_left} day(s) left"
    return f"OK: {days_left} day(s) left"


def get_expiry_reminder_groups(inventory, today=None):
    """Group food that is expired, expires today, or expires tomorrow."""
    if today is None:
        today = date.today()

    reminders = {
        "expired": [],
        "today": [],
        "tomorrow": [],
    }

    for item in sort_items_by_expiry(inventory):
        days_left = (parse_date(item["expiry_date"]) - today).days
        if days_left < 0:
            reminders["expired"].append(item)
        elif days_left == 0:
            reminders["today"].append(item)
        elif days_left == 1:
            reminders["tomorrow"].append(item)

    return reminders


def print_reminder_group(title, items):
    """Print one reminder group."""
    if len(items) == 0:
        return

    print(title)
    for item in items:
        print(
            f"  ID {item['id']}: {item['name']} ({item['quantity']}), "
            f"expiry {item['expiry_date']}"
        )


def print_expiry_reminders(inventory):
    """Warn the user about urgent expiry items."""
    reminders = get_expiry_reminder_groups(inventory)
    total_reminders = (
        len(reminders["expired"])
        + len(reminders["today"])
        + len(reminders["tomorrow"])
    )

    print("\nExpiry reminder")
    if total_reminders == 0:
        print("No expired food, and nothing expires today or tomorrow.")
        return

    print_reminder_group("Expired food:", reminders["expired"])
    print_reminder_group("Expires today:", reminders["today"])
    print_reminder_group("Expires tomorrow:", reminders["tomorrow"])


def print_item_table(items):
    """Print items in a compact table."""
    if len(items) == 0:
        print("No food stored here.")
        return

    print("-" * 95)
    print(
        f"{'ID':<4} {'Name':<18} {'Type':<12} {'Quantity':<16} "
        f"{'Added':<12} {'Expiry':<12} Status"
    )
    print("-" * 95)
    for item in sort_items_by_expiry(items):
        status = get_expiry_status(item["expiry_date"])
        print(
            f"{item['id']:<4} {item['name']:<18} {item['food_type']:<12} "
            f"{item['quantity']:<16} {item['added_date']:<12} "
            f"{item['expiry_date']:<12} {status}"
        )
    print("-" * 95)


def view_inventory(inventory):
    """Show the current inventory by storage location."""
    print("\nCurrent inventory")
    if len(inventory) == 0:
        print("Your refrigerator is empty.")
        return

    for location in ["fridge", "freezer"]:
        print(f"\n{LOCATION_NAMES[location]}")
        location_items = []
        for item in inventory:
            if item["location"] == location:
                location_items.append(item)
        print_item_table(location_items)


def choose_removal_reason():
    """Ask whether the user ate or discarded the selected food."""
    while True:
        print("1. Eaten")
        print("2. Discarded")
        choice = input("Removal reason (1-2): ").strip()
        try:
            if choice == "1":
                return "eaten"
            if choice == "2":
                return "discarded"
            raise ValueError("Please choose 1 or 2.")
        except ValueError as error:
            print(f"Input error: {error}")
            continue


def remove_item(inventory):
    """Remove an eaten or discarded item from the inventory."""
    print("\nConsume or discard food")
    if len(inventory) == 0:
        raise ValueError("The refrigerator is empty, so there is nothing to remove.")

    view_inventory(inventory)
    target_id = input_positive_int("Enter the ID of the food to remove: ")

    for index, item in enumerate(inventory):
        if item["id"] == target_id:
            reason = choose_removal_reason()
            removed_item = inventory.pop(index)
            save_inventory(inventory)
            print(f"Removed {removed_item['name']} as {reason}.")
            break
    else:
        raise ValueError("No food item has that ID.")


def show_shelf_life_guide():
    """Print the active shelf-life rules."""
    print("\nShelf-life guide")
    print("-" * 66)
    print(f"{'Food type':<14} {'Fresh layer':<16} {'Freezer layer':<16} Source")
    print("-" * 66)
    for food_type in sorted(SHELF_LIFE.keys()):
        fridge_days = SHELF_LIFE[food_type]["fridge"]
        freezer_days = SHELF_LIFE[food_type]["freezer"]
        fridge_text = f"{fridge_days} days" if fridge_days > 0 else "not suitable"
        freezer_text = f"{freezer_days} days" if freezer_days > 0 else "not suitable"
        source = get_shelf_life_source(food_type)
        print(f"{food_type:<14} {fridge_text:<16} {freezer_text:<16} {source}")
    print("-" * 66)


def manage_shelf_life_guide():
    """Show or edit the shelf-life guide."""
    while True:
        print("\nShelf-life guide menu")
        print("1. View shelf-life guide")
        print("2. Add or update any shelf-life rule")
        print("3. Delete custom rule or reset adjusted rule")
        print("4. Return to main menu")
        choice = input("Choose an option (1-4): ").strip()

        try:
            if choice == "1":
                show_shelf_life_guide()
            elif choice == "2":
                add_custom_shelf_life_rule()
            elif choice == "3":
                delete_shelf_life_rule_prompt()
            elif choice == "4":
                break
            else:
                raise ValueError("Please choose a number from 1 to 4.")
        except ValueError as error:
            print(f"Input error: {error}")
            continue


def show_menu():
    """Display the main menu."""
    print("\nSmart Refrigerator Manager")
    print("1. Add food")
    print("2. View inventory")
    print("3. Consume or discard food")
    print("4. Manage shelf-life guide")
    print("5. Save and exit")


def main():
    """Run the main menu loop."""
    apply_custom_shelf_life(load_custom_shelf_life())
    inventory = load_inventory()
    print("Welcome! Your inventory file is ready.")

    while True:
        print_expiry_reminders(inventory)
        show_menu()
        choice = input("Choose an option (1-5): ").strip()

        try:
            if choice == "1":
                add_item(inventory)
            elif choice == "2":
                view_inventory(inventory)
            elif choice == "3":
                remove_item(inventory)
            elif choice == "4":
                manage_shelf_life_guide()
            elif choice == "5":
                save_inventory(inventory)
                print("Inventory saved. Goodbye!")
                break
            else:
                raise ValueError("Please choose a number from 1 to 5.")
        except ValueError as error:
            print(f"Input error: {error}")
            continue
        except KeyboardInterrupt:
            save_inventory(inventory)
            print("\nInventory saved before exit. Goodbye!")
            break


if __name__ == "__main__":
    main()
