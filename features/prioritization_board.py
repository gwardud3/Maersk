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

    # ---------------- Board Layout ----------------
    col1, col2 = st.columns(2)

    # ================= IN PROCESS =================
    with col1:
        st.subheader("🔄 In Process")

        cards = st.session_state.cards["in_process"]

        if not cards:
            st.caption("No cards in process")
        else:
            for idx, client in enumerate(cards):
                priority = idx + 1

                with st.container(border=True):
                    c1, c2, c3, c4, c5 = st.columns([4, 1, 1, 1, 1])

                    with c1:
                        st.markdown(f"**{priority}. {client}**")

                    with c2:
                        if idx > 0:
                            if st.button("⬆️", key=f"up_{idx}", help="Move up", use_container_width=True):
                                cards[idx - 1], cards[idx] = cards[idx], cards[idx - 1]
                                st.rerun()

                    with c3:
                        if idx < len(cards) - 1:
                            if st.button("⬇️", key=f"down_{idx}", help="Move down", use_container_width=True):
                                cards[idx + 1], cards[idx] = cards[idx], cards[idx + 1]
                                st.rerun()

                    with c4:
                        if st.button("✅", key=f"to_done_{idx}", help="Mark complete", use_container_width=True):
                            st.session_state.cards["complete"].append(client)
                            cards.pop(idx)
                            st.rerun()

                    with c5:
                        if st.button("🗑️", key=f"remove_ip_{idx}", help="Remove", use_container_width=True):
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
                with st.container(border=True):
                    c1, c2, c3 = st.columns([5, 1, 1])

                    with c1:
                        st.markdown(f"**{client}**")

                    with c2:
                        if st.button("🔄", key=f"to_ip_{idx}", help="Move back to In Process", use_container_width=True):
                            st.session_state.cards["in_process"].append(client)
                            done_cards.pop(idx)
                            st.rerun()

                    with c3:
                        if st.button("🗑️", key=f"remove_done_{idx}", help="Remove", use_container_width=True):
                            done_cards.pop(idx)
                            st.rerun()

        # -------- Clear Complete --------
        if done_cards:
            if st.button("🧹 Clear Complete", help="Remove all completed cards"):
                st.session_state.cards["complete"] = []
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
                help="Enter a number for In Process priority, or 'C' to mark complete"
            )

        with c3:
            submitted = st.form_submit_button("Add")

        if submitted:
            name = client_name.strip()

            if not name:
                st.warning("Client name cannot be empty.")
            else:
                priority_val = priority_input.strip()

                # ---- Complete ----
                if priority_val.lower() == "c":
                    st.session_state.cards["complete"].append(name)
                    st.success(f"Added '{name}' to Complete")

                # ---- In Process with priority ----
                elif priority_val.isdigit():
                    position = int(priority_val) - 1
                    cards = st.session_state.cards["in_process"]

                    # Clamp position
                    position = max(0, min(position, len(cards)))
                    cards.insert(position, name)

                    st.success(f"Added '{name}' to In Process at priority {position + 1}")

                # ---- Default: bottom of In Process ----
                else:
                    st.session_state.cards["in_process"].append(name)
                    st.success(f"Added '{name}' to In Process")

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

