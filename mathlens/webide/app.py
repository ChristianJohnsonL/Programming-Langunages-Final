import base64
import requests
import streamlit as st
from components import render_corrections, render_steps, render_answer, render_ast_graph, render_error

st.set_page_config(page_title="!photoMath IDE", layout="wide", page_icon="🔢")

API_URL = st.sidebar.text_input("Backend URL", value="http://localhost:8080")

if "last_result" not in st.session_state:
    st.session_state.last_result = None


def call_solve(endpoint: str, payload: dict):
    try:
        r = requests.post(f"{API_URL}/solve/{endpoint}", json=payload, timeout=15)
        return r.json()
    except Exception as e:
        st.error(f"Backend error: {e}")
        return None


def render_result(result: dict) -> None:
    if not result:
        return
    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("### Input")
        st.code(result.get("raw_input", ""), language=None)
        st.markdown("**Normalised:**")
        st.code(result.get("normalized", ""), language=None)
        render_corrections(result.get("corrections", []))
        st.markdown("### Parse Tree")
        ast = result.get("ast")
        if ast and "error" not in ast:
            render_ast_graph(ast)
        elif ast:
            render_error(ast)
        with st.expander("Raw AST JSON"):
            st.json(ast)
    with col_right:
        st.markdown("### Solution Steps")
        solution = result.get("solution")
        error = result.get("error")
        if error:
            render_error(error)
        elif solution:
            render_steps(solution.get("steps", []))
            st.markdown("### Answer")
            render_answer(solution.get("result", ""))


st.title("!photoMath IDE")

tab_type, tab_image = st.tabs(["⌨️ Type", "📷 Upload Image"])

with tab_type:
    text_input = st.text_area("Enter math expression", placeholder="factor x^2 + 5x + 6", height=80)
    if st.button("Solve"):
        if text_input.strip():
            with st.spinner("Solving…"):
                st.session_state.last_result = call_solve("text", {"text": text_input.strip()})

with tab_image:
    uploaded = st.file_uploader("Upload a photo of your math problem", type=["png", "jpg", "jpeg"])
    if uploaded and st.button("Solve Image"):
        b64 = base64.b64encode(uploaded.read()).decode()
        with st.spinner("Running OCR…"):
            st.session_state.last_result = call_solve("image", {"image": b64})

st.markdown("---")
render_result(st.session_state.last_result)
