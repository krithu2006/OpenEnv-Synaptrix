import streamlit as st
from env.environment import EmailTriageEnv
from agent.agent import simple_agent

st.set_page_config(page_title="AI Email Triage", layout="wide")

st.title("📧 AI Email Triage Environment")

env = EmailTriageEnv()

if "obs" not in st.session_state:
    st.session_state.obs = env.reset()

obs = st.session_state.obs

st.subheader("📩 Email")
st.write(f"**Subject:** {obs.subject}")
st.write(f"**Body:** {obs.body}")
st.write(f"**Sender:** {obs.sender}")

if st.button("Analyze Email"):
    action = simple_agent(obs)
    result = env.step(action)

    st.subheader("🤖 AI Output")
    st.write(f"Category: {action.category}")
    st.write(f"Priority: {action.priority}")
    st.write(f"Tone: {action.tone}")

    st.subheader("🏆 Reward Score")
    st.success(result.reward)

    st.subheader("✅ Correct Answer")
    st.write(result.info["correct"])

    st.session_state.obs = env.reset()
