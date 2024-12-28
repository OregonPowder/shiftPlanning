from ortools.sat.python import cp_model
from datetime import datetime, timedelta

# Konfiguration
work_hours_per_month = 173  # Maximale Stunden ohne Überstunden (rund 173 Stunden pro Monat als Basis)
shift_start_day = datetime(2025, 1, 1, 8, 0, 0)  # 1. Januar 2025, 8:00 Uhr
num_days_in_month = 31  # Gesamtzahl der Tage im Monat (31 Tage für Test)
employees = [f"Mitarbeiter {i}" for i in range(1, 12)]
DAY_SHIFT_HOURS = 8  # Stunden von 8-16 Uhr
NIGHT_SHIFT_HOURS = 16  # Stunden von 16-8 Uhr (nächster Tag)
MINIMUM_REST_HOURS = 11  # Mindestpause zwischen Schichten
MAX_SHIFT_HOURS_PER_DAY = 16  # Maximale Arbeitszeit pro Tag
public_holidays = [datetime(2025, 1, 1), datetime(2025, 12, 25)]  # Beispiel-Feiertage

# Optimierungsmodell und Schichtplanung
def optimize_schedule():
    model = cp_model.CpModel()
    
    # Variablen für Schichten
    shifts = {}
    for day in range(1, num_days_in_month + 1):
        for employee in employees:
            shifts[(employee, day, "Tagesschicht")] = model.NewBoolVar(f"shift_{employee}_{day}_day")
            shifts[(employee, day, "Nachtschicht")] = model.NewBoolVar(f"shift_{employee}_{day}_night")
    
    # 1. Sicherstellen, dass Nachtschichten besetzt sind (mindestens 1 Nachtschicht pro Tag)
    for day in range(1, num_days_in_month + 1):
        model.Add(sum(shifts[(employee, day, "Nachtschicht")] for employee in employees) == 1)  # 1 Nachtschicht pro Tag
    
    # 2. Sicherstellen, dass 6 Mitarbeiter für die Tagesschicht pro Tag eingeplant sind
    for day in range(1, num_days_in_month + 1):
        model.Add(sum(shifts[(employee, day, "Tagesschicht")] for employee in employees) == 6)
    
    # 3. Keine Mitarbeiter sollen beide Schichten an einem Tag haben
    for day in range(1, num_days_in_month + 1):
        for employee in employees:
            model.Add(shifts[(employee, day, "Tagesschicht")] + shifts[(employee, day, "Nachtschicht")] <= 1)
    
    # 4. Flexiblere Nachtschichtverteilung: Hier wird jeder Mitarbeiter eine bestimmte Anzahl von Nachtschichten zugewiesen, aber flexibel
    min_night_shifts_per_employee = num_days_in_month // len(employees)  # Minimale Anzahl der Nachtschichten
    max_night_shifts_per_employee = min_night_shifts_per_employee + 1  # Maximale Anzahl der Nachtschichten
    for employee in employees:
        model.Add(sum(shifts[(employee, day, "Nachtschicht")] for day in range(1, num_days_in_month + 1)) >= min_night_shifts_per_employee)
        model.Add(sum(shifts[(employee, day, "Nachtschicht")] for day in range(1, num_days_in_month + 1)) <= max_night_shifts_per_employee)
    
    # 5. Zuweisung der Stunden (Arbeit und Überstunden)
    total_hours = {}
    overtime = {}  # Überstunden speichern
    for employee in employees:
        total_hours[employee] = model.NewIntVar(0, work_hours_per_month * 2, f'total_hours_{employee}')
        overtime[employee] = model.NewIntVar(0, work_hours_per_month, f'overtime_{employee}')
    
    # Berechne die Gesamtarbeitsstunden für Tagesschicht und Nachtschicht pro Mitarbeiter
    for employee in employees:
        work_hours_expr = model.NewIntVar(0, work_hours_per_month * 2, f'work_hours_expr_{employee}')
        
        expr = sum(
            shifts[(employee, day, "Tagesschicht")] * DAY_SHIFT_HOURS +
            shifts[(employee, day, "Nachtschicht")] * NIGHT_SHIFT_HOURS
            for day in range(1, num_days_in_month + 1)
        )
        model.Add(work_hours_expr == expr)
        model.Add(total_hours[employee] == work_hours_expr)
        # Überstunden: Wenn Arbeitsstunden > 173 Stunden sind
        model.Add(overtime[employee] == total_hours[employee] - work_hours_per_month)
    
    # 6. Sicherstellen, dass die Mindestruhezeit eingehalten wird
    for day in range(1, num_days_in_month):
        for employee in employees:
            # Wenn ein Mitarbeiter eine Nachtschicht hat, darf er am nächsten Tag keine Tagesschicht haben
            model.Add(shifts[(employee, day, "Nachtschicht")] + shifts[(employee, day + 1, "Tagesschicht")] <= 1)
            # Wenn ein Mitarbeiter eine Tagesschicht hat, darf er am nächsten Tag keine Nachtschicht haben
            model.Add(shifts[(employee, day, "Tagesschicht")] + shifts[(employee, day + 1, "Nachtschicht")] <= 1)
    
    # 7. Minimierung der Überstunden
    model.Minimize(sum(overtime[employee] for employee in employees))
    
    # 8. Minimierung der Differenz zwischen den Arbeitszeiten der Mitarbeiter (für eine gleichmäßigere Verteilung)
    # Hilfsvariablen für das Quadrat der Differenz
    square_diff_vars = {}
    for employee in employees:
        square_diff_vars[employee] = model.NewIntVar(0, work_hours_per_month, f'square_diff_{employee}')
        model.Add(square_diff_vars[employee] == total_hours[employee] - work_hours_per_month)
    
    # Das Quadrat der Differenzen berechnen
    square_diff_vars_squares = {}
    for employee in employees:
        square_diff_vars_squares[employee] = model.NewIntVar(0, work_hours_per_month * work_hours_per_month, f'square_diff_{employee}_square')
        model.AddMultiplicationEquality(square_diff_vars_squares[employee], [square_diff_vars[employee], square_diff_vars[employee]])
    
    # Minimierung der quadratischen Differenz
    model.Minimize(sum(square_diff_vars_squares[employee] for employee in employees))
    
    # Solver
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status == cp_model.OPTIMAL:
        schedule = {employee: [] for employee in employees}
        
        # Berechne die Schichten nach der Lösung
        for employee in employees:
            for day in range(1, num_days_in_month + 1):
                if solver.Value(shifts[(employee, day, "Tagesschicht")]) == 1:
                    schedule[employee].append(("Tagesschicht", day))
                elif solver.Value(shifts[(employee, day, "Nachtschicht")]) == 1:
                    schedule[employee].append(("Nachtschicht", day))
        return schedule, total_hours, overtime, solver
    else:
        print(f"Keine Lösung gefunden. Status: {status}")
        return None, None, None, None

# Monatplan in Markdown speichern
def save_schedule_to_md(schedule, total_hours, overtime, filepath):
    with open(filepath, mode='w', encoding='utf-8') as file:
        # Header der Tabelle mit den Mitarbeiterdaten
        file.write("| Mitarbeiter | Tagesschichten | Nachtschichten | Arbeitszeit (h) | Überstunden (h) | Maximale Stunden (h) |\n")
        file.write("|-------------|----------------|----------------|-----------------|------------------|----------------------|\n")
        
        for employee, shifts in schedule.items():
            day_shifts = [shift for shift, day in shifts if shift == "Tagesschicht"]
            night_shifts = [shift for shift, day in shifts if shift == "Nachtschicht"]
            
            total_work_hours = len(day_shifts) * DAY_SHIFT_HOURS + len(night_shifts) * NIGHT_SHIFT_HOURS
            overtime_hours = max(0, total_work_hours - work_hours_per_month)  # Überstunden
            file.write(f"| {employee} | {len(day_shifts)} | {len(night_shifts)} | {total_work_hours} | {overtime_hours} | {work_hours_per_month} |\n")
        
        # Monatplan hinzufügen
        file.write("\n## Monatplan\n\n")
        file.write("| Tag | Tagesschicht | Nachtschicht |\n")
        file.write("|-----|--------------|--------------|\n")
        
        # Erstelle den Monatplan
        for day in range(1, num_days_in_month + 1):
            file.write(f"| {shift_start_day + timedelta(days=day-1):%d.%m.%Y} | ")
            # Ermittlung der Besetzung für Tagesschicht und Nachtschicht
            day_shift_employees = [employee for employee in employees if any(shift[1] == day and shift[0] == "Tagesschicht" for shift in schedule.get(employee, []))]
            night_shift_employees = [employee for employee in employees if any(shift[1] == day and shift[0] == "Nachtschicht" for shift in schedule.get(employee, []))]
            
            # Verwende <br> zum Trennen der Namen
            file.write("<br>".join(day_shift_employees) + " | " + "<br>".join(night_shift_employees) + " |\n")

# Schichtplan optimieren und speichern
schedule, total_hours, overtime, solver = optimize_schedule()
if schedule:
    save_schedule_to_md(schedule, total_hours, overtime, "schichtplan_mit_auswertung.md")
