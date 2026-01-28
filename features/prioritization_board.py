import streamlit as st
import pandas as pd
import io
from streamlit_sortables import sortables

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

        if submitted and client_name.strip():
            key = "in_process" if section == "In Process" else "complete"
            st.session_state.cards[key].append(client_name.strip())
            st.success(f"Added '{client_name}' to {section}")

    st.divider()

    # ---------------- Board Layout ----------------
    col1, col2 = st.columns(2)

    # ================= IN PROCESS =================
    with col1:
        st.subheader("🔄 In Process (Drag to Reorder)")

        if not st.session_state.cards["in_process"]:
            st.caption("No cards in process")
        else:
            # Drag-and-drop sortable list
            new_order = sortables(
                st.session_state.cards["in_process"],
                direction="vertical",
                key="in_process_sortable"
            )

            # Persist new order
            st.session_state.cards["in_process"] = new_order

            # Display with priority + remove buttons
            for idx, client in enumerate(new_order, start=1):
                c1, c2 = st.columns([6, 1])
                with c1:
                    st.markdown(f"**{idx}. {client}**")
                with c2:
                    if st.button("❌", key=f"remove_ip_{idx}"):
                        st.session_state.cards["in_process"].remove(client)
                        st.rerun()

    # ================= COMPLETE =================
    with col2:
        st.subheader("✅ Complete")

        if not st.session_state.cards["complete"]:
            st.caption("No completed cards")
        else:
            for idx, client in enumerate(st.session_state.cards["complete"]):
                c1, c2 = st.columns([6, 1])
                with c1:
                    st.markdown(f"**{client}**")
                with c2:
                    if st.button("❌", key=f"remove_done_{idx}"):
                        st.session_state.cards["complete"].pop(idx)
                        st.rerun()

    st.divider()

    # ---------------- Export to Excel ----------------
    st.subheader("📤 Export Board")

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

