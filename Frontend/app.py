import streamlit as st
import requests

FASTAPI_ENDPOINT = "http://localhost:8000"

st.set_page_config(page_title="EHR Assistant", page_icon="🔍", initial_sidebar_state="collapsed")

st.title('EHR Assistant by VoxHealth Solutions')

st.markdown(f"<h3>Responds with a specific EHR message</h3>", unsafe_allow_html=True)

st.markdown("<br><br><br>",unsafe_allow_html=True)

if 'input' not in st.session_state:
    st.session_state['input'] = ""
if 'report_generated' not in st.session_state:
    st.session_state['report_generated'] = False
if 'report_content' not in st.session_state:
    st.session_state['report_content'] = ""
    
def process_request():
    response=requests.post(f'{FASTAPI_ENDPOINT}/process_request/',json={'query':st.session_state.input})
    if response.status_code==200:
        response_data = response.json()
        st.session_state['report_generated'] = True
        st.session_state['report_content'] = response_data.get('Generated Report', '')
        st.session_state['file_path'] = response_data.get('File Path', '')
        # return response_data
    else:
        st.error("Failed to recieve response from FASTAPI")
        return []

def save_report():
    response = requests.post(f"{FASTAPI_ENDPOINT}/save_report/", json={'report': st.session_state['edited_report'], 'file_path':  st.session_state['file_path']})
    if response.status_code == 200:
        st.success("Report saved successfully")
    else:
        st.error("Failed to save the report")
    st.session_state['report_generated'] = False
    st.session_state['report_content'] = ""
    
input_text=st.text_area("Input: ",key="input")

if st.button('Submit'):
    process_request()

if st.session_state['report_generated']:
    edited_report = st.text_area("Review and Edit Report:", value=st.session_state['report_content'], height=600, key='edited_report')
    if st.button('Save Report',on_click=save_report):
        pass
        

# Create a concise medical report for Arjun Patel, a 45-year-old male, who underwent a
# laparoscopic hernia repair on 03/22/2024 for a right inguinal hernia. The surgery, led by Dr. Anil
# Kumar and anesthesiologist Dr. Rhea Desai, lasted 1 hour and 30 minutes and involved three small
# abdominal incisions and mesh repair, concluding without complications. Patel's medical history
# includes controlled hypertension without prior surgeries. Post-surgery, Patel stayed in recovery
# for 2 hours with stable vitals, and received instructions for pain management, activity restrictions,
# and a follow-up on 04/05/2024. Discharge on 03/23/2024 included guidelines for pain
# management, wound care, infection monitoring, and a scheduled follow-up with Dr. Kumar.

#For patient Dev Jain, compare his creat levels to past records

# John ,id:fhgj23, 40 years old male came with complaints of pain in the epigastric region and
# right hypochondrium since 2-3 months.
# Since 1-2 weeks, the intensity and the frequency of pain increased such that pt had
# to take iv analgesics.
# Usg done on 19/3/24 suggestive of distended gall bladder with multiple calculi
# within ranging between 4-8 mm in size,common bile duct is normal in caliber.
# Patient was clinically examined,had tenderness in the upper abdomen in epigastric
# region,no relief with oral medications and hence planned for robotic
# cholecystectomy.
# Patient was thoroughly investigated and planned for surgery next week.
# Preop cbc being hb 15.1,wbc 6,500,platelets 2 lakh 28 thousand.
# Liver function tests : total bilirubin 0.55,direct bilirubin 0.13,indirect bilirubin
# 0.42,SGOT 20.3,SGPT 25.2,ALKALINE PHOPHATASE 63,Gamma GT 42.5
# Pt is a known Diabetic and his pre- op hbaic was 9.6
# Robotic cholecystectomy done on 26/3/24.
# Intraoperative findings: Gb edematous ,adhesions present,robotic dissection went
# smoothly,cystic artery and cystic duct isolated,clipped and cut,no biliary spillage
# while extracting the gall bladder,gall bladder showed more than 3 gall stones and
# sludge within.
# Postoperative day 0 : post 6 hours of surgery,hardly any pain .visual analogue scale
# being 0-1.
# Pt was started on water orally @ 50 cc per hour.
# Postoperative day 1 (27/3/24) pt had 2 episodes of nausea followed by bilious
# vomiting along with fever spikes starting from 99 degree Fahrenheit,and gradually
# stepping up to 100 degree Fahrenheit,100.1 degree Fahrenheit,
# Patient was evaluated,per abdominal examination was abdomen being soft,non
# tender and bs were present.
# Cbc was hb 15.4, wbc was 2200,platelects were 2 lakh 39,000
# Liver function tests ,total bilirubin 1.73,direct bilirubin 0.8,indirect bilirubin
# 0.93,SGOT 39,SGPT 37,ALKALINE PHOSPHATASE 117,GGTP 67.
# Patient was upgraded from inj supacef to inj Meropenem and Inj Tigecycline,and
# cbc and liver function tests were again repeated on 28/3/24.
# Cbc hb 15.1wbc 17,000 platelets 1,99,000
# Liver function tests- total bilirubin 2.02,direct bilirubin 0.92,indirect bilirubin
# 01.1,SGOT 69,SGPT 94,ALKALINE PHOSPHATASE 97,GGTP 164.
# Hence decision was taken to subject the patient for ERCP
# ERCP done on 28/3/24,sphincterotomy done,sludge retrieved
# On 29/3/24 pt’s parameters checked again.NO FEVER SPIKE SINCE ERCP.
# WBC reduced to 12,000.
# Liver function tests- total bilirubin 1.17,direct bilirubin 0.50,indirect bilirubin
# 0.67,SGOT 29,SGPT 64,ALKALINE PHOSPHATASE 100,GGTP 127.
# Patient settled well and discharged on 30/3/24.
# On discharge he had oral lesions of Herpes Labialis ,which was treated with single
# dose famciclovir and acivir cream .