"""
SkillBridge AI - Personal Skill Gap & Career Roadmap Analyzer
Run:  streamlit run app.py
"""
import json
import re
from datetime import date
from pathlib import Path

import plotly.graph_objects as go
import pandas as pd
import streamlit as st

st.set_page_config(page_title="SkillBridge AI", page_icon="🌉", layout="wide")
DATA_FILE = Path("progress.json")  # simple local storage for the tracker

# ----------------------------------------------------------------------------
# KNOWLEDGE BASE
# skill: (required level 1-5, resume keywords, learning resource, mini project)
# Skills are listed in learning order (foundations first).
# ----------------------------------------------------------------------------
CAREERS = {
    "Data Analyst": {
        "Python": (4, ["python", "pandas", "numpy"], "CS50P / Python for Everybody", "Clean and analyse a Kaggle dataset"),
        "SQL": (4, ["sql", "mysql", "postgresql"], "SQLBolt + LeetCode SQL", "Design a college DB and write 20 queries"),
        "Statistics": (3, ["statistics", "probability", "hypothesis"], "Khan Academy Statistics", "A/B test analysis on sample data"),
        "Excel": (3, ["excel", "pivot", "vlookup"], "ExcelIsFun (YouTube)", "Monthly expense dashboard"),
        "Data Visualization": (4, ["tableau", "power bi", "matplotlib", "plotly"], "Power BI / Tableau free tutorials", "Sales dashboard with 5 KPIs"),
        "Machine Learning Basics": (2, ["machine learning", "scikit-learn", "regression"], "Andrew Ng ML Specialization", "Predict house prices"),
        "Communication": (3, ["presentation", "communication", "report"], "Toastmasters / class seminars", "Present findings to your class"),
    },
    "Full Stack Web Developer": {
        "HTML/CSS": (4, ["html", "css", "responsive"], "freeCodeCamp Responsive Web Design", "Portfolio website"),
        "JavaScript": (4, ["javascript", "es6", "dom"], "javascript.info", "To-do app with local storage"),
        "React": (3, ["react", "jsx", "hooks"], "Official React docs tutorial", "Weather app using an API"),
        "Node.js & APIs": (3, ["node", "express", "rest api"], "The Odin Project", "REST API for a blog"),
        "Databases": (3, ["mongodb", "sql", "mysql", "postgresql"], "MongoDB University / SQLBolt", "Add auth + DB to the blog API"),
        "Git & GitHub": (4, ["git", "github"], "Git official tutorial", "Push every project with clean commits"),
        "Deployment": (2, ["deploy", "vercel", "render", "netlify"], "Vercel / Render docs", "Deploy your full-stack app live"),
    },
    "Machine Learning Engineer": {
        "Python": (5, ["python", "numpy", "pandas"], "CS50P + Python Data Science Handbook", "Data cleaning pipeline"),
        "Maths (LA, Calculus, Prob)": (4, ["linear algebra", "calculus", "probability"], "3Blue1Brown + MIT OCW", "Implement gradient descent from scratch"),
        "Machine Learning": (4, ["machine learning", "scikit-learn", "classification", "regression"], "Andrew Ng ML Specialization", "Spam classifier"),
        "Deep Learning": (3, ["deep learning", "tensorflow", "pytorch", "neural network"], "fast.ai / DeepLearning.AI", "Image classifier (CNN)"),
        "Data Structures & Algorithms": (3, ["data structures", "algorithms", "leetcode"], "NeetCode roadmap", "Solve 100 LeetCode problems"),
        "MLOps Basics": (2, ["docker", "mlflow", "flask", "fastapi"], "Made With ML", "Serve a model using FastAPI"),
    },
    "Cybersecurity Analyst": {
        "Networking": (4, ["networking", "tcp/ip", "dns", "http"], "Professor Messer Network+", "Capture & analyse traffic in Wireshark"),
        "Linux": (4, ["linux", "bash", "shell"], "OverTheWire Bandit", "Automate tasks with bash scripts"),
        "Python Scripting": (3, ["python", "scripting", "automation"], "Automate the Boring Stuff", "Port scanner (on your own lab)"),
        "Security Fundamentals": (4, ["owasp", "encryption", "cryptography", "security"], "TryHackMe Pre-Security path", "Write an OWASP Top 10 summary"),
        "Ethical Hacking Tools": (3, ["nmap", "burp", "metasploit", "kali"], "TryHackMe / HackTheBox Academy", "Solve 10 beginner CTF rooms"),
        "Cloud Security": (2, ["aws", "azure", "iam"], "AWS Cloud Practitioner", "Secure an S3 bucket correctly"),
    },
    "Cloud / DevOps Engineer": {
        "Linux": (4, ["linux", "bash", "shell"], "Linux Journey", "Set up a Linux server on a VM"),
        "Networking Basics": (3, ["networking", "dns", "tcp/ip", "http"], "Computer Networking (Kurose)", "Host a site behind Nginx"),
        "Git & CI/CD": (4, ["git", "github actions", "jenkins", "ci/cd"], "GitHub Actions docs", "Auto-test & deploy a project"),
        "Docker": (4, ["docker", "container"], "Docker official Get Started", "Containerise a web app"),
        "Cloud (AWS/Azure)": (3, ["aws", "azure", "gcp", "cloud"], "AWS Cloud Practitioner", "Deploy an app on AWS free tier"),
        "Kubernetes": (2, ["kubernetes", "k8s", "helm"], "Kubernetes Basics (docs)", "Run your container on minikube"),
        "Infrastructure as Code": (2, ["terraform", "ansible"], "HashiCorp Learn", "Provision a VM using Terraform"),
    },
}

LEVELS = {0: "None", 1: "Heard of it", 2: "Basics", 3: "Can build small things", 4: "Confident", 5: "Expert"}
COLORS = {"High": "#e74c3c", "Medium": "#f39c12", "Low": "#3498db", "Ready": "#2ecc71"}


# ----------------------------------------------------------------------------
# HELPERS
# ----------------------------------------------------------------------------
def load_db() -> dict:
    try:
        return json.loads(DATA_FILE.read_text())
    except Exception:
        return {}


def save_db(db: dict) -> None:
    DATA_FILE.write_text(json.dumps(db, indent=2))


def priority(gap: int) -> str:
    return "High" if gap >= 3 else "Medium" if gap == 2 else "Low" if gap == 1 else "Ready"


def analyze(career: str, ratings: dict) -> pd.DataFrame:
    rows = []
    for skill, (req, _kw, res, proj) in CAREERS[career].items():
        cur = ratings[skill]
        gap = max(req - cur, 0)
        rows.append({"Skill": skill, "Current": cur, "Required": req, "Gap": gap,
                     "Priority": priority(gap), "Resource": res, "Project": proj})
    return pd.DataFrame(rows)


def readiness(df: pd.DataFrame) -> float:
    return round(100 * df.apply(lambda r: min(r.Current, r.Required), axis=1).sum() / df.Required.sum(), 1)


def build_roadmap(df: pd.DataFrame, start_sem: int) -> dict:
    """Spread skill gaps (in foundation-first order) across remaining semesters."""
    gaps = list(df[df.Gap > 0].itertuples())
    sems = list(range(start_sem, 9))
    if not gaps or not sems:
        return {}
    plan = {s: [] for s in sems}
    for i, row in enumerate(gaps):
        plan[sems[i * len(sems) // len(gaps)]].append(row)
    return {s: v for s, v in plan.items() if v}


def scan_resume(text: str, career: str) -> set:
    low = text.lower()
    return {s for s, v in CAREERS[career].items()
            if any(re.search(r"(?<!\w)" + re.escape(k) + r"(?!\w)", low) for k in v[1])}


def make_report(name, career, sem, score, df, plan) -> str:
    lines = [f"SKILLBRIDGE AI REPORT - {name}", f"Date: {date.today()}", f"Target: {career} | Semester: {sem}",
             f"Career readiness: {score}%", "", "SKILL GAPS"]
    for r in df.itertuples():
        lines.append(f"- {r.Skill}: {r.Current}/{r.Required} ({r.Priority})")
    lines += ["", "ROADMAP"]
    for s, items in plan.items():
        lines.append(f"Semester {s}:")
        for r in items:
            lines.append(f"  * {r.Skill} -> {r.Resource} | Project: {r.Project}")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# SIDEBAR (live inputs - everything below updates instantly)
# ----------------------------------------------------------------------------
with st.sidebar:
    st.title("🌉 SkillBridge AI")
    st.caption("Know your gap. Build your bridge.")
    name = st.text_input("Your name", "Student")
    sem = st.selectbox("Current semester", [1, 2, 3, 4, 5, 6, 7, 8], help="1st year = semester 1 or 2")
    year = st.selectbox(
    "Current Year",
    ["1st Year", "2nd Year", "3rd Year", "4th Year"]
)
    career = st.selectbox("Target career", list(CAREERS))
    hours = st.slider("Study hours per week", 2, 30, 8)
    st.subheader("Rate your skills (0-5)")
    ratings = {s: st.slider(s, 0, 5, 1, key=f"r-{career}-{s}", help=" | ".join(f"{k}: {v}" for k, v in LEVELS.items()))
               for s in CAREERS[career]}

df = analyze(career, ratings)
score = readiness(df)
plan = build_roadmap(df, sem)
total_hours = int(df.Gap.sum() * 15)  # ~15 hours per level gained
weeks = round(total_hours / hours, 1)

st.title(f"🎯 {career} - Skill Gap Dashboard")
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🗺️ Roadmap", "📄 Resume Scan", "✅ Tracker"])

# ----------------------------------------------------------------------------
# TAB 1 - DASHBOARD
# ----------------------------------------------------------------------------
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Career readiness", f"{score}%")
    c2.metric("Skills ready", f"{(df.Gap == 0).sum()} / {len(df)}")
    top = df.sort_values("Gap", ascending=False).iloc[0]
    c3.metric("Biggest gap", top.Skill if top.Gap else "None 🎉")
    c4.metric("Time to bridge", f"{weeks} weeks", help=f"~{total_hours} study hours at {hours} h/week")
    st.progress(min(score / 100, 1.0))
    st.info("Beginner stage - start with the High-priority skills." if score < 40
            else "Developing - keep building projects." if score < 70
            else "Job-ready track - polish projects and apply for internships!")

    left, right = st.columns(2)
    with left:
        fig = go.Figure()
        skills = df.Skill.tolist()
        fig.add_trace(go.Scatterpolar(r=df.Required.tolist() + [df.Required[0]], theta=skills + [skills[0]],
                                      fill="toself", name="Required", line_color="#e74c3c"))
        fig.add_trace(go.Scatterpolar(r=df.Current.tolist() + [df.Current[0]], theta=skills + [skills[0]],
                                      fill="toself", name="You", line_color="#2ecc71"))
        fig.update_layout(polar=dict(radialaxis=dict(range=[0, 5])), title="Skill radar", height=420)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        bar = go.Figure(go.Bar(x=df.Gap, y=df.Skill, orientation="h",
                               marker_color=[COLORS[p] for p in df.Priority]))
        bar.update_layout(title="Gap per skill (levels to gain)", height=420, yaxis=dict(autorange="reversed"))
        st.plotly_chart(bar, use_container_width=True)

    st.dataframe(df[["Skill", "Current", "Required", "Gap", "Priority"]], use_container_width=True, hide_index=True)

# ----------------------------------------------------------------------------
# TAB 2 - ROADMAP
# ----------------------------------------------------------------------------
with tab2:
    if not plan:
        st.success("No gaps found - you're ready! Focus on internships and advanced projects.")
    else:
        st.write(f"Personalised plan from **Semester {sem}** to **Semester 8** for **{name}**:")
        for s, items in plan.items():
            with st.expander(f"📘 Semester {s}  ({len(items)} skill{'s' if len(items) > 1 else ''})", expanded=(s == sem)):
                for r in items:
                    st.markdown(f"**{r.Skill}** - level {r.Current} → {r.Required}  `{r.Priority}`")
                    st.markdown(f"- 📚 Learn: {r.Resource}\n- 🛠️ Project: {r.Project}\n- ⏱️ Effort: ~{r.Gap * 2} weeks")
        st.download_button("⬇️ Download report", make_report(name, career, sem, score, df, plan),
                           file_name=f"skillbridge_{name}.txt")

# ----------------------------------------------------------------------------
# TAB 3 - RESUME SCAN
# ----------------------------------------------------------------------------
with tab3:
    st.write("Paste your resume text to check whether it shows the skills your target career needs.")
    text = st.text_area("Resume text", height=250)
    if text.strip():
        found = scan_resume(text, career)
        missing = [s for s in CAREERS[career] if s not in found]
        st.metric("Resume skill coverage", f"{round(100 * len(found) / len(CAREERS[career]))}%")
        a, b = st.columns(2)
        a.success("✅ Found: " + (", ".join(sorted(found)) or "none"))
        b.warning("❌ Not visible: " + (", ".join(missing) or "none"))
        hidden = [s for s in missing if ratings[s] >= 3]
        if hidden:
            st.info("You rate yourself 3+ in these but they're missing from your resume: " + ", ".join(hidden))
        tips = []
        if not re.search(r"\d", text): tips.append("Add numbers to show impact (e.g. 'built app used by 50 students').")
        if "github" not in text.lower(): tips.append("Add your GitHub link.")
        if "project" not in text.lower(): tips.append("Add a Projects section.")
        for t in tips:
            st.write("💡", t)

# ----------------------------------------------------------------------------
# TAB 4 - TRACKER (saved to progress.json)
# ----------------------------------------------------------------------------
with tab4:
    db = load_db()
    key = f"{name}|{career}"
    saved = set(db.get(key, []))
    st.write("Tick off skills as you complete them. Your progress is saved locally.")
    todo = df[df.Gap > 0].Skill.tolist()
    if not todo:
        st.success("Nothing to track - all skills are at the required level!")
    else:
        done = [s for s in todo if st.checkbox(s, value=s in saved, key=f"d-{name}-{career}-{s}")]
        st.progress(len(done) / len(todo), text=f"{len(done)} of {len(todo)} skills completed")
        if st.button("💾 Save progress"):
            db[key] = done
            save_db(db)
            st.toast("Progress saved!", icon="✅")
