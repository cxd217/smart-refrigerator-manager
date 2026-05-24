Smart Refrigerator Manager
==========================

Project goal
------------
I made this program because I often forget what is already in the fridge,
especially when the same food is bought more than once. The program keeps a
small inventory for the fresh layer and freezer layer, estimates expiry dates,
and reminds the user when something has expired or is close to expiring.

How to run
----------
1. Put all files in the same folder.
2. Open a terminal in this folder.
3. Run:

   python smart_refrigerator_manager.py

Main functions
--------------
1. Add food with name, food type, storage location, quantity, and added date.
2. Choose the food type from a numbered list, or enter a custom food type.
3. View current inventory by storage location, sorted by expiry date.
4. Automatically show reminders for expired food, food expiring today, and food
   expiring tomorrow before the main menu appears.
5. Remove food when it has been eaten or discarded.
6. View, update, and delete shelf-life guide rules, including adjusted built-in
   food types.
7. Save all inventory records in inventory.csv.

The default shelf-life guide is built into the Python file, but I did not want
the numbers to be completely fixed. Different fridges can behave differently,
so the user can adjust an existing rule. For example, if an older fridge is not
very cold, "pork" can be changed from 3 days to 2 days in the fresh layer.

New food types can also be saved in shelf_life_guide.csv. For example, the
user can add "kimchi" with 30 days in the fresh layer and 90 days in the
freezer layer. Deleting a custom rule removes that food type from the guide.
Deleting an adjusted built-in rule resets it to the original default.

For custom food types, the program gives two expiry options:
1. Enter the expiry date directly.
2. Enter the production date and shelf life, then let the program calculate the
   expiry date.
If the final expiry date is already in the past, the program asks for
confirmation before saving it as an expired item.

If the same food type is bought twice, the program stores the purchases as two
separate records with different IDs. For example, "Pork mince" and "Pork ribs"
can both use the food type "pork", but they can have different quantities,
storage locations, added dates, and expiry dates.

Small note
----------
The shelf-life numbers are only simple estimates for the project. In real life
the user should still use common sense, because packaging, temperature, and food
condition can all change the real expiry time.

Advanced concepts used
----------------------
1. File I/O:
   - load_inventory() reads data from inventory.csv.
   - save_inventory() writes updated inventory data back to inventory.csv.
   - ensure_data_file() creates the data file if it does not exist.
   - load_custom_shelf_life() and save_custom_shelf_life() manage custom rules
     in shelf_life_guide.csv.

2. Flow control and exceptions:
   - try/except is used to prevent invalid user input from crashing the program.
   - raise is used for invalid menu choices, unsupported storage locations, and
     impossible removal actions.
   - break exits menu loops after saving or after successfully removing an item.
   - continue restarts input loops after an error.

3. Testing:
   - test_smart_refrigerator_manager.py includes optional assert-based tests for
     expiry calculation, sorting, and CSV file reading/writing.

Optional tests
--------------
Run:

   python test_smart_refrigerator_manager.py

Suggested 3-minute presentation flow
------------------------------------
1. Introduce the problem: I wanted a simple way to remember what is in the
   fridge before food gets wasted.
2. Show adding a food item, choosing fresh/freezer storage, and automatic expiry
   calculation.
3. Show the main-menu expiry reminder and explain the warning labels.
4. Remove an item as eaten/discarded and show that inventory.csv updates.
5. Explain the advanced concepts: File I/O, exception handling, and optional
   tests.
