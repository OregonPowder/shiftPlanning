from datetime import datetime, timedelta
import random
import calendar

# Konfigurationen
work_hours_per_week = 40
shift_start_day = datetime(2025, 1, 1, 8, 0, 0)  # 1. Januar 2025, 8:00 Uhr
num_days_in_month = 31  # Fester Wert für Januar
public_holidays = [datetime(2025, 1, 1), datetime(2025, 12, 25)]  # Beispiel für Feiertage

# Mitarbeiter als Variablen
mitarbeiter1 = "Mitarbeiter 1"
mitarbeiter2 = "Mitarbeiter 2"
mitarbeiter3 = "Mitarbeiter 3"
mitarbeiter4 = "Mitarbeiter 4"
mitarbeiter5 = "Mitarbeiter 5"
mitarbeiter6 = "Mitarbeiter 6"
mitarbeiter7 = "Mitarbeiter 7"
mitarbeiter8 = "Mitarbeiter 8"
mitarbeiter9 = "Mitarbeiter 9"
mitarbeiter10 = "Mitarbeiter 10"
mitarbeiter11 = "Mitarbeiter 11"

employees = [
    mitarbeiter1, mitarbeiter2, mitarbeiter3, mitarbeiter4, mitarbeiter5,
    mitarbeiter6, mitarbeiter7, mitarbeiter8, mitarbeiter9, mitarbeiter10, mitarbeiter11
]

# Schichtdefinition
DAY_SHIFT_HOURS = 8  # Stunden von 8-16 Uhr
NIGHT_SHIFT_HOURS = 16  # Stunden von 16-8 Uhr (nächster Tag)
AFTERNOON_SHIFT_HOURS = 8  # Stunden von 12-20 Uhr

# Beispiel für Mitarbeiterpräferenzen
employee_preferences = {
    mitarbeiter1: 'Tagesschicht',
    mitarbeiter2: 'Nachtschicht',
    mitarbeiter3: 'Spätschicht',
    mitarbeiter4: 'Tagesschicht',
    mitarbeiter5: 'Tagesschicht',
    mitarbeiter6: 'Spätschicht',
    mitarbeiter7: 'Nachtschicht',
    mitarbeiter8: 'Tagesschicht',
    mitarbeiter9: 'Spätschicht',
    mitarbeiter10: 'Nachtschicht',
    mitarbeiter11: 'Tagesschicht'
}

# Urlaubsplanung
employee_availabilities = {
    mitarbeiter1: [datetime(2025, 1, 10), datetime(2025, 1, 15)],  # Urlaub an bestimmten Tagen
    mitarbeiter3: [datetime(2025, 1, 5)],
    mitarbeiter7: [datetime(2025, 1, 20)]
}

# Funktion zur Schichtplanung
def generate_schedule():
    schedule = {employee: [] for employee in employees}

    for day in range(1, num_days_in_month + 1):
        date = shift_start_day.replace(day=day)

        # Überprüfen, ob der Tag ein Feiertag ist
        if date in public_holidays:
            continue  # Feiertage werden übersprungen

        available_employees = [emp for emp in employees if date not in employee_availabilities.get(emp, [])]

        # Sicherstellen, dass Mitarbeiter nicht mehr als 12 Stunden hintereinander arbeiten
        for emp in employees:
            if any(
                shift[1] == "Nachtschicht" and shift[0].date() == (date - timedelta(days=1)).date()
                for shift in schedule[emp]
            ):
                available_employees.remove(emp)

        # Sicherstellen, dass die Stunden gleichmäßig verteilt sind
        sorted_employees = sorted(
            available_employees,
            key=lambda e: sum(NIGHT_SHIFT_HOURS if s[1] == "Nachtschicht" else DAY_SHIFT_HOURS for s in schedule[e])
        )

        daily_employees = sorted_employees[:7]  # 6 für Tag, 1 für Nacht

        # Schichtpräferenzen berücksichtigen
        for emp in daily_employees:
            if employee_preferences.get(emp):
                preferred_shift = employee_preferences[emp]
                if preferred_shift == 'Tagesschicht':
                    schedule[emp].append((date, "Tagesschicht"))
                elif preferred_shift == 'Nachtschicht':
                    night_date = date + timedelta(hours=DAY_SHIFT_HOURS)
                    schedule[emp].append((night_date, "Nachtschicht"))
                elif preferred_shift == 'Spätschicht':
                    schedule[emp].append((date.replace(hour=12), "Spätschicht"))
            else:
                # Zufällige Schichtverteilung, wenn keine Präferenz besteht
                if len(schedule[emp]) % 2 == 0:
                    schedule[emp].append((date, "Tagesschicht"))
                else:
                    schedule[emp].append((date + timedelta(hours=DAY_SHIFT_HOURS), "Nachtschicht"))

    return schedule

# Funktion, um sicherzustellen, dass niemand Überstunden macht
def validate_schedule(schedule):
    for employee, shifts in schedule.items():
        total_hours = sum(
            NIGHT_SHIFT_HOURS if shift[1] == "Nachtschicht" else DAY_SHIFT_HOURS for shift in shifts
        )
        if total_hours > work_hours_per_week * 4:
            print(f"Warnung: {employee} hat Überstunden: {total_hours} Stunden im Monat")

# Ersatzregelung im Notfall
def handle_emergency_replacement(schedule):
    for day in range(1, num_days_in_month + 1):
        date = shift_start_day.replace(day=day)

        if date in public_holidays:
            continue  # Feiertage werden übersprungen

        # Finden von Mitarbeitern, die ihre Schicht nicht antreten können (z.B. Krankheit)
        unavailable_employees = [emp for emp in employees if date in employee_availabilities.get(emp, [])]

        # Ersatzplan für fehlende Mitarbeiter
        for emp in unavailable_employees:
            available_employees = [e for e in employees if e not in unavailable_employees]
            if available_employees:
                replacement = random.choice(available_employees)
                print(f"Notfall-Ersatz: {emp} ist nicht verfügbar, {replacement} übernimmt am {date.strftime('%d.%m.%Y')}")
                # Ersetze die Schicht des Mitarbeiters durch einen verfügbaren
                replacement_shift = 'Nachtschicht' if 'Nachtschicht' in [shift[1] for shift in schedule[replacement]] else 'Tagesschicht'
                schedule[replacement].append((date, replacement_shift))

# Feiertagsprüfung und Schichtplan anpassen
def adjust_for_holidays(schedule):
    for holiday in public_holidays:
        for employee in employees:
            if holiday not in employee_availabilities.get(employee, []):
                # Mitarbeiter am Feiertag einplanen, falls verfügbar
                schedule[employee].append((holiday, 'Feiertagsschicht'))

# Schichtplan als übersichtliches Tabellenformat speichern
def save_schedule_to_calendar(schedule, filepath):
    with open(filepath, mode='w', encoding='utf-8') as file:
        file.write("Schichtplan Januar 2025\n")
        file.write("===========================\n")
        file.write("Hinweise:\n")
        file.write("- Jede Tagesschicht dauert 8 Stunden (08:00 - 16:00).\n")
        file.write("- Jede Nachtschicht dauert 16 Stunden (16:00 - 08:00).\n")
        file.write("- Jede Spätschicht dauert 8 Stunden (12:00 - 20:00).\n")
        file.write("- Mitarbeiter dürfen nicht direkt hintereinander länger als 12 Stunden arbeiten.\n")
        file.write("- Feiertage sind nicht berücksichtigt, außer für spezielle Feiertagsschichten.\n")
        file.write("- Jede Person sollte gleichmäßig über den Monat verteilt arbeiten.\n")
        file.write("\n")
        file.write("Datum       | Tagesschicht                     | Nachtschicht | Spätschicht\n")
        file.write("-------------------------------------------------------------\n")

        for day in range(1, num_days_in_month + 1):
            date = shift_start_day.replace(day=day)
            day_employees = [
                employee for employee, shifts in schedule.items()
                for shift in shifts if shift[0].date() == date.date() and shift[1] == "Tagesschicht"
            ]
            night_employees = [
                employee for employee, shifts in schedule.items()
                for shift in shifts if shift[0].date() == date.date() and shift[1] == "Nachtschicht"
            ]
            afternoon_employees = [
                employee for employee, shifts in schedule.items()
                for shift in shifts if shift[0].date() == date.date() and shift[1] == "Spätschicht"
            ]

            file.write(f"{date.strftime('%d.%m.%Y')} | {', '.join(day_employees):<30} | {', '.join(night_employees):<12} | {', '.join(afternoon_employees)}\n")

        # Zusammenfassung pro Mitarbeiter
        file.write("\nZusammenfassung pro Mitarbeiter:\n")
        file.write("--------------------------------\n")
        for employee, shifts in schedule.items():
            work_days = len(set(shift[0].date() for shift in shifts))
            total_hours = sum(
                NIGHT_SHIFT_HOURS if shift[1] == "Nachtschicht" else DAY_SHIFT_HOURS for shift in shifts
            )
            day_shifts = sum(1 for shift in shifts if shift[1] == "Tagesschicht")
            night_shifts = sum(1 for shift in shifts if shift[1] == "Nachtschicht")
            afternoon_shifts = sum(1 for shift in shifts if shift[1] == "Spätschicht")

            file.write(f"{employee}:\n")
            file.write(f"  - Arbeitstage: {work_days}\n")
            file.write(f"  - Gesamtstunden: {total_hours} Stunden\n")
            file.write(f"  - Tagesschichten: {day_shifts}\n")
            file.write(f"  - Nachtschichten: {night_shifts}\n")
            file.write(f"  - Spätschichten: {afternoon_shifts}\n")

# Hauptprogramm
if __name__ == "__main__":
    schedule = generate_schedule()

    # Schichtplan validieren
    validate_schedule(schedule)

    # Notfallersatzregelung prüfen
    handle_emergency_replacement(schedule)

    # Feiertage und Urlaubsplanung berücksichtigen
    adjust_for_holidays(schedule)

    # Schichtplan speichern
    save_schedule_to_calendar(schedule, "schichtplan_januar_2025.csv")

    print("Der Schichtplan wurde erfolgreich generiert und gespeichert.")
