import streamlit as st
import pandas as pd
import io

# ---------------- Feature Entry Point ----------------
def prioritization_board_app():
    st.header("🗂️ Prioritization Board")

    # ---------------- Initialize state ----------------
    if "cards" not in st.session_state:
        st.session_state.cards = {
            "in_process": [],
            "complete": []
        }

    # ---------------- Add Card ----------------
    st.subheader("➕ Add New Card")

    with st.form("add_card_form", clear_on_submit=True):
        client_name = st.text_input("Client Name")
        section = st.selectbox("Section", ["In Process", "Complete"])
        submitted = st.form_submit_button("Add")

        if submitted:
            name = client_name.strip()
            if not name:
                st.warning("Client name cannot be empty.")
            else:
                key = "in_process" if section == "In Process" else "complete"
                st.session_state.cards[key].append(name)
                st.success(f"Added '{name}' to {section}")

    st.divider()

    # ---------------- Board Layout ----------------
    col1, col2 = st.columns(2)

    # ================= IN PROCESS =================
    with col1:
        st.subheader("🔄 In Process (Priority Order)")

        cards = st.session_state.cards["in_process"]

        if not cards:
            st.caption("No cards in process")
        else:
            for idx, client in enumerate(cards):
                priority = idx + 1

                c1, c2, c3, c4, c5 = st.columns([4, 1, 1, 1, 1])

                with c1:
                    st.markdown(f"**{priority}. {client}**")

                # Move Up
                with c2:
                    if idx > 0:
                        if st.button("⬆️", key=f"up_{idx}"):
                            cards[idx - 1], cards[idx] = cards[idx], cards[idx - 1]
                            st.rerun()

                # Move Down
                with c3:
                    if idx < len(cards) - 1:
                        if st.button("⬇️", key=f"down_{idx}"):
                            cards[idx + 1], cards[idx] = cards[idx], cards[idx + 1]
                            st.rerun()

                # Move to Complete
                with c4:
                    if st.button("✅", key=f"to_done_{idx}"):
                        st.session_state.cards["complete"].append(client)
                        cards.pop(idx)
                        st.rerun()

                # Remove
                with c5:
                    if st.button("❌", key=f"remove_ip_{idx}"):
                        cards.pop(idx)
                        st.rerun()

    # ================= COMPLETE =================
    with col2:
        st.subheader("✅ Complete")

        done_cards = st.session_state.cards["complete"]

        if not done_cards:
            st.caption("No completed cards")
        else:
            for idx, client in enumerate(done_cards):
                c1, c2, c3 = st.columns([5, 1, 1])

                with c1:
                    st.markdown(f"**{client}**")

                # Move back to In Process (bottom priority)
                with c2:
                    if st.button("🔄", key=f"to_ip_{idx}"):
                        st.session_state.cards["in_process"].append(client)
                        done_cards.pop(idx)
                        st.rerun()

                # Remove
                with c3:
                    if st.button("❌", key=f"remove_done_{idx}"):
                        done_cards.pop(idx)
                        st.rerun()

    st.divider()

    # ---------------- Export to Excel ----------------
    st.subheader("📤 Export Board to Excel")

    rows = []

    for i, client in enumerate(st.session_state.cards["in_process"], start=1):
        rows.append({
            "Client": client,
            "Status": "In Process",
            "Priority": i
        })

    for client in st.session_state.cards["complete"]:
        rows.append({
            "Client": client,
            "Status": "Complete",
            "Priority": ""
        })

    export_df = pd.DataFrame(rows)

    buffer = io.BytesIO()
    export_df.to_excel(buffer, index=False, engine="openpyxl")
    buffer.seek(0)

    st.download_button(
        label="📥 Download Excel",
        data=buffer,
        file_name="prioritization_board.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
