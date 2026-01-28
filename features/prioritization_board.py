import streamlit as st
import pandas as pd
import io
import json
import os

# ---------------- Persistence ----------------
DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "prioritization_board.json")

def empty_board():
    return {"in_process": [], "complete": []}

def new_card(name):
    return {
        "client": name,
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

def normalize_board(cards):
    """
    Migrate legacy string-based cards to dict-based cards.
    """
    for section in ["in_process", "complete"]:
        normalized = []
        for item in cards.get(section, []):
            if isinstance(item, str):
                normalized.append(new_card(item))
            elif isinstance(item, dict):
                normalized.append(item)
        cards[section] = normalized
    return cards

def save_board(cards):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(cards, f, indent=2)

# ---------------- Feature Entry Point ----------------
def prioritization_board_app():
    st.header("🗂️ Prioritization Board")

    # ---------------- Initialize state ----------------
    loaded = load_board()

    # Always normalize (handles legacy session_state + file)
    normalized = normalize_board(loaded)

    st.session_state.cards = normalized
    save_board(st.session_state.cards)


    cards_ip = st.session_state.cards["in_process"]
    cards_done = st.session_state.cards["complete"]

    col1, col2 = st.columns(2)

    # ================= IN PROCESS =================
    with col1:
        st.subheader("🔄 In Process")

        if not cards_ip:
            st.caption("No cards in process")
        else:
            for idx, card in enumerate(cards_ip):
                priority = idx + 1

                with st.container(border=True):
                    c1, c2, c3, c4, c5 = st.columns([4, 1, 1, 1, 1])

                    with c1:
                        with st.expander(f"**{priority}. {card['client']}**"):
                            card["annual_rev"] = st.text_input(
                                "Annual Revenue",
                                card["annual_rev"],
                                key=f"rev_ip_{idx}"
                            )
                            card["annual_spend"] = st.text_input(
                                "Annual Spend",
                                card["annual_spend"],
                                key=f"spend_ip_{idx}"
                            )
                            card["notes"] = st.text_area(
                                "Notes",
                                card["notes"],
                                key=f"notes_ip_{idx}"
                            )
                            save_board(st.session_state.cards)

                    with c2:
                        if idx > 0 and st.button("⬆️", key=f"up_{idx}", use_container_width=True):
                            cards_ip[idx - 1], cards_ip[idx] = cards_ip[idx], cards_ip[idx - 1]
                            save_board(st.session_state.cards)
                            st.rerun()

                    with c3:
                        if idx < len(cards_ip) - 1 and st.button("⬇️", key=f"down_{idx}", use_container_width=True):
                            cards_ip[idx + 1], cards_ip[idx] = cards_ip[idx], cards_ip[idx + 1]
                            save_board(st.session_state.cards)
                            st.rerun()

                    with c4:
                        if st.button("✅", key=f"to_done_{idx}", use_container_width=True):
                            cards_done.append(card)
                            cards_ip.pop(idx)
                            save_board(st.session_state.cards)
                            st.rerun()

                    with c5:
                        if st.button("🗑️", key=f"remove_ip_{idx}", use_container_width=True):
                            cards_ip.pop(idx)
                            save_board(st.session_state.cards)
                            st.rerun()

    # ================= COMPLETE =================
    with col2:
        st.subheader("✅ Complete")

        if not cards_done:
            st.caption("No completed cards")
        else:
            for idx, card in enumerate(cards_done):
                with st.container(border=True):
                    c1, c2, c3 = st.columns([5, 1, 1])

                    with c1:
                        with st.expander(card["client"]):
                            card["annual_rev"] = st.text_input(
                                "Annual Revenue",
                                card["annual_rev"],
                                key=f"rev_done_{idx}"
                            )
                            card["annual_spend"] = st.text_input(
                                "Annual Spend",
                                card["annual_spend"],
                                key=f"spend_done_{idx}"
                            )
                            card["notes"] = st.text_area(
                                "Notes",
                                card["notes"],
                                key=f"notes_done_{idx}"
                            )
                            save_board(st.session_state.cards)

                    with c2:
                        if st.button("🔄", key=f"to_ip_{idx}", use_container_width=True):
                            cards_ip.append(card)
                            cards_done.pop(idx)
                            save_board(st.session_state.cards)
                            st.rerun()

                    with c3:
                        if st.button("🗑️", key=f"remove_done_{idx}", use_container_width=True):
                            cards_done.pop(idx)
                            save_board(st.session_state.cards)
                            st.rerun()

        if cards_done and st.button("🧹 Clear Complete"):
            st.session_state.cards["complete"] = []
            save_board(st.session_state.cards)
            st.rerun()

    st.divider()

    # ---------------- Add Card ----------------
    st.subheader("➕ Add New Card")

    with st.form("add_card_form", clear_on_submit=True):
        c1, c2, c3 = st.columns([3, 2, 1])

        with c1:
            client_name = st.text_input("Client Name")

        with c2:
            priority_input = st.text_input(
                "Priority (number or C)",
                help="Number = In Process priority, C = Complete"
            )

        with c3:
            submitted = st.form_submit_button("Add")

        if submitted:
            name = client_name.strip()
            p = priority_input.strip().lower()

            if not name:
                st.warning("Client name cannot be empty.")
            elif p == "c":
                cards_done.append(new_card(name))
                save_board(st.session_state.cards)
                st.success(f"Added '{name}' to Complete")
            elif p.isdigit():
                pos = max(0, min(int(p) - 1, len(cards_ip)))
                cards_ip.insert(pos, new_card(name))
                save_board(st.session_state.cards)
                st.success(f"Added '{name}' at priority {pos + 1}")
            else:
                cards_ip.append(new_card(name))
                save_board(st.session_state.cards)
                st.success(f"Added '{name}' to In Process")

    st.divider()

    # ---------------- Export to Excel ----------------
    rows = []

    for i, card in enumerate(cards_ip, start=1):
        rows.append({
            "Client": card["client"],
            "Status": "In Process",
            "Priority": i,
            "Annual Revenue": card["annual_rev"],
            "Annual Spend": card["annual_spend"],
            "Notes": card["notes"]
        })

    for card in cards_done:
        rows.append({
            "Client": card["client"],
            "Status": "Complete",
            "Priority": "",
            "Annual Revenue": card["annual_rev"],
            "Annual Spend": card["annual_spend"],
            "Notes": card["notes"]
        })

    df = pd.DataFrame(rows)

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)

    st.download_button(
        "📥 Download Excel",
        data=buffer,
        file_name="prioritization_board.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
