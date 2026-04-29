import json
import streamlit as st
from typing import Optional


def render_corrections(corrections: list[str]) -> None:
    if not corrections:
        return
    with st.container():
        st.markdown("**Normaliser corrections:**")
        for c in corrections:
            st.markdown(f"<span style='background:#3a3000;padding:2px 6px;border-radius:4px;color:#f0c040'>{c}</span>", unsafe_allow_html=True)


def render_steps(steps: list[dict]) -> None:
    if not steps:
        st.info("No steps returned.")
        return
    for s in steps:
        with st.container():
            st.markdown(
                f"<div style='border-left:3px solid #7c6af7;padding:8px 12px;"
                f"margin:6px 0;background:#1a1a2e;border-radius:4px'>"
                f"<b style='color:#7c6af7'>Step {s['step']}</b><br/>"
                f"<span style='color:#e0e0e0'>{s['description']}</span></div>",
                unsafe_allow_html=True,
            )


def render_answer(result_str: str) -> None:
    st.markdown(
        f"<div style='text-align:center;font-size:28px;font-weight:bold;"
        f"color:#7c6af7;background:#1a1a2e;padding:20px;border-radius:10px;"
        f"border:1px solid #7c6af7;margin-top:10px'>{result_str}</div>",
        unsafe_allow_html=True,
    )


def render_ast_graph(ast: dict) -> None:
    """Render AST as a graphviz digraph in Streamlit."""
    try:
        import graphviz
        dot = graphviz.Digraph(graph_attr={"bgcolor": "#0f0f1a"})
        dot.attr("node", style="filled", fillcolor="#1e1e30", fontcolor="#e0e0e0", color="#7c6af7")
        dot.attr("edge", color="#666")
        _build_dot(dot, ast, "root")
        st.graphviz_chart(dot.source)
    except ImportError:
        # Fallback: raw JSON in expander
        with st.expander("AST JSON"):
            st.json(ast)


_node_counter = 0


def _build_dot(dot, node: dict, parent_id: str) -> None:
    global _node_counter
    _node_counter += 1
    node_id = f"n{_node_counter}"

    t = node.get("type", "?")
    if t == "Number":
        label = str(node["value"])
    elif t == "Variable":
        label = node["name"]
    elif t == "BinOp":
        label = node["op"]
    elif t == "UnaryMinus":
        label = "−"
    elif t == "Power":
        label = "^"
    elif t == "Equation":
        label = "="
    elif t == "Factor":
        label = "factor"
    elif t == "Solve":
        label = "solve"
    else:
        label = t

    dot.node(node_id, label=f"{t}\\n{label}")
    if parent_id != node_id:
        dot.edge(parent_id, node_id)

    for key in ("expr", "left", "right", "operand", "base", "exp"):
        if key in node and isinstance(node[key], dict):
            _build_dot(dot, node[key], node_id)

    if "equations" in node:
        for eq in node["equations"]:
            _build_dot(dot, eq, node_id)


def render_error(error: dict) -> None:
    st.error(f"**{error.get('error', 'Error')}**: {error.get('message', '')}")
    suggestion = error.get("suggestion")
    if suggestion:
        st.warning(f"Suggestion: {suggestion}")
