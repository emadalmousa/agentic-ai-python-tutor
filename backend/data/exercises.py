"""
Static exercise library for KI Python Tutor beginner skills.
Each skill has exactly 5 exercises with precise expected output.
"""

EXERCISES: dict[str, list[dict]] = {
    "variables": [
        {
            "id": "variables_1",
            "skill_key": "variables",
            "order": 1,
            "title": "Einfache Variable",
            "description": "Erstelle eine Variable `name` mit dem Wert `'Python'` und gib sie aus.",
            "expected_output": "Python",
            "test_type": "output_match"
        },
        {
            "id": "variables_2",
            "skill_key": "variables",
            "order": 2,
            "title": "Zwei Variablen addieren",
            "description": "Erstelle zwei Variablen `a=5` und `b=3`, berechne ihre Summe und gib sie aus.",
            "expected_output": "8",
            "test_type": "output_match"
        },
        {
            "id": "variables_3",
            "skill_key": "variables",
            "order": 3,
            "title": "Dezimalzahl speichern",
            "description": "Erstelle Variable `preis=9.99` und gib sie aus.",
            "expected_output": "9.99",
            "test_type": "output_match"
        },
        {
            "id": "variables_4",
            "skill_key": "variables",
            "order": 4,
            "title": "Boolean Variable",
            "description": "Erstelle Variable `aktiv=True` und gib sie aus.",
            "expected_output": "True",
            "test_type": "output_match"
        },
        {
            "id": "variables_5",
            "skill_key": "variables",
            "order": 5,
            "title": "Variablen verbinden",
            "description": "Erstelle Variablen `vorname='Max'` und `nachname='Müller'`, verbinde sie mit Leerzeichen und gib aus.",
            "expected_output": "Max Müller",
            "test_type": "output_match"
        },
    ],
    "datatypes": [
        {
            "id": "datatypes_1",
            "skill_key": "datatypes",
            "order": 1,
            "title": "Typ von Integer",
            "description": "Gib den Typ von `42` aus.",
            "expected_output": "<class 'int'>",
            "test_type": "output_match"
        },
        {
            "id": "datatypes_2",
            "skill_key": "datatypes",
            "order": 2,
            "title": "Typ von Float",
            "description": "Gib den Typ von `3.14` aus.",
            "expected_output": "<class 'float'>",
            "test_type": "output_match"
        },
        {
            "id": "datatypes_3",
            "skill_key": "datatypes",
            "order": 3,
            "title": "Typ von String",
            "description": "Gib den Typ von `'Hallo'` aus.",
            "expected_output": "<class 'str'>",
            "test_type": "output_match"
        },
        {
            "id": "datatypes_4",
            "skill_key": "datatypes",
            "order": 4,
            "title": "Typ von Boolean",
            "description": "Gib den Typ von `True` aus.",
            "expected_output": "<class 'bool'>",
            "test_type": "output_match"
        },
        {
            "id": "datatypes_5",
            "skill_key": "datatypes",
            "order": 5,
            "title": "Typ von Liste",
            "description": "Gib den Typ von `[1,2,3]` aus.",
            "expected_output": "<class 'list'>",
            "test_type": "output_match"
        },
    ],
    "input_output": [
        {
            "id": "input_output_1",
            "skill_key": "input_output",
            "order": 1,
            "title": "Klassischer Gruß",
            "description": "Gib `Hallo Welt!` aus.",
            "expected_output": "Hallo Welt!",
            "test_type": "output_match"
        },
        {
            "id": "input_output_2",
            "skill_key": "input_output",
            "order": 2,
            "title": "Name ausgeben",
            "description": "Gib den Namen `'Max'` auf einer Zeile aus.",
            "expected_output": "Max",
            "test_type": "output_match"
        },
        {
            "id": "input_output_3",
            "skill_key": "input_output",
            "order": 3,
            "title": "Drei Zeilen",
            "description": "Gib die Zahlen `1`, `2`, `3` jeweils auf einer eigenen Zeile aus.",
            "expected_output": "1\n2\n3",
            "test_type": "output_match"
        },
        {
            "id": "input_output_4",
            "skill_key": "input_output",
            "order": 4,
            "title": "Zwei mal wiederholen",
            "description": "Gib `Python ist toll!` zweimal hintereinander aus, je eine Zeile.",
            "expected_output": "Python ist toll!\nPython ist toll!",
            "test_type": "output_match"
        },
        {
            "id": "input_output_5",
            "skill_key": "input_output",
            "order": 5,
            "title": "Drei Ausgaben",
            "description": "Gib `Start`, dann `Mitte`, dann `Ende` je auf einer eigenen Zeile aus.",
            "expected_output": "Start\nMitte\nEnde",
            "test_type": "output_match"
        },
    ],
    "string_methods": [
        {
            "id": "string_methods_1",
            "skill_key": "string_methods",
            "order": 1,
            "title": "Großbuchstaben",
            "description": "Wandle `'hallo'` in Großbuchstaben um und gib das Ergebnis aus.",
            "expected_output": "HALLO",
            "test_type": "output_match"
        },
        {
            "id": "string_methods_2",
            "skill_key": "string_methods",
            "order": 2,
            "title": "Kleinbuchstaben",
            "description": "Wandle `'PYTHON'` in Kleinbuchstaben um und gib das Ergebnis aus.",
            "expected_output": "python",
            "test_type": "output_match"
        },
        {
            "id": "string_methods_3",
            "skill_key": "string_methods",
            "order": 3,
            "title": "Leerzeichen trimmen",
            "description": "Entferne Leerzeichen am Anfang und Ende von `'  Python  '` und gib das Ergebnis aus.",
            "expected_output": "Python",
            "test_type": "output_match"
        },
        {
            "id": "string_methods_4",
            "skill_key": "string_methods",
            "order": 4,
            "title": "Text ersetzen",
            "description": "Ersetze in `'Hallo Welt'` das Wort `'Welt'` durch `'Python'` und gib das Ergebnis aus.",
            "expected_output": "Hallo Python",
            "test_type": "output_match"
        },
        {
            "id": "string_methods_5",
            "skill_key": "string_methods",
            "order": 5,
            "title": "Zeichen zählen",
            "description": "Zähle wie oft `'l'` in `'Hallo Welt'` vorkommt und gib die Zahl aus.",
            "expected_output": "3",
            "test_type": "output_match"
        },
    ],
    "type_conversion": [
        {
            "id": "type_conversion_1",
            "skill_key": "type_conversion",
            "order": 1,
            "title": "String zu Integer",
            "description": "Konvertiere den String `'42'` in eine Ganzzahl und gib sie aus.",
            "expected_output": "42",
            "test_type": "output_match"
        },
        {
            "id": "type_conversion_2",
            "skill_key": "type_conversion",
            "order": 2,
            "title": "Float zu Integer",
            "description": "Konvertiere die Zahl `3.7` in eine Ganzzahl und gib sie aus.",
            "expected_output": "3",
            "test_type": "output_match"
        },
        {
            "id": "type_conversion_3",
            "skill_key": "type_conversion",
            "order": 3,
            "title": "Integer zu String",
            "description": "Konvertiere die Zahl `7` in einen String und gib sie aus.",
            "expected_output": "7",
            "test_type": "output_match"
        },
        {
            "id": "type_conversion_4",
            "skill_key": "type_conversion",
            "order": 4,
            "title": "String zu Float",
            "description": "Konvertiere `'3.14'` in eine Gleitkommazahl und gib sie aus.",
            "expected_output": "3.14",
            "test_type": "output_match"
        },
        {
            "id": "type_conversion_5",
            "skill_key": "type_conversion",
            "order": 5,
            "title": "Boolean zu Integer",
            "description": "Konvertiere den Boolean `True` in eine Zahl und gib sie aus.",
            "expected_output": "1",
            "test_type": "output_match"
        },
    ],
    "if_else": [
        {
            "id": "if_else_1",
            "skill_key": "if_else",
            "order": 1,
            "title": "Einfacher Vergleich",
            "description": "Schreibe Code der prüft ob `10 > 5` ist und `Ja` ausgibt.",
            "expected_output": "Ja",
            "test_type": "output_match"
        },
        {
            "id": "if_else_2",
            "skill_key": "if_else",
            "order": 2,
            "title": "Gerade oder ungerade",
            "description": "Prüfe ob `3` gerade ist — gib `gerade` oder `ungerade` aus.",
            "expected_output": "ungerade",
            "test_type": "output_match"
        },
        {
            "id": "if_else_3",
            "skill_key": "if_else",
            "order": 3,
            "title": "Vorzeichen bestimmen",
            "description": "Gib `positiv`, `negativ` oder `null` für die Zahl `-5` aus.",
            "expected_output": "negativ",
            "test_type": "output_match"
        },
        {
            "id": "if_else_4",
            "skill_key": "if_else",
            "order": 4,
            "title": "Teilbarkeit prüfen",
            "description": "Prüfe ob `15` durch `3` teilbar ist und gib `teilbar` oder `nicht teilbar` aus.",
            "expected_output": "teilbar",
            "test_type": "output_match"
        },
        {
            "id": "if_else_5",
            "skill_key": "if_else",
            "order": 5,
            "title": "Maximum bestimmen",
            "description": "Bestimme das Maximum von `8` und `12` und gib es aus.",
            "expected_output": "12",
            "test_type": "output_match"
        },
    ],
    "for_loop": [
        {
            "id": "for_loop_1",
            "skill_key": "for_loop",
            "order": 1,
            "title": "Zahlen 1 bis 5",
            "description": "Gib die Zahlen `1` bis `5` je auf einer eigenen Zeile aus.",
            "expected_output": "1\n2\n3\n4\n5",
            "test_type": "output_match"
        },
        {
            "id": "for_loop_2",
            "skill_key": "for_loop",
            "order": 2,
            "title": "Gerade Zahlen",
            "description": "Gib alle geraden Zahlen von `2` bis `10` je auf einer Zeile aus.",
            "expected_output": "2\n4\n6\n8\n10",
            "test_type": "output_match"
        },
        {
            "id": "for_loop_3",
            "skill_key": "for_loop",
            "order": 3,
            "title": "Zeichen einer Zeichenkette",
            "description": "Gib jedes Zeichen von `'Python'` auf einer eigenen Zeile aus.",
            "expected_output": "P\ny\nt\nh\no\nn",
            "test_type": "output_match"
        },
        {
            "id": "for_loop_4",
            "skill_key": "for_loop",
            "order": 4,
            "title": "Quadratzahlen",
            "description": "Gib die Quadratzahlen von `1` bis `5` je auf einer Zeile aus.",
            "expected_output": "1\n4\n9\n16\n25",
            "test_type": "output_match"
        },
        {
            "id": "for_loop_5",
            "skill_key": "for_loop",
            "order": 5,
            "title": "Summe berechnen",
            "description": "Berechne die Summe der Zahlen `1` bis `10` und gib sie aus.",
            "expected_output": "55",
            "test_type": "output_match"
        },
    ],
    "while_loop": [
        {
            "id": "while_loop_1",
            "skill_key": "while_loop",
            "order": 1,
            "title": "While bis 5",
            "description": "Gib mit einer While-Schleife die Zahlen `1` bis `5` je auf einer Zeile aus.",
            "expected_output": "1\n2\n3\n4\n5",
            "test_type": "output_match"
        },
        {
            "id": "while_loop_2",
            "skill_key": "while_loop",
            "order": 2,
            "title": "Rückwärtszählen",
            "description": "Starte bei `10` und zähle mit einer While-Schleife bis `1` herunter (je eine Zeile).",
            "expected_output": "10\n9\n8\n7\n6\n5\n4\n3\n2\n1",
            "test_type": "output_match"
        },
        {
            "id": "while_loop_3",
            "skill_key": "while_loop",
            "order": 3,
            "title": "Verdoppeln",
            "description": "Verdopple eine Zahl (starte bei `1`) so lange bis sie `>= 16` ist — gib jeden Schritt aus.",
            "expected_output": "1\n2\n4\n8\n16",
            "test_type": "output_match"
        },
        {
            "id": "while_loop_4",
            "skill_key": "while_loop",
            "order": 4,
            "title": "Vielfache von 3",
            "description": "Gib mit einer While-Schleife alle Vielfachen von `3` bis `30` aus.",
            "expected_output": "3\n6\n9\n12\n15\n18\n21\n24\n27\n30",
            "test_type": "output_match"
        },
        {
            "id": "while_loop_5",
            "skill_key": "while_loop",
            "order": 5,
            "title": "Summe mit While",
            "description": "Berechne die Summe der Zahlen `1` bis `10` mit einer While-Schleife und gib das Ergebnis aus.",
            "expected_output": "55",
            "test_type": "output_match"
        },
    ],
    "lists": [
        {
            "id": "lists_1",
            "skill_key": "lists",
            "order": 1,
            "title": "Liste ausgeben",
            "description": "Erstelle eine Liste `[1,2,3,4,5]` und gib sie aus.",
            "expected_output": "[1, 2, 3, 4, 5]",
            "test_type": "output_match"
        },
        {
            "id": "lists_2",
            "skill_key": "lists",
            "order": 2,
            "title": "Element hinzufügen",
            "description": "Füge `6` zur Liste `[1,2,3,4,5]` hinzu und gib die Liste aus.",
            "expected_output": "[1, 2, 3, 4, 5, 6]",
            "test_type": "output_match"
        },
        {
            "id": "lists_3",
            "skill_key": "lists",
            "order": 3,
            "title": "Element zugreifen",
            "description": "Gib das dritte Element der Liste `['a','b','c','d']` aus.",
            "expected_output": "c",
            "test_type": "output_match"
        },
        {
            "id": "lists_4",
            "skill_key": "lists",
            "order": 4,
            "title": "Element entfernen",
            "description": "Entferne das letzte Element aus `[1,2,3,4,5]` und gib die Liste aus.",
            "expected_output": "[1, 2, 3, 4]",
            "test_type": "output_match"
        },
        {
            "id": "lists_5",
            "skill_key": "lists",
            "order": 5,
            "title": "Listenlänge",
            "description": "Gib die Länge der Liste `['x','y','z']` aus.",
            "expected_output": "3",
            "test_type": "output_match"
        },
    ],
    "tuples": [
        {
            "id": "tuples_1",
            "skill_key": "tuples",
            "order": 1,
            "title": "Tupel ausgeben",
            "description": "Erstelle ein Tupel `(1,2,3)` und gib es aus.",
            "expected_output": "(1, 2, 3)",
            "test_type": "output_match"
        },
        {
            "id": "tuples_2",
            "skill_key": "tuples",
            "order": 2,
            "title": "Tupel-Element zugreifen",
            "description": "Gib das zweite Element des Tupels `(10,20,30)` aus.",
            "expected_output": "20",
            "test_type": "output_match"
        },
        {
            "id": "tuples_3",
            "skill_key": "tuples",
            "order": 3,
            "title": "Tupellänge",
            "description": "Gib die Länge des Tupels `('a','b','c','d')` aus.",
            "expected_output": "4",
            "test_type": "output_match"
        },
        {
            "id": "tuples_4",
            "skill_key": "tuples",
            "order": 4,
            "title": "Membership-Test",
            "description": "Prüfe ob `5` im Tupel `(1,3,5,7,9)` enthalten ist und gib `True` oder `False` aus.",
            "expected_output": "True",
            "test_type": "output_match"
        },
        {
            "id": "tuples_5",
            "skill_key": "tuples",
            "order": 5,
            "title": "Tupel zu Liste",
            "description": "Konvertiere das Tupel `(1,2,3)` in eine Liste und gib sie aus.",
            "expected_output": "[1, 2, 3]",
            "test_type": "output_match"
        },
    ],
    "sets": [
        {
            "id": "sets_1",
            "skill_key": "sets",
            "order": 1,
            "title": "Set erstellen",
            "description": "Erstelle eine Menge `{1,2,3}` und gib ihre Länge aus.",
            "expected_output": "3",
            "test_type": "output_match"
        },
        {
            "id": "sets_2",
            "skill_key": "sets",
            "order": 2,
            "title": "Duplikate entfernen",
            "description": "Erstelle die Menge `{1,2,2,3,3,3}` und gib ihre Länge aus (Duplikate werden entfernt).",
            "expected_output": "3",
            "test_type": "output_match"
        },
        {
            "id": "sets_3",
            "skill_key": "sets",
            "order": 3,
            "title": "Set Membership",
            "description": "Prüfe ob `4` in der Menge `{1,2,3,4,5}` enthalten ist und gib das Ergebnis aus.",
            "expected_output": "True",
            "test_type": "output_match"
        },
        {
            "id": "sets_4",
            "skill_key": "sets",
            "order": 4,
            "title": "Set Vereinigung",
            "description": "Gib die Vereinigungsmenge von `{1,2,3}` und `{3,4,5}` als sortierte Liste aus.",
            "expected_output": "[1, 2, 3, 4, 5]",
            "test_type": "output_match"
        },
        {
            "id": "sets_5",
            "skill_key": "sets",
            "order": 5,
            "title": "Set Schnittmenge",
            "description": "Gib die Schnittmenge von `{1,2,3,4}` und `{3,4,5,6}` aus.",
            "expected_output": "{3, 4}",
            "test_type": "output_match"
        },
    ],
    "dictionaries": [
        {
            "id": "dictionaries_1",
            "skill_key": "dictionaries",
            "order": 1,
            "title": "Dict-Wert zugreifen",
            "description": "Erstelle ein Dictionary `{'name': 'Python', 'version': 3}` und gib den Wert von `'name'` aus.",
            "expected_output": "Python",
            "test_type": "output_match"
        },
        {
            "id": "dictionaries_2",
            "skill_key": "dictionaries",
            "order": 2,
            "title": "Eintrag hinzufügen",
            "description": "Füge dem Dictionary `{'a': 1}` den Eintrag `'b': 2` hinzu und gib die Länge aus.",
            "expected_output": "2",
            "test_type": "output_match"
        },
        {
            "id": "dictionaries_3",
            "skill_key": "dictionaries",
            "order": 3,
            "title": "Schlüssel prüfen",
            "description": "Prüfe ob der Schlüssel `'x'` im Dictionary `{'x': 10, 'y': 20}` vorhanden ist und gib `True` oder `False` aus.",
            "expected_output": "True",
            "test_type": "output_match"
        },
        {
            "id": "dictionaries_4",
            "skill_key": "dictionaries",
            "order": 4,
            "title": "Keys auflisten",
            "description": "Gib alle Schlüssel des Dictionaries `{'a':1,'b':2,'c':3}` als sortierte Liste aus.",
            "expected_output": "['a', 'b', 'c']",
            "test_type": "output_match"
        },
        {
            "id": "dictionaries_5",
            "skill_key": "dictionaries",
            "order": 5,
            "title": "Eintrag löschen",
            "description": "Entferne den Eintrag `'b'` aus `{'a':1,'b':2,'c':3}` und gib die verbleibende Länge aus.",
            "expected_output": "2",
            "test_type": "output_match"
        },
    ],
    "functions": [
        {
            "id": "functions_1",
            "skill_key": "functions",
            "order": 1,
            "title": "Einfache Funktion",
            "description": "Schreibe eine Funktion `begruesse` die `Hallo Python!` ausgibt, und rufe sie auf.",
            "expected_output": "Hallo Python!",
            "test_type": "output_match"
        },
        {
            "id": "functions_2",
            "skill_key": "functions",
            "order": 2,
            "title": "Summen-Funktion",
            "description": "Schreibe eine Funktion `addiere(a,b)` die die Summe zurückgibt. Ruf sie mit `3` und `4` auf und gib das Ergebnis aus.",
            "expected_output": "7",
            "test_type": "output_match"
        },
        {
            "id": "functions_3",
            "skill_key": "functions",
            "order": 3,
            "title": "Quadrat-Funktion",
            "description": "Schreibe eine Funktion `quadrat(n)` die das Quadrat von `n` zurückgibt. Ruf sie mit `5` auf.",
            "expected_output": "25",
            "test_type": "output_match"
        },
        {
            "id": "functions_4",
            "skill_key": "functions",
            "order": 4,
            "title": "Boolean-Funktion",
            "description": "Schreibe eine Funktion `ist_gerade(n)` die `True` zurückgibt wenn `n` gerade ist, sonst `False`. Teste mit `8`.",
            "expected_output": "True",
            "test_type": "output_match"
        },
        {
            "id": "functions_5",
            "skill_key": "functions",
            "order": 5,
            "title": "Maximum-Funktion",
            "description": "Schreibe eine Funktion `max_von_drei(a,b,c)` die die größte Zahl zurückgibt. Teste mit `4`, `9`, `2`.",
            "expected_output": "9",
            "test_type": "output_match"
        },
    ],
}
