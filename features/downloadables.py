import streamlit as st

def downloadables():
    st.header("Important Files from the Pricing Team")

    with open("assets/DAS-EDAS-2026LIST.xlsx", "rb") as f:
        st.download_button(
            label="Download Excel File",
            data=f,
            file_name="DAS-EDAS-2026LIST.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )