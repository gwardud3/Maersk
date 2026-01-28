import streamlit as st

# ---------------- Feature Entry Point ----------------
def prioritization_board_app():
    st.header("🗂️ Prioritization Board")

    # ---------------- Initialize state ----------------
    if "cards" not in st.session_state:
        st.session_state.cards = {
            "in_process": [],
            "complete": []
        }

    # ---------------- Add new card ----------------
    st.subheader("➕ Add New Card")

    with st.form("add_card_form", clear_on_submit=True):
        client_name = st.text_input("Client Name")
        section = st.selectbox(
            "Section",
            options=["In Process", "Complete"]
        )
        submitted = st.form_submit_button("Add")

        if submitted and client_name.strip():
            key = "in_process" if section == "In Process" else "complete"
            st.session_state.cards[key].append(client_name.strip())
            st.success(f"Added '{client_name}' to {section}")

    st.divider()

    # ---------------- Display Board ----------------
    col1, col2 = st.columns(2)

    # -------- In Process --------
    with col1:
        st.subheader("🔄 In Process")

        if not st.session_state.cards["in_process"]:
            st.caption("No cards in process")
        else:
            for idx, client in enumerate(st.session_state.cards["in_process"], start=1):
                c1, c2 = st.columns([5, 1])

                with c1:
                    st.markdown(f"**{idx}. {client}**")

                with c2:
                    if st.button("❌", key=f"remove_ip_{idx}"):
                        st.session_state.cards["in_process"].pop(idx - 1)
                        st.rerun()

    # -------- Complete --------
    with col2:
        st.subheader("✅ Complete")

        if not st.session_state.cards["complete"]:
            st.caption("No completed cards")
        else:
            for idx, client in enumerate(st.session_state.cards["complete"]):
                c1, c2 = st.columns([5, 1])

                with c1:
                    st.markdown(f"**{client}**")

                with c2:
                    if st.button("❌", key=f"remove_done_{idx}"):
                        st.session_state.cards["complete"].pop(idx)
                        st.rerun()
