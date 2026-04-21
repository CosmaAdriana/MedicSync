"""
MedicSync — Grafic Lunar
Asistent: solicitare concedii / zile libere
Manager:  generare AI grafic lunar, editare și export CSV
"""

import calendar
import io
import json
import sys
import os
from datetime import date, datetime

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import require_auth, get_user_role, handle_api_exception
from components.navigation import render_top_nav

st.set_page_config(page_title="Grafic Lunar", page_icon="📅", layout="wide",
                   initial_sidebar_state="collapsed")
require_auth(allowed_roles=["nurse", "manager"])
render_top_nav()

# ---------------------------------------------------------------------------
# Constante vizuale
# ---------------------------------------------------------------------------
SHIFT_COLORS = {
    "D": "#3b82f6",   # albastru — Dimineață
    "A": "#f59e0b",   # portocaliu — Amiază
    "N": "#8b5cf6",   # violet — Noapte
    "C": "#10b981",   # verde — Concediu
    "M": "#ef4444",   # roșu — Concediu Medical
    "L": "#6b7280",   # gri — Zi liberă
}
SHIFT_LABELS = {
    "D": "Dimineață 07-15",
    "A": "Amiază 15-23",
    "N": "Noapte 23-07",
    "C": "Concediu",
    "M": "Concediu Medical",
    "L": "Zi liberă",
}
MONTHS_RO = {
    1: "Ianuarie", 2: "Februarie", 3: "Martie", 4: "Aprilie",
    5: "Mai", 6: "Iunie", 7: "Iulie", 8: "August",
    9: "Septembrie", 10: "Octombrie", 11: "Noiembrie", 12: "Decembrie",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
SHIFT_BG = {
    "D": "#dbeafe",  # albastru deschis
    "A": "#fef3c7",  # portocaliu deschis
    "N": "#ede9fe",  # violet deschis
    "C": "#d1fae5",  # verde deschis
    "M": "#fee2e2",  # roșu deschis
    "L": "#f3f4f6",  # gri deschis
}
SHIFT_FG = {
    "D": "#1d4ed8",
    "A": "#b45309",
    "N": "#6d28d9",
    "C": "#065f46",
    "M": "#b91c1c",
    "L": "#374151",
}


def _color_cell(val: str) -> str:
    bg = SHIFT_BG.get(str(val), "#ffffff")
    fg = SHIFT_FG.get(str(val), "#374151")
    return f"background-color:{bg};color:{fg};font-weight:700;text-align:center;"


def _styled_dataframe(df):
    """Returnează DataFrame-ul cu culori aplicate per celulă."""
    return df.style.applymap(_color_cell)


def _legend():
    cols = st.columns(len(SHIFT_COLORS))
    for col, (code, color) in zip(cols, SHIFT_COLORS.items()):
        label = SHIFT_LABELS[code]
        col.markdown(
            f'<div style="background:{color};color:white;padding:4px 8px;'
            f'border-radius:6px;text-align:center;font-size:0.78rem;font-weight:600;">'
            f'{code if code else "—"} {label}</div>',
            unsafe_allow_html=True,
        )


def _build_dataframe(schedule_data: dict, year: int, month: int) -> pd.DataFrame:
    """Construiește DataFrame-ul editabil: rânduri = asistenți, coloane = zile."""
    nurses = schedule_data["nurses"]
    sched = schedule_data["schedule"]
    num_days = calendar.monthrange(year, month)[1]

    rows = {}
    for nurse in nurses:
        nid = str(nurse["id"])
        row = {}
        for d in range(1, num_days + 1):
            date_str = f"{year}-{month:02d}-{d:02d}"
            row[str(d)] = sched.get(nid, {}).get(date_str, "")
        rows[nurse["name"]] = row

    df = pd.DataFrame(rows).T
    df.index.name = "Asistent"
    return df


def _df_to_schedule_data(df: pd.DataFrame, original: dict, year: int, month: int) -> dict:
    """Convertește DataFrame-ul editat înapoi în formatul schedule_data."""
    updated = dict(original)
    sched = {}
    nurses = original["nurses"]

    for nurse in nurses:
        nid = str(nurse["id"])
        nname = nurse["name"]
        sched[nid] = {}
        if nname in df.index:
            for col in df.columns:
                day = int(col)
                date_str = f"{year}-{month:02d}-{day:02d}"
                sched[nid][date_str] = str(df.loc[nname, col])

    updated["schedule"] = sched
    return updated


def _export_csv(df: pd.DataFrame, year: int, month: int) -> bytes:
    """Exportă DataFrame-ul ca CSV."""
    buf = io.StringIO()
    buf.write(f"Grafic Lunar — {MONTHS_RO[month]} {year}\n")
    df.to_csv(buf)
    return buf.getvalue().encode("utf-8-sig")  # BOM pentru Excel


# ============================================================================
# VIEW ASISTENT
# ============================================================================
def _nurse_schedule_view(api):
    """Afișează graficul lunar personal al asistentei."""
    st.markdown("### Graficul meu lunar")

    user = st.session_state.get("user", {})
    dept_id = user.get("department_id")
    nurse_id = str(user.get("id", ""))

    if not dept_id:
        st.info("Nu ești asignată unui departament.")
        return

    today = date.today()
    next_month = 1 if today.month == 12 else today.month + 1
    next_year = today.year + 1 if today.month == 12 else today.year

    col_m, col_y = st.columns([2, 1])
    month = col_m.selectbox(
        "Luna",
        options=list(range(1, 13)),
        index=next_month - 1,
        format_func=lambda m: MONTHS_RO[m],
        key="nurse_month_sel",
    )
    year = col_y.number_input("Anul", min_value=2024, max_value=2030,
                               value=next_year, step=1, key="nurse_year_sel")

    try:
        saved = api.get_monthly_schedule(dept_id, int(year), month)
        sched_data = json.loads(saved["schedule_data"])
        nurse_sched = sched_data.get("schedule", {}).get(nurse_id, {})

        if not nurse_sched:
            st.info("Graficul pentru această lună nu a fost publicat încă.")
            return

        num_days = calendar.monthrange(int(year), month)[1]

        # ── Sumar ture ──────────────────────────────────────────────────────
        counts = {s: 0 for s in ["D", "A", "N", "C", "L", ""]}
        for ds, shift in nurse_sched.items():
            counts[shift] = counts.get(shift, 0) + 1

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ture Dimineață", counts["D"])
        c2.metric("Ture Amiază", counts["A"])
        c3.metric("Ture Noapte", counts["N"])
        c4.metric("Concediu / Liber", counts["C"] + counts["L"])

        # ── Calendar vizual ──────────────────────────────────────────────────
        _legend()
        st.markdown("<br>", unsafe_allow_html=True)

        # Afișare pe săptămâni: luni-duminică
        first_weekday = calendar.monthrange(int(year), month)[0]  # 0=luni
        DAY_NAMES = ["Lu", "Ma", "Mi", "Jo", "Vi", "Sâ", "Du"]

        # Header zile săptămână
        header_cols = st.columns(7)
        for i, dn in enumerate(DAY_NAMES):
            weekend = i >= 5
            header_cols[i].markdown(
                f'<div style="text-align:center;font-weight:700;'
                f'color:{"#ef4444" if weekend else "#374151"};'
                f'font-size:0.8rem;padding-bottom:4px;">{dn}</div>',
                unsafe_allow_html=True,
            )

        # Celule calendar
        day = 1
        cell_idx = first_weekday  # offset pentru prima zi
        while day <= num_days:
            cols = st.columns(7)
            for col_i in range(7):
                if cell_idx > 0 or day > num_days:
                    # celulă goală
                    cols[col_i].markdown(
                        '<div style="height:52px;"></div>', unsafe_allow_html=True
                    )
                    if cell_idx > 0:
                        cell_idx -= 1
                    elif day > num_days:
                        pass
                else:
                    ds = f"{int(year)}-{month:02d}-{day:02d}"
                    shift = nurse_sched.get(ds, "")
                    bg = SHIFT_BG.get(shift, "#f9fafb")
                    fg = SHIFT_FG.get(shift, "#9ca3af")
                    label = SHIFT_LABELS.get(shift, "")
                    weekend = col_i >= 5
                    border = "1px solid #fca5a5" if weekend else "1px solid #e5e7eb"
                    cols[col_i].markdown(
                        f'<div style="background:{bg};color:{fg};border:{border};'
                        f'border-radius:8px;padding:4px 2px;text-align:center;'
                        f'font-size:0.75rem;font-weight:700;min-height:52px;">'
                        f'<span style="font-size:0.9rem;color:#6b7280;">{day}</span><br>'
                        f'{shift if shift else "—"}<br>'
                        f'<span style="font-size:0.65rem;font-weight:400;">{label.split()[0] if label else ""}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    day += 1

        finalizat = saved.get("is_finalized", False)
        st.caption(
            f"{'✅ Grafic finalizat' if finalizat else '⏳ Grafic în lucru (poate fi modificat)'}"
        )

    except Exception as e:
        if not handle_api_exception(e):
            st.info("Graficul pentru această lună nu a fost publicat încă.")


def nurse_view(api):
    st.markdown("## Grafic Lunar — Cereri")

    # ── Sold concediu ────────────────────────────────────────────────────────
    try:
        balance = api.get_vacation_balance(year=date.today().year)
        c1, c2, c3 = st.columns(3)
        c1.metric("Zile totale / an", balance["total_days"])
        c2.metric("Zile utilizate", balance["used_days"])
        c3.metric("Zile rămase", balance["remaining_days"],
                  delta=None,
                  help="Zile de concediu disponibile pentru anul curent")
    except Exception as e:
        handle_api_exception(e)
        st.warning("Nu s-a putut încărca soldul de concediu.")

    _nurse_schedule_view(api)

    st.divider()

    # ── Formular cerere nouă ─────────────────────────────────────────────────
    with st.expander("➕ Depune cerere nouă", expanded=True):
        with st.form("form_request"):
            request_type = st.selectbox(
                "Tip cerere",
                options=["vacation", "day_off"],
                format_func=lambda x: "🌴 Concediu (scade din sold)" if x == "vacation" else "🗓️ Zi liberă",
            )

            # Luna viitoare implicit
            today = date.today()
            next_month_first = date(today.year + (1 if today.month == 12 else 0),
                                    1 if today.month == 12 else today.month + 1, 1)

            col_s, col_e = st.columns(2)
            start = col_s.date_input("Data început", value=next_month_first,
                                     min_value=today)
            end = col_e.date_input("Data sfârșit", value=next_month_first,
                                   min_value=today)
            notes = st.text_area("Observații (opțional)", height=80)

            submitted = st.form_submit_button("Trimite cererea", type="primary",
                                              use_container_width=True)
            if submitted:
                if end < start:
                    st.error("Data de sfârșit trebuie să fie după data de început.")
                else:
                    try:
                        api.create_vacation_request(
                            request_type=request_type,
                            start_date=start.isoformat(),
                            end_date=end.isoformat(),
                            notes=notes or None,
                        )
                        st.success("✅ Cererea a fost trimisă cu succes!")
                        st.rerun()
                    except Exception as e:
                        if not handle_api_exception(e):
                            try:
                                msg = e.response.json().get("detail", str(e))
                            except Exception:
                                msg = str(e)
                            st.error(f"❌ {msg}")

    st.divider()

    # ── Lista cereri proprii ─────────────────────────────────────────────────
    st.markdown("### Cererile mele")
    try:
        requests = api.get_vacation_requests()
        if not requests:
            st.info("Nu ai nicio cerere depusă.")
        else:
            STATUS_ICONS = {"pending": "⏳", "approved": "✅", "rejected": "❌"}
            STATUS_LABELS = {"pending": "În așteptare", "approved": "Aprobată", "rejected": "Respinsă"}
            TYPE_LABELS = {"vacation": "🌴 Concediu", "day_off": "🗓️ Zi liberă"}

            for req in requests:
                status_icon = STATUS_ICONS.get(req["status"], "")
                status_label = STATUS_LABELS.get(req["status"], req["status"])
                type_label = TYPE_LABELS.get(req["request_type"], req["request_type"])
                days = (date.fromisoformat(req["end_date"]) -
                        date.fromisoformat(req["start_date"])).days + 1

                bg = {"pending": "#fef3c7", "approved": "#d1fae5", "rejected": "#fee2e2"}.get(
                    req["status"], "#f3f4f6")
                border = {"pending": "#f59e0b", "approved": "#10b981", "rejected": "#ef4444"}.get(
                    req["status"], "#9ca3af")

                st.markdown(
                    f'<div style="background:{bg};border-left:4px solid {border};'
                    f'border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.6rem;">'
                    f'<b>{type_label}</b> &nbsp;·&nbsp; '
                    f'{req["start_date"]} → {req["end_date"]} ({days} {"zile" if days > 1 else "zi"})'
                    f'<br><span style="font-size:0.82rem;color:#6b7280;">'
                    f'{status_icon} {status_label}'
                    f'{(" &nbsp;·&nbsp; " + req["notes"]) if req.get("notes") else ""}'
                    f'</span></div>',
                    unsafe_allow_html=True,
                )
    except Exception as e:
        handle_api_exception(e)


# ============================================================================
# VIEW MANAGER
# ============================================================================
def manager_view(api):
    st.markdown("## Grafic Lunar — Manager")

    # ── Selectare lună și departament ────────────────────────────────────────
    today = date.today()
    next_month = 1 if today.month == 12 else today.month + 1
    next_year = today.year + 1 if today.month == 12 else today.year

    col_dept, col_month, col_year = st.columns([2, 1, 1])

    try:
        departments = api.get_departments()
        dept_map = {d["name"]: d["id"] for d in departments}
    except Exception:
        departments = []
        dept_map = {}

    if not dept_map:
        st.warning("Nu există departamente. Creează mai întâi un departament.")
        return

    dept_name = col_dept.selectbox("Departament", options=list(dept_map.keys()))
    dept_id = dept_map[dept_name]

    month = col_month.selectbox(
        "Luna",
        options=list(range(1, 13)),
        index=next_month - 1,
        format_func=lambda m: MONTHS_RO[m],
    )
    year = col_year.number_input("Anul", min_value=2024, max_value=2030,
                                  value=next_year, step=1)

    st.divider()

    # ── Cereri în așteptare ──────────────────────────────────────────────────
    with st.expander("⏳ Cereri de concediu în așteptare", expanded=False):
        _manager_requests(api, dept_id)

    st.divider()

    # ── Generare / Incarcare grafic ──────────────────────────────────────────
    col_gen, col_load = st.columns(2)

    if col_gen.button("Generează grafic", type="primary", use_container_width=True):
        with st.spinner("Generez graficul optim cu AI..."):
            try:
                result = api.generate_schedule(dept_id, int(year), month)
                st.session_state["schedule_data"] = result
                st.session_state["schedule_dept"] = dept_id
                st.session_state["schedule_year"] = int(year)
                st.session_state["schedule_month"] = month
                st.success(f"✅ Grafic generat pentru {len(result.get('nurses', []))} asistenți.")
            except Exception as e:
                if not handle_api_exception(e):
                    try:
                        msg = e.response.json().get("detail", str(e))
                    except Exception:
                        msg = str(e)
                    st.error(f"❌ {msg}")

    if col_load.button("Încarcă grafic salvat", use_container_width=True):
        try:
            saved = api.get_monthly_schedule(dept_id, int(year), month)
            loaded = json.loads(saved["schedule_data"])
            st.session_state["schedule_data"] = loaded
            st.session_state["schedule_dept"] = dept_id
            st.session_state["schedule_year"] = int(year)
            st.session_state["schedule_month"] = month
            st.success("✅ Grafic salvat încărcat.")
        except Exception as e:
            if not handle_api_exception(e):
                st.info("Nu există grafic salvat pentru această lună și departament.")

    # ── Editor grafic ────────────────────────────────────────────────────────
    sched = st.session_state.get("schedule_data")
    s_dept = st.session_state.get("schedule_dept")
    s_year = st.session_state.get("schedule_year")
    s_month = st.session_state.get("schedule_month")

    if sched and s_dept == dept_id and s_year == int(year) and s_month == month:
        nurses = sched.get("nurses", [])
        if not nurses:
            st.warning("Nu există asistenți înregistrați în acest departament.")
            return

        month_name = MONTHS_RO[month]
        st.markdown(f"### {month_name} {int(year)} — {dept_name}")

        _legend()
        st.markdown("<br>", unsafe_allow_html=True)

        _show_schedule_stats(sched, int(year), month)
        st.markdown("<br>", unsafe_allow_html=True)

        # ── Grafic colorat (read-only) ───────────────────────────────────────
        df = _build_dataframe(sched, int(year), month)
        st.dataframe(
            _styled_dataframe(df),
            use_container_width=True,
            height=min(80 + len(nurses) * 36, 600),
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Editor + salvare ─────────────────────────────────────────────────
        num_days = calendar.monthrange(int(year), month)[1]
        col_config = {
            str(d): st.column_config.SelectboxColumn(
                label=str(d),
                options=["D", "A", "N", "C", "M", "L"],
                width="small",
            )
            for d in range(1, num_days + 1)
        }

        with st.expander("Editează graficul", expanded=False):
            st.caption("Dublu-click pe o celulă pentru a schimba tura. Salvează după modificări.")
            edited_df = st.data_editor(
                df.copy(),
                column_config=col_config,
                use_container_width=True,
                num_rows="fixed",
                key=f"sched_editor_{dept_id}_{year}_{month}",
            )

            col_save, col_final = st.columns(2)

            if col_save.button("Salvează", use_container_width=True):
                updated = _df_to_schedule_data(edited_df, sched, int(year), month)
                try:
                    api.save_schedule(
                        department_id=dept_id,
                        year=int(year),
                        month=month,
                        schedule_data=json.dumps(updated),
                        is_finalized=False,
                    )
                    st.session_state["schedule_data"] = updated
                    st.success("✅ Grafic salvat!")
                    st.rerun()
                except Exception as e:
                    if not handle_api_exception(e):
                        st.error(f"❌ {e}")

            if col_final.button("Finalizează & Salvează", use_container_width=True, type="primary"):
                updated = _df_to_schedule_data(edited_df, sched, int(year), month)
                try:
                    api.save_schedule(
                        department_id=dept_id,
                        year=int(year),
                        month=month,
                        schedule_data=json.dumps(updated),
                        is_finalized=True,
                    )
                    st.session_state["schedule_data"] = updated
                    st.success("✅ Grafic finalizat!")
                    st.rerun()
                except Exception as e:
                    if not handle_api_exception(e):
                        st.error(f"❌ {e}")

        # ── Export CSV ───────────────────────────────────────────────────────
        csv_bytes = _export_csv(df, int(year), month)
        st.download_button(
            label="Export CSV",
            data=csv_bytes,
            file_name=f"grafic_{dept_name}_{MONTHS_RO[month]}_{int(year)}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.divider()

        # ── Publică ──────────────────────────────────────────────────────────
        is_finalized = st.session_state.get("schedule_data", {}).get("is_finalized", False)
        if is_finalized:
            st.success("✅ Graficul este deja publicat — asistentele îl pot vedea.")
        else:
            st.info("Graficul nu este publicat încă. Asistentele nu îl pot vedea.")

        if st.button(
            "Publică graficul" if not is_finalized else "Re-publică graficul",
            type="primary",
            use_container_width=True,
            key="btn_publish",
        ):
            try:
                api.save_schedule(
                    department_id=dept_id,
                    year=int(year),
                    month=month,
                    schedule_data=json.dumps(sched),
                    is_finalized=True,
                )
                updated = dict(sched)
                updated["is_finalized"] = True
                st.session_state["schedule_data"] = updated
                st.success(f"✅ Grafic publicat! Asistentele din {dept_name} îl pot vedea acum.")
                st.rerun()
            except Exception as e:
                if not handle_api_exception(e):
                    st.error(f"❌ {e}")


def _show_schedule_stats(sched: dict, year: int, month: int):
    """Afișează statistici sumare pentru graficul generat."""
    schedule = sched.get("schedule", {})
    nurses = sched.get("nurses", [])
    targets = sched.get("targets", {})
    num_days = calendar.monthrange(year, month)[1]

    total_d = total_a = total_n = total_c = total_l = 0
    nurse_totals = {}
    nurse_nights = {}

    for nurse in nurses:
        nid = str(nurse["id"])
        counts = {"D": 0, "A": 0, "N": 0, "C": 0, "L": 0, "": 0}
        for day in range(1, num_days + 1):
            ds = f"{year}-{month:02d}-{day:02d}"
            v = schedule.get(nid, {}).get(ds, "")
            counts[v] = counts.get(v, 0) + 1
        total_d += counts["D"]
        total_a += counts["A"]
        total_n += counts["N"]
        total_c += counts["C"]
        total_l += counts["L"]
        nurse_totals[nurse["name"]] = counts["D"] + counts["A"] + counts["N"]
        nurse_nights[nurse["name"]] = counts["N"]

    # Target staffing per tură (din profilul departamentului)
    if targets:
        st.markdown(
            f'<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;'
            f'padding:0.6rem 1rem;margin-bottom:0.8rem;font-size:0.85rem;">'
            f'🎯 <b>Target staffing per zi:</b> &nbsp;'
            f'<span style="color:#1d4ed8;">⬛ {targets.get("D", "?")} Dimineață</span> &nbsp;·&nbsp; '
            f'<span style="color:#b45309;">⬛ {targets.get("A", "?")} Amiază</span> &nbsp;·&nbsp; '
            f'<span style="color:#6d28d9;">⬛ {targets.get("N", "?")} Noapte</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ture Dimineață", total_d)
    c2.metric("Ture Amiază", total_a)
    c3.metric("Ture Noapte", total_n)
    c4.metric("Concedii + Libere", total_c + total_l)

    # Distribuție per asistent
    if nurse_totals:
        avg = sum(nurse_totals.values()) / len(nurse_totals)
        min_n = min(nurse_totals.values())
        max_n = max(nurse_totals.values())
        avg_nights = sum(nurse_nights.values()) / len(nurse_nights) if nurse_nights else 0
        max_nights = max(nurse_nights.values()) if nurse_nights else 0
        min_nights = min(nurse_nights.values()) if nurse_nights else 0

        echilibru_ture = max_n - min_n <= 3
        echilibru_nopti = max_nights - min_nights <= 2

        st.caption(
            f"Ture per asistent: medie **{avg:.1f}** · min **{min_n}** · max **{max_n}** "
            f"({'✅ echilibrat' if echilibru_ture else '⚠️ dezechilibrat'})  \n"
            f"Nopți per asistent: medie **{avg_nights:.1f}** · min **{min_nights}** · max **{max_nights}** "
            f"({'✅ echilibrat' if echilibru_nopti else '⚠️ dezechilibrat'})"
        )


def _manager_requests(api, dept_id: int):
    """Afișează cererile în așteptare pentru manager."""
    try:
        requests = api.get_vacation_requests(department_id=dept_id)
        pending = [r for r in requests if r["status"] == "pending"]
        if not pending:
            st.info("Nu există cereri în așteptare.")
            return

        for req in pending:
            days = (date.fromisoformat(req["end_date"]) -
                    date.fromisoformat(req["start_date"])).days + 1
            type_label = "🌴 Concediu" if req["request_type"] == "vacation" else "🗓️ Zi liberă"

            col_info, col_app, col_rej = st.columns([4, 1, 1])
            col_info.markdown(
                f"**{req.get('nurse_name', 'N/A')}** — {type_label}  \n"
                f"📅 {req['start_date']} → {req['end_date']} ({days} {'zile' if days > 1 else 'zi'})"
                + (f"  \n_{req['notes']}_" if req.get("notes") else "")
            )
            if col_app.button("✅", key=f"app_{req['id']}", help="Aprobă", use_container_width=True):
                try:
                    api.review_vacation_request(req["id"], "approved")
                    st.rerun()
                except Exception as e:
                    handle_api_exception(e)
            if col_rej.button("❌", key=f"rej_{req['id']}", help="Respinge", use_container_width=True):
                try:
                    api.review_vacation_request(req["id"], "rejected")
                    st.rerun()
                except Exception as e:
                    handle_api_exception(e)
            st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)

    except Exception as e:
        handle_api_exception(e)


# ============================================================================
# Entry point
# ============================================================================
api = st.session_state.api_client
role = get_user_role()

if role == "nurse":
    nurse_view(api)
elif role == "manager":
    manager_view(api)
