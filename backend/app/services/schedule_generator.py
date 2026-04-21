"""
MedicSync — Schedule Generator Service 

Coduri tura:
  D = Dimineata  07:00-15:00
  A = Amiaza     15:00-23:00
  N = Noapte     23:00-07:00
  L = Zi libera
  C = Concediu aprobat
"""

import calendar
from datetime import date, timedelta
from typing import Any

from sqlalchemy.orm import Session

from ..models import User, RoleEnum, VacationRequest, VacationRequestStatusEnum, RequestTypeEnum

SHIFT_D = "D"
SHIFT_A = "A"
SHIFT_N = "N"
SHIFT_L = "L"
SHIFT_C = "C"

WORKING_SHIFTS = {SHIFT_D, SHIFT_A, SHIFT_N}
DEFAULT_TEMP = 18.0


DEPT_PROFILES: dict[int, dict] = {
    2: { 
        "shifts_needed":         {"D": 3, "A": 3, "N": 2},
        "max_consecutive":        4,
        "max_nights_per_month":   8,
        "min_rest_after_night":   2,
        "max_consecutive_nights": 2,
    },
    3: { 
        "shifts_needed":         {"D": 2, "A": 2, "N": 2},
        "max_consecutive":        5,
        "max_nights_per_month":  10,
        "min_rest_after_night":   2,
        "max_consecutive_nights": 3,
    },
    4: {
        "shifts_needed":         {"D": 2, "A": 2, "N": 2},
        "max_consecutive":        5,
        "max_nights_per_month":  10,
        "min_rest_after_night":   2,
        "max_consecutive_nights": 3,
    },
    5: {
        "shifts_needed":         {"D": 3, "A": 2, "N": 2},
        "max_consecutive":        4,
        "max_nights_per_month":   9,
        "min_rest_after_night":   2,
        "max_consecutive_nights": 2,
    },
    6: {
        "shifts_needed":         {"D": 3, "A": 3, "N": 2},
        "max_consecutive":        4,
        "max_nights_per_month":   8,
        "min_rest_after_night":   2,
        "max_consecutive_nights": 2,
    },
    7: {
        "shifts_needed":         {"D": 2, "A": 2, "N": 2},
        "max_consecutive":        5,
        "max_nights_per_month":  10,
        "min_rest_after_night":   2,
        "max_consecutive_nights": 3,
    },
}

DEFAULT_PROFILE: dict = {
    "shifts_needed":         {"D": 2, "A": 2, "N": 2},
    "max_consecutive":        5,
    "max_nights_per_month":  10,
    "min_rest_after_night":   2,
    "max_consecutive_nights": 3,
}


def _get_profile(department_id: int) -> dict:
    return DEPT_PROFILES.get(department_id, DEFAULT_PROFILE)


def _compute_shift_targets(num_nurses: int, profile: dict) -> dict[str, int]:
    ideal = profile["shifts_needed"]
    ideal_total = sum(ideal.values())
    # 67% din echipa lucreaza simultan → ~20 ture/luna
    target_working = max(6, round(num_nurses * 0.67))
    min_per_shift = 2 if num_nurses >= 6 else 1

    ratio = target_working / ideal_total
    result = {
        "D": max(min_per_shift, round(ideal["D"] * ratio)),
        "A": max(min_per_shift, round(ideal["A"] * ratio)),
        "N": max(min_per_shift, round(ideal["N"] * ratio)),
    }

    diff = target_working - sum(result.values())
    if diff > 0:
        result["D"] += diff
    elif diff < 0:
        for key in ["A", "D", "N"]:
            while diff < 0 and result[key] > min_per_shift:
                result[key] -= 1
                diff += 1

    return result

def _can_work(
    nurse_id:           int,
    shift_type:         str,
    schedule:           dict[str, dict[str, str]],
    year:               int,
    month:              int,
    day_num:            int,
    profile:            dict,
    night_counts:       dict[int, int],
    consecutive_nights: dict[int, int],
) -> bool:
    nid_str    = str(nurse_id)
    max_cons   = profile["max_consecutive"]
    max_nights = profile["max_nights_per_month"]
    min_rest   = profile["min_rest_after_night"]
    max_cons_n = profile["max_consecutive_nights"]

    def gs(d: int) -> str:
        if d < 1 or d >= day_num:
            return SHIFT_L
        ds = date(year, month, d).isoformat()
        return schedule.get(nid_str, {}).get(ds, SHIFT_L)

    consec = 0
    for back in range(1, max_cons + 1):
        if gs(day_num - back) in WORKING_SHIFTS:
            consec += 1
        else:
            break
    if consec >= max_cons:
        return False

    if shift_type in {SHIFT_D, SHIFT_A} and gs(day_num - 1) == SHIFT_N:
        return False

    if shift_type == SHIFT_N:
        if consecutive_nights.get(nurse_id, 0) >= max_cons_n:
            return False
        if night_counts.get(nurse_id, 0) >= max_nights:
            return False
        
    if shift_type in WORKING_SHIFTS:
        for back in range(1, min_rest + 1):
            end_day = day_num - back
            if end_day < 1:
                break
            if gs(end_day) != SHIFT_N:
                continue
            if end_day + 1 >= day_num:
                # Ziua urmatoare e azi (nealocat inca).
                # Daca vrem N → extindem blocul, R2 nu se aplica.
                if shift_type == SHIFT_N:
                    continue
                return False  # D sau A in perioada de repaus post-bloc
            else:
                if gs(end_day + 1) != SHIFT_N:
                    # Blocul s-a terminat la end_day, suntem in fereastra de repaus.
                    return False
                # Altfel blocul a continuat, end_day nu era ultimul N.

    return True


def _predict_nurses_for_day(target_date: date, department_id: int) -> int:
    try:
        from .staff_predictor import predict_staff_needs
        result = predict_staff_needs(
            target_date=target_date,
            weather_temp=DEFAULT_TEMP,
            is_holiday=False,
            is_epidemic=False,
            department_id=department_id,
        )
        return max(1, result["recommended_nurses"])
    except Exception:
        return 2


def generate_monthly_schedule(
    db:            Session,
    department_id: int,
    year:          int,
    month:         int,
) -> dict[str, Any]:

    nurses = (
        db.query(User)
        .filter(User.department_id == department_id, User.role == RoleEnum.nurse)
        .order_by(User.full_name)
        .all()
    )
    if not nurses:
        return {"nurses": [], "schedule": {}, "daily_stats": {}, "violations": [], "targets": {}}

    profile    = _get_profile(department_id)
    nurse_ids  = [n.id for n in nurses]
    num_nurses = len(nurses)
    num_days   = calendar.monthrange(year, month)[1]
    targets    = _compute_shift_targets(num_nurses, profile)

    month_start = date(year, month, 1)
    month_end   = date(year, month, num_days)
    approved = (
        db.query(VacationRequest)
        .filter(
            VacationRequest.nurse_id.in_(nurse_ids),
            VacationRequest.status == VacationRequestStatusEnum.approved,
            VacationRequest.start_date <= month_end,
            VacationRequest.end_date   >= month_start,
        )
        .all()
    )
    override: dict[int, dict[date, str]] = {nid: {} for nid in nurse_ids}
    for req in approved:
        code = SHIFT_C if req.request_type == RequestTypeEnum.vacation else SHIFT_L
        d = req.start_date
        while d <= req.end_date:
            if month_start <= d <= month_end:
                override[req.nurse_id][d] = code
            d += timedelta(days=1)

    total_work:         dict[int, int]            = {nid: 0 for nid in nurse_ids}
    night_counts:       dict[int, int]            = {nid: 0 for nid in nurse_ids}
    consecutive_nights: dict[int, int]            = {nid: 0 for nid in nurse_ids}
    type_counts:        dict[int, dict[str, int]] = {
        nid: {SHIFT_D: 0, SHIFT_A: 0, SHIFT_N: 0} for nid in nurse_ids
    }

    schedule: dict[str, dict[str, str]] = {str(n.id): {} for n in nurses}

    for day_num in range(1, num_days + 1):
        current_date = date(year, month, day_num)
        date_str     = current_date.isoformat()

        # Marcheaza concedii/libere aprobate
        on_leave: set[int] = set()
        for nid in nurse_ids:
            if current_date in override[nid]:
                schedule[str(nid)][date_str] = override[nid][current_date]
                on_leave.add(nid)

        available = [nid for nid in nurse_ids if nid not in on_leave]
        assigned:  set[int] = set()

        for shift_type, target in [
            (SHIFT_N, targets["N"]),
            (SHIFT_D, targets["D"]),
            (SHIFT_A, targets["A"]),
        ]:
            eligible = [
                nid for nid in available
                if nid not in assigned
                and _can_work(
                    nid, shift_type, schedule, year, month, day_num,
                    profile, night_counts, consecutive_nights,
                )
            ]
            if shift_type == SHIFT_N:
                eligible.sort(key=lambda nid: (night_counts[nid], total_work[nid]))
            elif shift_type == SHIFT_D:
                eligible.sort(key=lambda nid: (type_counts[nid][SHIFT_D], total_work[nid]))
            else:
                eligible.sort(key=lambda nid: (type_counts[nid][SHIFT_A], total_work[nid]))

            for nid in eligible[:target]:
                schedule[str(nid)][date_str] = shift_type
                assigned.add(nid)
                total_work[nid]              += 1
                type_counts[nid][shift_type] += 1
                if shift_type == SHIFT_N:
                    night_counts[nid]       += 1
                    consecutive_nights[nid] += 1

        for nid in available:
            if nid not in assigned:
                schedule[str(nid)][date_str] = SHIFT_L
            if schedule[str(nid)].get(date_str) != SHIFT_N:
                consecutive_nights[nid] = 0


    violations = _final_validation(schedule, nurse_ids, year, month, num_days, profile)

    daily_stats: dict[str, dict] = {}
    for day_num in range(1, num_days + 1):
        current_date = date(year, month, day_num)
        date_str     = current_date.isoformat()
        day_shifts   = [schedule[str(nid)].get(date_str, SHIFT_L) for nid in nurse_ids]
        daily_stats[date_str] = {
            "needed_per_shift": _predict_nurses_for_day(current_date, department_id),
            "assigned_d":       day_shifts.count(SHIFT_D),
            "assigned_a":       day_shifts.count(SHIFT_A),
            "assigned_n":       day_shifts.count(SHIFT_N),
            "on_leave":         day_shifts.count(SHIFT_C) + day_shifts.count(SHIFT_L),
        }

    return {
        "nurses":      [{"id": n.id, "name": n.full_name} for n in nurses],
        "schedule":    schedule,
        "daily_stats": daily_stats,
        "violations":  violations,
        "targets":     targets,
    }


def _final_validation(
    schedule:  dict[str, dict[str, str]],
    nurse_ids: list[int],
    year:      int,
    month:     int,
    num_days:  int,
    profile:   dict,
) -> list[str]:
    
    violations = []
    max_cons   = profile["max_consecutive"]

    for nid in nurse_ids:
        nid_str = str(nid)
        dates  = [date(year, month, d).isoformat() for d in range(1, num_days + 1)]
        shifts = [schedule[nid_str].get(d, SHIFT_L) for d in dates]

        for i in range(len(shifts) - 1):
            if shifts[i] == SHIFT_N and shifts[i + 1] in {SHIFT_D, SHIFT_A}:
                violations.append(
                    f"[R1] Asistenta {nid}, ziua {i + 2}: N→{shifts[i + 1]} (repaus insuficient)"
                )

        consec = 0
        for i, s in enumerate(shifts):
            if s in WORKING_SHIFTS:
                consec += 1
                if consec > max_cons:
                    violations.append(
                        f"[R3] Asistenta {nid}, ziua {i + 1}: {consec} ture consecutive"
                    )
            else:
                consec = 0

    return violations
