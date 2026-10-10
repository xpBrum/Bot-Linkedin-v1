import sqlite3
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "candidaturas.db"

PROFILE_DEFAULT = """Formação: Análise e Desenvolvimento de Sistemas; MBA em Segurança da Informação.
Experiência: responsável pelo apoio de TI na operação de atendimento/ouvidoria da Prefeitura de Maricá, em ambiente de teleatendimento, sistemas de protocolos e canais telefone/WhatsApp/e-mail.
Interesses: Segurança da Informação, GRC, Compliance, LGPD/Privacidade, Governança de TI, Monitoramento, Blue Team, Suporte de TI, Suporte ao Cliente e Sistemas.
Conhecimentos e estudos: ISO/IEC 27001/27002, LGPD, NIST, OWASP, fundamentos de segurança, Python, JavaScript, HTML/CSS, Git, Windows Prompt; interesse em SQL Server, PostgreSQL, Active Directory/Entra ID, SSO/MFA, Jira e indicadores/KPIs.
Preferências: remoto, híbrido ou presencial; salário flexível, priorizando aderência, crescimento e oportunidade de desenvolvimento.
"""
DEFAULT_TERMS = "segurança da informação, suporte de TI, analista de suporte, analista de sistemas, GRC, compliance, LGPD, privacidade, governança de TI, SOC, blue team, monitoramento, service desk, suporte técnico, risco, ISO 27001, IAM, SQL, infraestrutura"

def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT DEFAULT '',
            location TEXT DEFAULT '',
            modality TEXT DEFAULT '',
            salary TEXT DEFAULT '',
            url TEXT DEFAULT '',
            description TEXT DEFAULT '',
            score INTEGER DEFAULT 0,
            rationale TEXT DEFAULT '',
            status TEXT DEFAULT 'Encontrada',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(title, company, url)
        )
    """)
    conn.commit()
    return conn

def tokens(text):
    import re
    return set(re.findall(r"[a-zA-ZÀ-ÿ0-9+#.]{2,}", (text or "").lower()))

def score_job(title, description, modality, salary, profile, priorities):
    text = f"{title} {description}"
    jt = tokens(text)
    pt = tokens(profile)
    terms = [x.strip().lower() for x in priorities.split(",") if x.strip()]
    matched = [t for t in terms if t in text.lower()]
    # Weighted role relevance: explicit role keywords, skill overlap, profile education/context.
    role_points = min(40, len(matched) * 7)
    skill_overlap = len(jt & pt)
    skill_points = min(30, skill_overlap * 2)
    education_points = 10 if any(x in text.lower() for x in ["ads", "análise e desenvolvimento", "segurança da informação", "mba", "superior", "tecnólogo"]) else 0
    modality_points = 10 if not modality or any(x in modality.lower() for x in ["remoto", "híbrido", "hibrido", "presencial", "não informado", "nao informado"]) else 4
    growth_points = 10 if any(x in text.lower() for x in ["júnior", "junior", "trainee", "pleno", "desenvolvimento", "aprendizado", "crescimento", "n1", "n2", "assistente", "analista"]) else 0
    score = max(0, min(100, role_points + skill_points + education_points + modality_points + growth_points))
    reasons = []
    if matched: reasons.append("Termos alinhados: " + ", ".join(matched[:6]))
    if skill_overlap: reasons.append(f"{skill_overlap} palavras/competências em comum")
    if education_points: reasons.append("Possível aderência à formação")
    if not reasons: reasons.append("Poucos sinais explícitos de aderência; revisar manualmente")
    return score, "; ".join(reasons)

def add_job(conn, row, profile, priorities):
    title = str(row.get("title", "")).strip()
    if not title:
        return False, "Título obrigatório"
    company = str(row.get("company", "") or "").strip()
    location = str(row.get("location", "") or "").strip()
    modality = str(row.get("modality", "") or "").strip()
    salary = str(row.get("salary", "") or "").strip()
    url = str(row.get("url", "") or "").strip()
    description = str(row.get("description", "") or "").strip()
    score, rationale = score_job(title, description, modality, salary, profile, priorities)
    now = datetime.now().isoformat(timespec="seconds")
    try:
        conn.execute("""INSERT INTO jobs(title,company,location,modality,salary,url,description,score,rationale,status,notes,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,'Encontrada','',?,?)""",
        (title, company, location, modality, salary, url, description, score, rationale, now, now))
        conn.commit()
        return True, f"Vaga adicionada ({score}/100)"
    except sqlite3.IntegrityError:
        return False, "Vaga duplicada (mesmo título, empresa e link)"

st.set_page_config(page_title="Bot de Candidaturas", page_icon="🎯", layout="wide")
st.title("🎯 Bot de Candidaturas — painel local")
st.caption("Organiza e prioriza vagas. A candidatura no LinkedIn é sempre confirmada manualmente por você.")
conn = db()

with st.sidebar:
    st.header("Seu perfil")
    profile = st.text_area("Perfil profissional usado na pontuação", value=PROFILE_DEFAULT, height=280)
    priorities = st.text_area("Termos prioritários (separados por vírgula)", value=DEFAULT_TERMS, height=120)
    st.info("Edite o perfil e os termos para melhorar a classificação. A pontuação é heurística, não uma garantia de compatibilidade.")

tab_add, tab_import, tab_manage, tab_export = st.tabs(["➕ Adicionar vaga", "📥 Importar CSV", "📋 Acompanhar candidaturas", "📤 Exportar"])

with tab_add:
    st.subheader("Cadastrar uma oportunidade")
    with st.form("new_job", clear_on_submit=True):
        c1, c2 = st.columns(2)
        title = c1.text_input("Cargo *", placeholder="Ex.: Analista de Suporte N1")
        company = c2.text_input("Empresa", placeholder="Nome da empresa")
        location = c1.text_input("Localidade", placeholder="Ex.: Remoto / Rio de Janeiro")
        modality = c2.selectbox("Modalidade", ["Não informado", "Remoto", "Híbrido", "Presencial"])
        salary = c1.text_input("Salário / faixa", placeholder="Ex.: a combinar")
        url = c2.text_input("Link da vaga", placeholder="https://...")
        description = st.text_area("Descrição e requisitos", height=180, placeholder="Cole aqui a descrição da vaga.")
        submitted = st.form_submit_button("Calcular aderência e salvar", type="primary")
        if submitted:
            ok, msg = add_job(conn, {"title":title,"company":company,"location":location,"modality":modality,"salary":salary,"url":url,"description":description}, profile, priorities)
            (st.success if ok else st.warning)(msg)

with tab_import:
    st.subheader("Importar várias vagas de uma vez")
    st.write("Envie um CSV com as colunas: `title`, `company`, `location`, `modality`, `salary`, `url`, `description`.")
    sample = pd.DataFrame([{"title":"Analista de Suporte N1","company":"Empresa exemplo","location":"Brasil","modality":"Remoto","salary":"A combinar","url":"https://www.linkedin.com/jobs/","description":"Suporte técnico por chat e e-mail, troubleshooting Windows, SQL e Jira."}])
    st.download_button("Baixar modelo CSV", sample.to_csv(index=False).encode("utf-8-sig"), "modelo_vagas.csv", "text/csv")
    uploaded = st.file_uploader("Selecione o CSV", type=["csv"])
    if uploaded is not None and st.button("Importar e pontuar vagas"):
        try:
            df = pd.read_csv(uploaded).fillna("")
            required = {"title"}
            if not required.issubset(set(df.columns)):
                st.error("O CSV precisa ter ao menos a coluna 'title'.")
            else:
                count = 0
                for _, row in df.iterrows():
                    ok, _ = add_job(conn, row.to_dict(), profile, priorities)
                    count += int(ok)
                st.success(f"{count} vaga(s) importada(s). Duplicadas ou sem título foram ignoradas.")
        except Exception as e:
            st.error(f"Não foi possível ler o CSV: {e}")

with tab_manage:
    st.subheader("Vagas classificadas por aderência")
    statuses = ["Todas", "Encontrada", "Revisar", "Pronta para candidatura", "Candidatura enviada", "Entrevista", "Recusada", "Encerrada"]
    filter_status = st.selectbox("Filtrar por status", statuses)
    min_score = st.slider("Pontuação mínima", 0, 100, 0, 5)
    query = "SELECT * FROM jobs WHERE score >= ?"
    params = [min_score]
    if filter_status != "Todas":
        query += " AND status = ?"
        params.append(filter_status)
    query += " ORDER BY score DESC, updated_at DESC"
    rows = conn.execute(query, params).fetchall()
    if not rows:
        st.info("Nenhuma vaga cadastrada com esses filtros. Adicione uma vaga ou importe um CSV.")
    else:
        st.write(f"{len(rows)} vaga(s)")
        for job in rows:
            with st.container(border=True):
                c1, c2 = st.columns([4,1])
                c1.markdown(f"**{job['title']}** — {job['company'] or 'Empresa não informada'}")
                c1.caption(f"{job['location']} · {job['modality']} · {job['salary']}")
                c2.metric("Aderência", f"{job['score']}/100")
                st.write(job["rationale"])
                with st.expander("Descrição, notas e atualização"):
                    st.write(job["description"] or "Sem descrição.")
                    new_status = st.selectbox("Status", ["Encontrada","Revisar","Pronta para candidatura","Candidatura enviada","Entrevista","Recusada","Encerrada"], index=["Encontrada","Revisar","Pronta para candidatura","Candidatura enviada","Entrevista","Recusada","Encerrada"].index(job["status"]) if job["status"] in ["Encontrada","Revisar","Pronta para candidatura","Candidatura enviada","Entrevista","Recusada","Encerrada"] else 0, key=f"status_{job['id']}")
                    notes = st.text_area("Notas", value=job["notes"] or "", key=f"notes_{job['id']}", height=70)
                    if st.button("Salvar atualização", key=f"save_{job['id']}"):
                        now = datetime.now().isoformat(timespec="seconds")
                        conn.execute("UPDATE jobs SET status=?, notes=?, updated_at=? WHERE id=?", (new_status, notes, now, job["id"]))
                        conn.commit()
                        st.success("Atualizado. Recarregue a página se necessário.")
                if job["url"]:
                    st.link_button("Abrir vaga para revisar/candidatar-se", job["url"])
                if job["status"] != "Candidatura enviada":
                    if st.button("Confirmo: candidatura enviada", key=f"applied_{job['id']}"):
                        now = datetime.now().isoformat(timespec="seconds")
                        conn.execute("UPDATE jobs SET status='Candidatura enviada', updated_at=? WHERE id=?", (now, job["id"]))
                        conn.commit()
                        st.success("Status registrado como candidatura enviada.")

with tab_export:
    st.subheader("Exportar histórico")
    all_rows = conn.execute("SELECT title,company,location,modality,salary,url,score,rationale,status,notes,created_at,updated_at FROM jobs ORDER BY score DESC").fetchall()
    df = pd.DataFrame([dict(r) for r in all_rows])
    if df.empty:
        st.info("Ainda não há candidaturas para exportar.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Baixar histórico CSV", df.to_csv(index=False).encode("utf-8-sig"), "historico_candidaturas.csv", "text/csv")

st.divider()
st.caption("Privacidade: os dados ficam em um arquivo SQLite local neste computador. Não armazene senhas do LinkedIn nem automatize login, CAPTCHA ou envio de candidaturas.")
