import streamlit as st
from google import genai
import json

st.set_page_config(page_title="Résumé Scorer", layout="wide")

st.title("Résumé vs JD Fit Scorer")
st.caption("Day 5 Lab 5A — Gemini + Continue.dev + Streamlit")

col1, col2 = st.columns(2)

# -----------------------------
# Resume Upload
# -----------------------------
with col1:
    st.subheader("Résumé")

    resume_file = st.file_uploader(
        "Upload Résumé",
        type=["txt", "pdf", "docx"],
        key="resume_upload"
    )

    resume = ""

    if resume_file:
        try:
            resume = resume_file.read().decode("utf-8")
        except:
            resume = str(resume_file.read())

    resume = st.text_area(
        "Paste résumé",
        value=resume,
        height=400
    )

# -----------------------------
# JD Upload
# -----------------------------
with col2:
    st.subheader("Job Description")

    jd_file = st.file_uploader(
        "Upload JD",
        type=["txt", "pdf", "docx"],
        key="jd_upload"
    )

    jd = ""

    if jd_file:
        try:
            jd = jd_file.read().decode("utf-8")
        except:
            jd = str(jd_file.read())

    jd = st.text_area(
        "Paste job description",
        value=jd,
        height=400
    )

# -----------------------------
# API Key
# -----------------------------
api_key = st.text_input("Gemini API key", type="password")

try:
    api_key = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

# -----------------------------
# Score Button
# -----------------------------
if st.button("Score") and resume and jd and api_key:
    with st.spinner("Scoring..."):
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are a placement coach.

Given this résumé and job description, return only valid JSON in this exact format:

{{
  "score": 0,
  "rationale": "short explanation",
  "missing_skills": ["skill1", "skill2"],
  "suggestions": ["suggestion1", "suggestion2"],
  "technical_skills_match": 0,
  "soft_skills_match": 0,
  "experience_relevance": 0,
  "project_fit": 0,
  "learning_resources": [
    {{
      "skill": "Docker",
      "resource_type": "YouTube",
      "link": "https://youtube.com/example"
    }}
  ]
}}

Rules:
- score must be between 0 and 100.
- sub-scores must be between 0 and 100.
- missing_skills must contain only real missing skills, not generic words.
- learning_resources must suggest free learning resources.

Résumé:
{resume}

Job Description:
{jd}
"""

        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"}
        )

        try:
            result = json.loads(resp.text)

            st.metric("Fit Score", f"{result['score']}/100")

            st.subheader("Score Breakdown")
            breakdown = {
                "Technical Skills Match": result.get("technical_skills_match", 0),
                "Soft Skills Match": result.get("soft_skills_match", 0),
                "Experience Relevance": result.get("experience_relevance", 0),
                "Project Fit": result.get("project_fit", 0),
            }

            st.bar_chart(breakdown)

            st.subheader("Rationale")
            st.write(result.get("rationale", ""))

            st.subheader("Missing Skills")
            for skill in result.get("missing_skills", []):
                st.write(f"- {skill}")

            st.subheader("Suggestions")
            for suggestion in result.get("suggestions", []):
                st.write(f"- {suggestion}")

            st.subheader("Top Missing Skills with Learning Resources")
            for item in result.get("learning_resources", []):
                st.write(
                    f"- **{item.get('skill', '')}** "
                    f"({item.get('resource_type', '')}): "
                    f"{item.get('link', '')}"
                )

        except json.JSONDecodeError:
            st.error("Could not parse Gemini response as JSON.")
            st.write(resp.text)