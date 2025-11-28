import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

from src.prompts import system_prompt, calendar_prompt
from src.planner import build_week_plan
from src.generators import generate_caption, generate_hashtags, generate_image_prompt
from src.utils import export_csv, export_json

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please add it in .env (local) or Streamlit Secrets (cloud).")
    st.stop()

st.set_page_config(page_title="Social Media Agent", page_icon="📣", layout="wide")
st.title("📣 Social Media Agent")

# Sidebar inputs
brand = st.sidebar.text_area("Brand description", placeholder="e.g., Eco-friendly skincare brand for Gen Z.")
audience = st.sidebar.text_input("Target audience", placeholder="e.g., Gen Z, eco-conscious skincare enthusiasts")
platform = st.sidebar.selectbox("Platform", ["Instagram", "LinkedIn", "Twitter"])
tone = st.sidebar.selectbox("Tone", ["professional", "friendly", "bold", "educational"])
goal = st.sidebar.selectbox("Primary goal", ["awareness", "engagement", "leads"])
use_emojis = st.sidebar.checkbox("Use emojis", value=True)

# LLM setup
@st.cache_resource
def get_client():
    return OpenAI(api_key=OPENAI_API_KEY)

def run_llm(system, user):
    client = get_client()
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.8
    )
    return resp.choices[0].message.content.strip()

col_generate, col_export = st.columns([2,1])

with col_generate:
    if st.button("Generate 7-day plan"):
        if not OPENAI_API_KEY:
            st.error("OpenAI API key not set.")
            st.stop()
        if not brand or not audience:
            st.error("Please fill brand and audience.")
            st.stop()

        system = system_prompt(platform, tone)
        user_calendar = calendar_prompt(brand, audience, goal, platform)
        # Ask LLM to output JSON array for robust parsing
        json_calendar_prompt = user_calendar + "\nOutput as a JSON array with keys: theme, hook, post_type, cta, objective."
        raw_calendar = run_llm(system, json_calendar_prompt)

        # Try to parse JSON; fallback to default planner
        import json
        try:
            parsed = json.loads(raw_calendar)
        except Exception:
            st.warning("Using fallback calendar.")
            parsed = [{"theme": t["theme"], "hook": "Let's dive in.", "post_type": t["post_type"], "cta": "Follow for more.", "objective": goal}
                      for t in build_week_plan()]

        week = []
        for i, day_plan in enumerate(parsed):
            caption = run_llm(system, f"{brand}\n" + generate_caption(lambda x: run_llm(system, x), day_plan, tone, platform, use_emojis))
            hashtags = generate_hashtags(lambda x: run_llm(system, x), audience, brand, platform)
            img_prompt = generate_image_prompt(lambda x: run_llm(system, x), day_plan, brand, platform)

            week.append({
                "day": f"Day {i+1}",
                "theme": day_plan.get("theme",""),
                "post_type": day_plan.get("post_type",""),
                "hook": day_plan.get("hook",""),
                "caption": caption,
                "hashtags": " ".join(hashtags),
                "cta": day_plan.get("cta",""),
                "objective": day_plan.get("objective",""),
                "image_prompt": img_prompt
            })

        st.success("Plan generated!")
        st.session_state["week"] = week

with col_export:
    if "week" in st.session_state:
        week = st.session_state["week"]
        st.download_button("Download CSV", data="\n".join([
            "day,theme,post_type,hook,caption,hashtags,cta,objective,image_prompt"
        ] + [
            f'{w["day"]},{w["theme"]},{w["post_type"]},"{w["hook"]}","{w["caption"]}","{w["hashtags"]}",{w["cta"]},{w["objective"]},"{w["image_prompt"]}"'
            for w in week
        ]), file_name="plan.csv", mime="text/csv")

        import json
        st.download_button("Download JSON", data=json.dumps(week, ensure_ascii=False, indent=2),
                           file_name="plan.json", mime="application/json")

# Display
if "week" in st.session_state:
    st.markdown("### 7-day calendar")
    for w in st.session_state["week"]:
        with st.expander(f"{w['day']} — {w['theme']} ({w['post_type']})"):
            st.write(f"**Hook:** {w['hook']}")
            st.write(f"**Caption:** {w['caption']}")
            st.write(f"**Hashtags:** {w['hashtags']}")
            st.write(f"**CTA:** {w['cta']}")
            st.write(f"**Objective:** {w['objective']}")
            st.write(f"**Image prompt:** {w['image_prompt']}")