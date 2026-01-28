import streamlit as st
import pandas as pd
import io
import json
import os

# =====================================================
# Persistence (anchored to repo root)
# =====================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "prioritization_board.json")


def empty_board():
    return {"in_process": [], "complete": []}


def new_card(client):
    return {
        "client": client,
        "annual_rev": "",
        "annual_spend": "",
        "notes": ""
    }


def load_board():
    if not os.path.exists(DATA_FILE):
        return empty_board()
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return empty_board()


def save_board(cards):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(cards, f, indent=2)


def normalize_board(cards):
    for section in ["in_process", "complete"]:
        normalized = []
        for item in cards.get(section, []):
            if isinstance(item, str):
                normalized.append(new_card(item))
            elif isinstance(item, dict):
                normalized.append(item)
        cards[section] = normalized
    return cards


# =====================================================
# Excel Import Helper
# =====================================================
def import_from_excel(df):
    required_cols = {
        "Client", "Status", "Priority",
        "Annual Revenue", "Annual Spend", "Notes"
    }

    if not required_cols.issubset(df.columns):
        raise ValueError("Excel file does not match expected export format.")

    cards = {"in_process": [], "complete": []}

    ip_df = df[df["Status"] == "In Process"].copy()
    ip_df["Priority"] = pd.to_numeric(ip_df["Priority"], errors="coerce")
    ip_df = ip_df.sort_values("Priority")

    for _, r in ip_df.iterrows():
        cards["in_process"].append({
            "client": str(r["Client"]),
            "annual_rev": str(r["Annual Revenue"] or ""),
            "annual_spend": str(r["Annual Spend"] or ""),
            "notes": str(r["Notes"] or "")
        })

    done_df = df[df["Status"] == "Complete"]
    for _, r in done_df.iterrows():
        cards["complete"].append({
            "client": str(r["Client"]),
            "annual_rev": str(r["Annual Revenue"] or ""),
            "annual_spend": str(r["Annual Spend"] or ""),
            "notes": str(r["Notes"] or "")
        })

    return cards


# =====================================================
# Feature Entry Point
# =====================================================
def prioritization_board_app():
    st.header("🗂️ Prioritization Board")

    # ---- Load once, never save on load ----
    if "cards" not in st.session_state:
        st.session_state.cards = normalize_board(load_board())

    cards_ip = st.session_state.cards["in_process"]
    cards_done = st.session_state.cards["complete"]

    col1, col2 = st.columns(2)

    # ===================== IN PROCESS =====================
    with col1:
        st.subheader("In Process")

        if not cards_ip:
            st.caption("No items in process")
        else:
            for idx, card in enumerate(cards_ip):
                priority = idx + 1

                with st.container(border=True):
                    pcol, main, actions = st.columns([1, 5, 1])

                    with pcol:
                        st.markdown(
                            f"<div style='font-size:22px; font-weight:700; text-align:center;'>{priority}</div>",
                            unsafe_allow_html=True
                        )

                    with main:
                        with st.expander(card["client"]):
                            card["annual_rev"] = st.text_input(
                                "Annual Revenue", card["annual_rev"], key=f"rev_ip_{idx}"
                            )
                            card["annual_spend"] = st.text_input(
                                "Annual Spend", card["annual_spend"], key=f"spend_ip_{idx}"
                            )
                            card["notes"] = st.text_area(
                                "Notes", card["notes"], key=f"notes_ip_{idx}"
                            )
                            save_board(st.session_state.cards)

                    with actions:
                        with st.popover("⋮"):
                            new_pos = st.number_input(
                                "Set position",
                                min_value=1,
                                max_value=len(cards_ip),
                                value=priority,
                                step=1,
                                key=f"pos_{idx}"
                            )

                            if st.button("Apply", key=f"apply_{idx}"):
                                cards_ip.pop(idx)
                                cards_ip.insert(new_pos - 1, card)
                                save_board(st.session_state.cards)
                                st.rerun()

                            st.divider()

                            if st.button("Mark Complete", key=f"done_{idx}"):
                                cards_done.append(card)
                                cards_ip.pop(idx)
                                save_board(st.session_state.cards)
                                st.rerun()

                            if st.button("Delete", key=f"del_{idx}"):
                                cards_ip.pop(idx)
                                save_board(st.session_state.cards)
                                st.rerun()

    # ===================== COMPLETE =====================
    with col2:
        st.subheader("Complete")

        if not cards_done:
            st.caption("No completed items")
        else:
            for idx, card in enumerate(cards_done):
                with st.container(border=True):
                    main, actions = st.columns([6, 1])

                    with main:
                        with st.expander(card["client"]):
                            card["annual_rev"] = st.text_input(
                                "Annual Revenue", card["annual_rev"], key=f"rev_done_{idx}"
                            )
                            card["annual_spend"] = st.text_input(
                                "Annual Spend", card["annual_spend"], key=f"spend_done_{idx}"
                            )
                            card["notes"] = st.text_area(
                                "Notes", card["notes"], key=f"notes_done_{idx}"
                            )
                            save_board(st.session_state.cards)

                    with actions:
                        with st.popover("⋮"):
                            if st.button("Move Back", key=f"back_{idx}"):
                                cards_ip.append(card)
                                cards_done.pop(idx)
                                save_board(st.session_state.cards)
                                st.rerun()

                            if st.button("Delete", key=f"del_done_{idx}"):
                                cards_done.pop(idx)
                                save_board(st.session_state.cards)
                                st.rerun()

        if cards_done:
            if st.button("Clear Complete"):
                st.session_state.cards["complete"] = []
                save_board(st.session_state.cards)
                st.rerun()

    # ===================== ADD CARD =====================
    st.divider()
    st.subheader("Add New Item")

    with st.form("add_card", clear_on_submit=True):
        c1, c2, c3 = st.columns([3, 2, 1])

        with c1:
            name = st.text_input("Client name")

        with c2:
            priority_input = st.text_input(
                "Priority (number or C)",
                help="Number = position in In Process, C = Complete"
            )

        with c3:
            submitted = st.form_submit_button("Add")

        if submitted:
            name = name.strip()
            p = priority_input.strip().lower()

            if not name:
                st.warning("Client name required.")
            elif p == "c":
                cards_done.append(new_card(name))
            elif p.isdigit():
                pos = max(0, min(int(p) - 1, len(cards_ip)))
                cards_ip.insert(pos, new_card(name))
            else:
                cards_ip.append(new_card(name))

            save_board(st.session_state.cards)
            st.rerun()

    # ===================== IMPORT / EXPORT =====================
    st.divider()
    st.subheader("Import / Export")

    uploaded = st.file_uploader(
        "Restore board from exported Excel",
        type=["xlsx"]
    )

    if uploaded:
        try:
            df_import = pd.read_excel(uploaded)
            if st.button("Restore from Excel"):
                st.session_state.cards = import_from_excel(df_import)
                save_board(st.session_state.cards)
                st.success("Board restored successfully.")
                st.rerun()
        except Exception as e:
            st.error(str(e))

    # ---- Export (always visible) ----
    rows = []

    for i, c in enumerate(cards_ip, start=1):
        rows.append({
            "Client": c["client"],
            "Status": "In Process",
            "Priority": i,
            "Annual Revenue": c["annual_rev"],
            "Annual Spend": c["annual_spend"],
            "Notes": c["notes"]
        })

    for c in cards_done:
        rows.append({
            "Client": c["client"],
            "Status": "Complete",
            "Priority": "",
            "Annual Revenue": c["annual_rev"],
            "Annual Spend": c["annual_spend"],
            "Notes": c["notes"]
        })

    df_export = pd.DataFrame(rows)
    buffer = io.BytesIO()
    df_export.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        "Download Excel Backup",
        data=buffer,
        file_name="prioritization_board.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
