import streamlit as st
import os
from openai import OpenAI

# Get API key from environment (works locally with .env and on Streamlit Cloud via Secrets)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    st.error("OpenAI API key not found. Please add it in Streamlit Secrets (cloud) or .env (local).")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

# Streamlit UI
st.set_page_config(page_title="📣 Social Media Agent", page_icon="📱", layout="wide")
st.title("📣 Social Media Agent")

brand = st.text_input("Enter your brand description", placeholder="Eco-friendly skincare brand")
audience = st.text_input("Enter your target audience", placeholder="Gen Z, eco-conscious users")
platform = st.selectbox("Choose platform", ["Instagram", "Twitter", "LinkedIn"])
tone = st.selectbox("Tone", ["professional", "friendly", "bold"])
goal = st.selectbox("Primary goal", ["awareness", "engagement", "leads"])

if st.button("Generate 7-day Plan"):
    prompt = f"""
    Create a 7-day social media content plan for {brand}.
    Audience: {audience}
    Platform: {platform}
    Tone: {tone}
    Goal: {goal}

    For each day, include:
    - Theme
    - Hook
    - Caption
    - Hashtags
    - CTA
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a social media strategist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8
        )
        st.success("Plan generated successfully!")
        st.write(response.choices[0].message.content)

    except Exception as e:
        st.error(f"Error generating plan: {e}")