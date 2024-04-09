import streamlit as st
import requests

FASTAPI_ENDPOINT = "http://localhost:8000/process_request/"

st.set_page_config(page_title="EHR Assistant", page_icon="🔍", initial_sidebar_state="collapsed")

st.title('EHR Assistant by VoxHealth Solutions')

st.markdown(f"<h3>Responds with a specific EHR message</h3>", unsafe_allow_html=True)

st.markdown("<br><br><br>",unsafe_allow_html=True)

if 'input' not in st.session_state:
    st.session_state['input'] = ""
    
def process_request():
    response=requests.post(FASTAPI_ENDPOINT,json={'query':st.session_state.input})
    if response.status_code==200:
        return response.json()
    else:
        st.error("Failed to recieve response from FASTAPI")
        return []
    
input_text=st.text_input("Input: ",key="input")

if st.button('Submit'):
    output=process_request()
    if output:
        st.write(output)

# Create a concise medical report for Arjun Patel, a 45-year-old male, who underwent a
# laparoscopic hernia repair on 03/22/2024 for a right inguinal hernia. The surgery, led by Dr. Anil
# Kumar and anesthesiologist Dr. Rhea Desai, lasted 1 hour and 30 minutes and involved three small
# abdominal incisions and mesh repair, concluding without complications. Patel's medical history
# includes controlled hypertension without prior surgeries. Post-surgery, Patel stayed in recovery
# for 2 hours with stable vitals, and received instructions for pain management, activity restrictions,
# and a follow-up on 04/05/2024. Discharge on 03/23/2024 included guidelines for pain
# management, wound care, infection monitoring, and a scheduled follow-up with Dr. Kumar.