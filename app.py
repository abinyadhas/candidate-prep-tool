import streamlit as st
import pypdf
import docx
from google import genai
from fpdf import FPDF

# Page Configuration
st.set_page_config(page_title="Candidate Prep Guide Generator", page_icon="🎯", layout="wide")

st.title("🎯 AI Candidate Prep Guide Generator")
st.write("Upload the Job Description, Hiring Guide, and past scorecards to automatically generate a tailored candidate prep guide.")

# Fetch API Key (Checks Streamlit Secrets first, falls back to sidebar input)
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.sidebar.header("Configuration")
    api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")
    st.sidebar.info("Get a free API key at: https://aistudio.google.com/")

# Helper function to extract text from uploaded files
def extract_text(uploaded_file):
    if uploaded_file is None:
        return ""
    text = ""
    file_type = uploaded_file.name.split('.')[-1].lower()
    
    if file_type == 'pdf':
        pdf_reader = pypdf.PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
    elif file_type == 'docx':
        doc = docx.Document(uploaded_file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif file_type == 'txt':
        text = uploaded_file.read().decode('utf-8')
        
    return text

# Function to convert generated text into a downloadable PDF
def create_pdf(text_content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=11)
    
    clean_text = text_content.encode('latin-1', 'replace').decode('latin-1')
    
    for line in clean_text.split('\n'):
        pdf.multi_cell(0, 8, txt=line)
        
    return bytes(pdf.output())

# Main Form
role_title = st.text_input("Role Title", placeholder="e.g., Product Marketing Manager")

col1, col2, col3 = st.columns(3)

with col1:
    jd_file = st.file_uploader("1. Upload Job Description", type=["pdf", "docx", "txt"])

with col2:
    hg_file = st.file_uploader("2. Upload Hiring Guide / Rubric", type=["pdf", "docx", "txt"])

with col3:
    scorecard_file = st.file_uploader("3. Upload Scorecards (Optional)", type=["pdf", "docx", "txt"])

# Generate Button
if st.button("🚀 Generate Candidate Prep Guide", type="primary"):
    if not api_key:
        st.error("Please enter a free Gemini API Key to continue.")
    elif not role_title or not jd_file or not hg_file:
        st.warning("Please fill in the Role Title and upload both the Job Description and Hiring Guide.")
    else:
        with st.spinner("Analyzing documents & extracting historical interview patterns..."):
            try:
                # Extract text
                jd_text = extract_text(jd_file)
                hg_text = extract_text(hg_file)
                scorecard_text = extract_text(scorecard_file) if scorecard_file else "No scorecards provided."

                # Initialize Gemini Client
                client = genai.Client(api_key=api_key)

                prompt = f"""
                You are an expert Talent Acquisition Specialist. Generate a comprehensive Candidate Prep Guide for the role of: {role_title}.

                Below are the source documents provided by the hiring team:

                --- JOB DESCRIPTION ---
                {jd_text}

                --- HIRING GUIDE / RUBRIC ---
                {hg_text}

                --- PAST CANDIDATE SCORECARDS ---
                {scorecard_text}

                Generate a well-structured Candidate Prep Guide with the following exact markdown sections:
                
                # 🎯 Candidate Prep Guide: {role_title}
                
                ## 📊 Role Overview & Core Focus
                Summarize what this team values most based on the rubric and feedback.
                
                ## ⚖️ Core Competencies & Rubric Mapping
                Create a table mapping key competencies to what a 5/5 'Strong Hire' looks like.
                
                ## ⚠️ Common Pitfalls & Rejection Reasons (From Past Feedback)
                Identify 3 specific candidate mistakes or red flags found in past feedback, and how candidates can avoid them.
                
                ## ❓ Targeted Practice Scenario Questions
                Provide 3 high-leverage practice questions with key answer guidance based on the hiring rubric.
                """

                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=prompt
                )

                # Display the output
                st.success("Guide Generated Successfully!")
                st.markdown("---")
                st.markdown(response.text)

                # Prepare PDF Download
                pdf_data = create_pdf(response.text)

                # Render Download Buttons Side-by-Side
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="📥 Download as PDF",
                        data=pdf_data,
                        file_name=f"{role_title.replace(' ', '_')}_Prep_Guide.pdf",
                        mime="application/pdf",
                        type="primary"
                    )

                with col_dl2:
                    st.download_button(
                        label="📄 Download as Text / Markdown",
                        data=response.text,
                        file_name=f"{role_title.replace(' ', '_')}_Prep_Guide.md",
                        mime="text/markdown"
                    )

            except Exception as e:
                st.error(f"Error generating guide: {str(e)}")
