import streamlit as st
import traceback
import re
import os
from datetime import datetime

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="Smart Error Debugger",
    page_icon="🐞",
    layout="wide"
)

# ================= LOAD CSS (FIXED) =================
def load_css():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    css_path = os.path.join(base_dir, "style.css")
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ================= OPTIONAL OPENAI =================
try:
    from openai import OpenAI
    client = OpenAI()   # uses OPENAI_API_KEY from environment
    OPENAI_AVAILABLE = True
except Exception:
    OPENAI_AVAILABLE = False

# ================= SIDEBAR =================
st.sidebar.title("🧠 Smart Debugger")
st.sidebar.markdown("""
**Features**
- Python Error Detection  
- Line Highlighting  
- Local Auto Fix  
- ChatGPT Quick Fix  
- Error History  
""")

st.sidebar.markdown("---")

if OPENAI_AVAILABLE:
    st.sidebar.success("✅ ChatGPT Connected")
else:
    st.sidebar.info("🔒 ChatGPT Disabled (API key not set)")

st.sidebar.markdown("---")
st.sidebar.caption("Built for learning & interviews")

# ================= TITLE =================
st.markdown("<h1 class='title'>🐞 Smart Error Debugging Assistant</h1>", unsafe_allow_html=True)

# ================= SESSION STATE =================
if "history" not in st.session_state:
    st.session_state.history = []

# ================= TABS =================
tabs = st.tabs([
    "🛠 Smart Debugger",
    "⚡ ChatGPT Quick Fix",
    "📜 Error History"
])

# =========================================================
# SMART DEBUGGER TAB
# =========================================================
with tabs[0]:
    st.markdown("### Paste your Python code")

    code = st.text_area(
        "Code Input",
        height=300,
        placeholder="Example:\na = 10\nb = 0\nprint(a / b)"
    )

    use_ai = OPENAI_AVAILABLE and st.checkbox("💡 Show ChatGPT Quick Fix")

    def analyze_code(user_code):
        try:
            exec(user_code, {})
            return {"status": "success"}
        except Exception as e:
            tb = traceback.format_exc()
            error_type = type(e).__name__
            lines = user_code.splitlines()
            line_no = None

            match = re.search(r"line (\d+)", tb)
            if match:
                ln = int(match.group(1))
                if 1 <= ln <= len(lines):
                    line_no = ln

            # Detect unclosed quotes
            if error_type == "SyntaxError":
                for i, l in enumerate(lines):
                    if l.count('"') % 2 != 0 or l.count("'") % 2 != 0:
                        line_no = i + 1
                        break

            highlighted = ""
            for i, l in enumerate(lines, start=1):
                mark = "❌" if i == line_no else "  "
                highlighted += f"{mark} Line {i}: {l}\n"

            line_code = lines[line_no - 1] if line_no else ""

            if error_type == "SyntaxError":
                fix = line_code
                explanation = "Syntax error (missing quote / colon)"
            elif error_type == "NameError":
                var = str(e).split("'")[1]
                fix = f"{var} = 0"
                explanation = "Variable not defined"
            elif error_type == "TypeError":
                fix = "# Convert variables to same type"
                explanation = "Type mismatch"
            elif error_type == "ZeroDivisionError":
                fix = f"if b != 0:\n    {line_code}"
                explanation = "Division by zero"
            else:
                fix = line_code
                explanation = "Check logic"

            return {
                "status": "error",
                "error_type": error_type,
                "line": line_no,
                "highlighted": highlighted,
                "explanation": explanation,
                "fix": fix
            }

    if st.button("🔍 Analyze Code"):
        if not code.strip():
            st.warning("Please paste Python code.")
        else:
            result = analyze_code(code)
            if result["status"] == "success":
                st.success("✅ No errors found!")
            else:
                st.code(f"""
status:
error

error_type:
{result['error_type']}

error_line:
{result['line']}

highlighted_code:
{result['highlighted']}

explanation:
{result['explanation']}

fix_code:
{result['fix']}
""", language="text")

                st.session_state.history.append({
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "error": result["error_type"],
                    "line": result["line"]
                })

# =========================================================
# CHATGPT QUICK FIX TAB
# =========================================================
with tabs[1]:
    st.markdown("### Fix a specific line")

    chat_code = st.text_area("Paste Code", height=250)
    error_line = st.number_input("Error Line Number", min_value=1, step=1)

    if st.button("⚡ Get Quick Fix"):
        if not OPENAI_AVAILABLE:
            st.info("ChatGPT disabled. Add OPENAI_API_KEY.")
        elif not chat_code.strip():
            st.warning("Paste code first.")
        else:
            lines = chat_code.splitlines()
            bad_line = lines[error_line - 1] if error_line <= len(lines) else ""

            prompt = f"""
Fix this Python line.
Return ONLY corrected code.

{bad_line}
"""
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0
                )
                st.code(response.choices[0].message.content, language="python")
            except Exception as e:
                st.error(f"AI Fix failed: {e}")

# =========================================================
# ERROR HISTORY TAB
# =========================================================
with tabs[2]:
    st.markdown("### 📜 Error History")

    if not st.session_state.history:
        st.info("No errors yet.")
    else:
        for h in reversed(st.session_state.history):
            st.markdown(
                f"""
                <div class="history-card">
                ⏱ {h['time']}  
                ❌ {h['error']} (Line {h['line']})
                </div>
                """,
                unsafe_allow_html=True
            )


