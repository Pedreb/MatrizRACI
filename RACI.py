import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

# --- CONFIGURAÇÕES INICIAIS ---------------------------------------------------
st.set_page_config(page_title="Matriz RACI", page_icon="🗂️", layout="wide")

DB_FILE   = "raci.db"
LOGO_PATH = r"C:\\Users\\Pedro Curry\\OneDrive\\Área de Trabalho\\Rezende\\MARKETING\\__sitelogo__Logo Rezende.png"

ROLES = ["", "R", "A", "C", "I"]         # Valores válidos para cada responsável
HEADERS = [
    "ID", "Atividade / Decisão",
    "CEO", "Presidente Área",
    "Diretor Executivo", "Conselheiro",
    "Gestor Executivo"
]

COLOR_MAP = {                            # Cores da legenda
    "A": "#ff4d4d",   # vermelho
    "R": "#28a745",   # verde
    "C": "#ffc107",   # amarelo
    "I": "#007bff"    # azul
}

# --- CSS DE ESTILO ------------------------------------------------------------
st.markdown(
    """
    <style>
        html, body, [class*="css"]  { font-family: "Segoe UI", sans-serif; }
        .block-container            { padding-top: 1.5rem; }
        header, footer              { visibility: hidden; }
        table       { width: 100%; border-collapse: collapse; }
        thead th    { background: #2E3192; color: #fff; padding: 8px; text-align: center; }
        tbody td    { padding: 6px; text-align: center; font-weight: 600; }
        tbody tr:nth-child(even) { background: #f2f4f6; }
        .legend {
            display: flex; gap: 12px; margin-top: .8rem; flex-wrap: wrap;
        }
        .legend span {
            display: inline-block; padding: 6px 10px; border-radius: 6px;
            font-size: .85rem; color: #fff; font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- CONEXÃO BANCO & TABELA ---------------------------------------------------
def get_connection(db_file: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_file, check_same_thread=False)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS activities (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            atividade         TEXT NOT NULL,
            ceo               TEXT,
            presidente_area   TEXT,
            diretor_executivo TEXT,
            conselheiro       TEXT,
            gestor_executivo  TEXT
        )
        """
    )
    conn.commit()
    return conn

conn = get_connection(DB_FILE)

# --- FUNÇÕES DE I/O -----------------------------------------------------------
def insert_row(data: dict):
    conn.execute(
        """
        INSERT INTO activities
        (atividade, ceo, presidente_area, diretor_executivo, conselheiro, gestor_executivo)
        VALUES (:atividade, :ceo, :presidente_area, :diretor_executivo, :conselheiro, :gestor_executivo)
        """,
        data,
    )
    conn.commit()

def delete_row(activity_id: int):
    conn.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
    conn.commit()

def fetch_df() -> pd.DataFrame:
    df = pd.read_sql("SELECT * FROM activities", conn)
    if df.empty:
        return pd.DataFrame(columns=HEADERS)
    df.rename(
        columns={
            "id": "ID",
            "atividade": "Atividade / Decisão",
            "ceo": "CEO",
            "presidente_area": "Presidente Área",
            "diretor_executivo": "Diretor Executivo",
            "conselheiro": "Conselheiro",
            "gestor_executivo": "Gestor Executivo",
        },
        inplace=True,
    )
    return df[HEADERS]

def dataframe_to_html(df: pd.DataFrame) -> str:
    if df.empty:
        return "<p style='opacity:.6'>Nenhuma atividade cadastrada.</p>"
    html = "<table><thead><tr>" + "".join(f"<th>{col}</th>" for col in df.columns) + "</tr></thead><tbody>"
    for _, row in df.iterrows():
        html += "<tr>"
        html += f"<td>{row['ID']}</td><td>{row['Atividade / Decisão']}</td>"
        for col in df.columns[2:]:
            val = (row[col] or "").strip().upper()
            bgcolor = COLOR_MAP.get(val, "transparent")
            style = f"background:{bgcolor};color:#fff" if val else ""
            html += f"<td style='{style}'>{val}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

# --- SIDEBAR: LOGO + FORMULÁRIO ----------------------------------------------
with st.sidebar:
    logo_path = Path(LOGO_PATH)
    if logo_path.is_file():
        st.image(LOGO_PATH, use_container_width=True)
    else:
        st.write("🔷 **Sua Logo Aparecerá Aqui** (ajuste `LOGO_PATH`)")

    st.markdown("## ➕ Nova Atividade")

    form = st.form("add_activity", clear_on_submit=True)
    atividade = form.text_input("Atividade / Decisão *")
    ceo               = form.selectbox("CEO",               ROLES, index=0)
    presidente_area   = form.selectbox("Presidente Área",   ROLES, index=0)
    diretor_executivo = form.selectbox("Diretor Executivo", ROLES, index=0)
    conselheiro       = form.selectbox("Conselheiro",       ROLES, index=0)
    gestor_executivo  = form.selectbox("Gestor Executivo",  ROLES, index=0)

    submitted = form.form_submit_button("Gravar")
    if submitted:
        if not atividade.strip():
            st.error("⚠️ O campo *Atividade / Decisão* é obrigatório.")
        else:
            insert_row(
                {
                    "atividade": atividade.strip(),
                    "ceo": ceo,
                    "presidente_area": presidente_area,
                    "diretor_executivo": diretor_executivo,
                    "conselheiro": conselheiro,
                    "gestor_executivo": gestor_executivo,
                }
            )
            st.success("✅ Atividade adicionada com sucesso!")

# --- CONTEÚDO PRINCIPAL -------------------------------------------------------
st.title("🗂️ Matriz RACI – Governança de Decisões")

# Legenda primeiro
st.markdown(
    "<div class='legend'>" +
    "".join(
        f"<span style='background:{COLOR_MAP[c]}'>"
        f"{c} – {'Aprovador' if c=='A' else 'Responsável' if c=='R' else 'Consultado' if c=='C' else 'Informado'}"
        "</span>"
        for c in ["A", "R", "C", "I"]
    )
    + "</div>",
    unsafe_allow_html=True,
)

# Espaço entre legenda e tabela
st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# Tabela depois
df = fetch_df()
st.markdown(dataframe_to_html(df), unsafe_allow_html=True)

# Exclusão de atividade
if not df.empty:
    st.markdown("### 🗑️ Excluir Atividade")
    activity_id_to_delete = st.selectbox("Selecione o ID da atividade a excluir:", df["ID"])
    if st.button("Excluir atividade"):
        delete_row(activity_id_to_delete)
        st.success("Atividade excluída com sucesso. Atualize a página para ver a mudança.")

st.caption("© 2025 — Matriz RACI Rezende Energia")
