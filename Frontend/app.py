import streamlit as st
import requests

FASTAPI_ENDPOINT = "http://localhost:8000"

st.set_page_config(page_title="EHR Assistant", page_icon="🔍", initial_sidebar_state="collapsed")

st.title('EHR Assistant by AristaSurge')

st.markdown(f"<h3>Responds with a specific EHR message</h3>", unsafe_allow_html=True)

st.markdown("<br><br><br>",unsafe_allow_html=True)

if 'input' not in st.session_state:
    st.session_state['input'] = ""

if 'report_content' not in st.session_state:
    st.session_state['report_content'] = ""

if 'updated_report' not in st.session_state:
    st.session_state['updated_report'] = ""

if 'undefined' not in st.session_state:
    st.session_state['undefined'] = ""

if 'create_new_report_block' not in st.session_state:
    st.session_state['create_new_report_block'] = False

if 'query_result' not in st.session_state:
    st.session_state['query_result'] = ''

    
def process_request():
    response=requests.post(f'{FASTAPI_ENDPOINT}/process_request/',json={'query':st.session_state.input})
    if response.status_code==200:
        response_data = response.json()
        st.session_state['intent']=response_data.get('Intent','')
        #For create intent
        st.session_state['report_content'] = response_data.get('Generated Report', '')
        st.session_state['file_path'] = response_data.get('File Path', '')
        st.session_state['patient_id_exists']=response_data.get('Patient id exists',False)
        #For update intent
        st.session_state['updated_report']=response_data.get('Updated Report','')
        #For read intent
        st.session_state['query_result']=response_data.get('read result','')
        #For undefined intent
        st.session_state['undefined']=response_data.get('undefined','')
    else:
        st.error("Failed to recieve response from FASTAPI")
        return []

def save_report():
    response = requests.post(f"{FASTAPI_ENDPOINT}/save_report/", json={'report': st.session_state['edited_report'], 'file_path':  st.session_state['file_path'],'intent':st.session_state['intent']})
    if response.status_code == 200:
        if response.json():
            st.warning('Patient id not provided')
        else:
            st.success("Report saved successfully")
    else:
        st.error("Failed to save the report")
    st.session_state['report_content'] = ""

def save_update_report():
    response = requests.post(f"{FASTAPI_ENDPOINT}/save_report/", json={'report': st.session_state['edited_updated_report'],'file_path':  st.session_state['file_path'],'intent':st.session_state['intent']})
    if response.status_code == 200:
        response_data=response.json()
        if response_data['message']=='Patient id is not provided':
            st.warning('Patient id not provided')
        elif response_data['message']=='Patient id does not exist in the database':
            st.warning('Patient id does not exist in the database')
            st.warning('You need to create a new record for the patient. Please check whether the input has sufficient information')
            #st.session_state['create_new_report_block']=True
        else:
            st.success("Report saved successfully")
    else:
        st.error("Failed to save the report")
    st.session_state['updated_report'] = ""

def create_new_report():
    st.session_state['intent']='create'
    st.write(st.session_state)
    
    
    
input_text=st.text_area("Input: ",key="input",height=200)

if st.button('Submit'):
    process_request()

if st.session_state['report_content']:
    edited_report = st.text_area("Review and Edit Report:", value=st.session_state['report_content'], height=600, key='edited_report')
    if not st.session_state.get('patient_id_exists', True):  # Default to True to avoid showing error on first load
        st.warning("Please ensure a Patient ID is included in the report.")
    if st.button('Save Report',on_click=save_report):
        pass

if st.session_state['updated_report']:
    updated_report = st.text_area("Review and Edit Report:", value=st.session_state['updated_report'], height=600, key='edited_updated_report')
    if not st.session_state.get('patient_id_exists', True):  # Default to True to avoid showing error on first load
        st.warning("Please ensure a Patient ID is included in the report.")
    if st.button('Save Report',on_click=save_update_report):
        pass

# if st.session_state['create_new_report_block']:
#     if st.button('Create a new Report with given information',on_click=process_request):
#         pass

if st.session_state['query_result']:
    st.write(st.session_state['query_result'])

if st.session_state['undefined']:
    st.warning(st.session_state['undefined']) 
    st.session_state['undefined'] = ""
    

# Create a concise medical report for Arjun Patel, a 45-year-old male, who underwent a
# laparoscopic hernia repair on 03/22/2024 for a right inguinal hernia. The surgery, led by Dr. Anil
# Kumar and anesthesiologist Dr. Rhea Desai, lasted 1 hour and 30 minutes and involved three small
# abdominal incisions and mesh repair, concluding without complications. Patel's medical history
# includes controlled hypertension without prior surgeries. Post-surgery, Patel stayed in recovery
# for 2 hours with stable vitals, and received instructions for pain management, activity restrictions,
# and a follow-up on 04/05/2024. Discharge on 03/23/2024 included guidelines for pain
# management, wound care, infection monitoring, and a scheduled follow-up with Dr. Kumar.

#For patient Dev Jain, compare his creat levels to past records

# John, 40 years old male came with complaints of pain in the epigastric region and
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

# add this to the record of Pt with id: jljj9,who followed up with us after 48 hours and
# Reports were within normal range
# Cbc hb 15.4,wbc 7,800 platelets 3,14,000
# Liver function tests- total bilirubin 0.83,direct bilirubin 0.22,indirect bilirubin
# 61,SGOT 33,SGPT 35,ALKALINE PHOSPHATASE109,GGTP 97.
# Suture removal done on 2/4/24 and patient doing well

# retrieve the latest lft results for john and the date of the test

# Patient John Doe, a 45-year-old male, was admitted for elective surgical repair of bilateral inguinal hernias, which he reported having troubled him for the past six months. The discomfort was notably exacerbated by physical activities and lifting heavy objects. On physical examination, the hernias were observed as bilateral, reducible, and without signs of strangulation or obstruction.
# The decision to perform a Transabdominal Preperitoneal (TEPP) hernia repair was made given the patient’s symptoms and physical findings. The procedure commenced at 08:30 AM under general anesthesia. The approach involved making a small incision just above the pubic area, followed by the insertion of a laparoscope for visualization. The hernia sacs were carefully dissected and reduced back into the abdominal cavity. A mesh was placed over the peritoneal opening to reinforce the abdominal wall and prevent recurrence.
# The mesh was secured without complications, and the layers of the abdomen were meticulously closed. The operation concluded successfully at 11:15 AM. Postoperatively, the patient was transferred to the recovery room in stable condition. He was monitored for any immediate complications and was prescribed pain management and instructions to limit physical activity. Follow-up was scheduled for two weeks post-operation to assess healing and discuss gradual return to normal activities. The patient was educated on signs of potential complications, such as infection or recurrence, and advised to report any unusual symptoms promptly.