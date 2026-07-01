import streamlit as st
import requests
import json

st.set_page_config(page_title="Skill Matching Tester", layout="wide")

st.title("🎯 Skill Matching Engine - API Tester")
st.markdown("This Streamlit app sends requests directly to your Hugging Face Space backend.")

# Settings Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    api_url = st.text_input(
        "Hugging Face Space URL", 
        value="https://nourhan214-skill-matching-engine.hf.space/match/upload",
        help="The full URL to your Hugging Face Space endpoint."
    )
    api_key = st.text_input(
        "App API Key (X-API-Key)", 
        type="password",
        help="The APP_API_KEY you set in your Hugging Face Space secrets."
    )

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.header("📄 Candidate CV")
    cv_file = st.file_uploader("Upload CV (PDF only)", type=["pdf"])

with col2:
    st.header("💼 Job Description")
    jd_input_type = st.radio("Provide Job Description via:", ["Text (Paste)", "Image (Screenshot)"])
    
    jd_text = None
    jd_image = None
    
    if jd_input_type == "Text (Paste)":
        jd_text = st.text_area("Paste Job Description Here", height=200)
    else:
        jd_image = st.file_uploader("Upload JD Screenshot", type=["png", "jpg", "jpeg", "webp"])

st.divider()

if st.button("🚀 Run Match", use_container_width=True, type="primary"):
    # Strip any accidental whitespace from the API key
    clean_api_key = api_key.strip() if api_key else ""
    
    if not clean_api_key:
        st.error("⚠️ Please provide the APP_API_KEY in the sidebar.")
    elif not cv_file:
        st.error("⚠️ Please upload a CV (PDF).")
    elif jd_input_type == "Text (Paste)" and not jd_text:
        st.error("⚠️ Please paste the Job Description text.")
    elif jd_input_type == "Image (Screenshot)" and not jd_image:
        st.error("⚠️ Please upload the Job Description image.")
    else:
        with st.spinner("Processing request on Hugging Face... This might take a few seconds."):
            headers = {
                "X-API-Key": clean_api_key
            }
            
            # Prepare multipart form data
            files = {
                "cv_file": (cv_file.name, cv_file.getvalue(), "application/pdf")
            }
            
            data = {}
            if jd_input_type == "Text (Paste)":
                data["job_description"] = jd_text
            else:
                files["job_description_image"] = (jd_image.name, jd_image.getvalue(), jd_image.type)

            try:
                response = requests.post(api_url, headers=headers, files=files, data=data)
                
                if response.status_code == 200:
                    st.success("✅ Match Successful!")
                    result_data = response.json()
                    
                    st.subheader("📊 Match Results")
                    
                    # Display the parsed CV and Job profiles in expanders
                    with st.expander("Parsed Candidate Profile"):
                        st.json(result_data.get("parsed_candidate", {}))
                        
                    with st.expander("Parsed Job Profile"):
                        st.json(result_data.get("parsed_job", {}))
                        
                    # Display the final evaluation result directly
                    st.subheader("💡 Final Evaluation")
                    st.json(result_data.get("match_result", {}))
                else:
                    st.error(f"❌ Error {response.status_code}")
                    try:
                        st.json(response.json())
                    except Exception:
                        st.text(response.text)
                    
            except Exception as e:
                st.error(f"Failed to connect to the API: {e}")
