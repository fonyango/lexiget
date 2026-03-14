import os
from io import BytesIO

import requests
import streamlit as st

st.set_page_config(
    page_title="LexiGet",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BACKEND_URL = "http://localhost:8000/batch_extract"

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        .hero {
            padding: 1.4rem 1.6rem;
            border: 1px solid rgba(120,120,160,0.18);
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(18,24,38,0.95), rgba(28,36,58,0.95));
            margin-bottom: 1.2rem;
        }

        .hero-title {
            font-size: 2.3rem;
            font-weight: 700;
            line-height: 1.15;
            margin-bottom: 0.55rem;
        }

        .hero-sub {
            font-size: 1rem;
            color: #B8C0D4;
            line-height: 1.6;
            max-width: 800px;
        }

        .mini-card {
            padding: 1rem 1.1rem;
            border-radius: 18px;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            margin-bottom: 0.8rem;
        }

        .mini-label {
            font-size: 0.78rem;
            color: #9AA4BF;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.15rem;
        }

        .mini-value {
            font-size: 1.02rem;
            font-weight: 600;
            color: white;
        }

        .section-card {
            padding: 1.15rem;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.025);
            margin-bottom: 1rem;
        }

        .section-title {
            font-size: 1.15rem;
            font-weight: 650;
            margin-bottom: 0.8rem;
        }

        .hint {
            font-size: 0.92rem;
            color: #AEB7C9;
            line-height: 1.6;
        }

        .success-box {
            padding: 1rem 1.1rem;
            border-radius: 18px;
            background: rgba(22, 163, 74, 0.08);
            border: 1px solid rgba(22, 163, 74, 0.28);
            color: #D7F8DF;
        }

        .stDownloadButton button,
        .stButton button {
            width: 100%;
            border-radius: 14px;
            height: 3rem;
            font-weight: 600;
        }

        textarea {
            border-radius: 14px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "processed" not in st.session_state:
    st.session_state.processed = False
if "result_zip" not in st.session_state:
    st.session_state.result_zip = None
if "download_name" not in st.session_state:
    st.session_state.download_name = "results.zip"

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">LexiGet</div>
        <div class="hero-sub">
            Batch document extraction for ZIP files of PDFs. Upload your archive, define the extraction
            instructions, process everything in one run, and download a clean results package.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

input_mode = st.radio(
    "Choose input type", ["Single PDF", "ZIP of PDFs"], horizontal=True
)

document_type = st.selectbox(
    "Document type", ["Invoice", "Receipt", "Delivery Note", "Contract"]
)
st.caption("Choose the type of document you want LexiGet to extract.")

top_a, top_b, top_c = st.columns(3)
with top_a:
    st.markdown(
        """
        <div class="mini-card">
            <div class="mini-label">Accepted input</div>
            <div class="mini-value">ZIP or Individual PDF file</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with top_b:
    st.markdown(
        """
        <div class="mini-card">
            <div class="mini-label">Primary output</div>
            <div class="mini-value">results.zip</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with top_c:
    st.markdown(
        """
        <div class="mini-card">
            <div class="mini-label">Included exports</div>
            <div class="mini-value">summary, items, errors</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

left, right = st.columns([1.7, 0.95], gap="large")

with left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">Upload documents</div>', unsafe_allow_html=True
    )

    if input_mode == "Single PDF":
        uploaded_file = st.file_uploader(
            "Upload a PDF file", type=["pdf"], label_visibility="collapsed"
        )
        backend_url = "http://localhost:8000/extract_single"
    else:
        uploaded_file = st.file_uploader(
            "Upload a ZIP file", type=["zip"], label_visibility="collapsed"
        )
        backend_url = "http://localhost:8000/batch_extract"

    st.markdown(
        '<div class="section-title" style="margin-top:1rem;">Extraction instructions</div>',
        unsafe_allow_html=True,
    )

    user_prompt = st.text_area(
        "Extraction instructions",
        value="""Extract the following fields from each document and return valid JSON only""",
        height=120,
        label_visibility="collapsed",
        placeholder="Describe exactly what you want extracted...",
    )

    process = st.button("Process Documents")

    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown(
        f"""
    <div class="section-card">
        <div class="section-title">How it works</div>
        <div class="hint">
            1. Choose whether to upload a single PDF or a ZIP of PDFs.<br><br>
            2. Add extraction instructions.<br><br>
            3. LexiGet processes the document(s) through FastAPI backend.<br><br>
            4. Download a results ZIP containing CSV exports.
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="section-card">
            <div class="section-title">Output package</div>
            <div class="hint">
                • document_summary.csv<br>
                • document_items.csv<br>
                • document_errors.csv
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if process:
    if uploaded_file is None:
        st.error("Upload a file first.")
    else:
        with st.status("Processing documents...", expanded=True) as status:
            st.write("Reading documents...")

            content_type = (
                "application/pdf"
                if input_mode == "Single PDF"
                else "application/zip"
            )
            field_name = "file" if input_mode == "Single PDF" else "zip_file"

            files = {
                field_name: (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    content_type,
                )
            }
            data = {"document_type": document_type}

            st.write("Extracting fields...")
            response = requests.post(
                backend_url,
                files=files,
                data=data,
                timeout=300,
            )

            st.write("Creating CSV exports...")

            if response.status_code == 200:
                import os
                st.session_state.processed = True
                st.session_state.result_zip = response.content
                base_name = os.path.splitext(uploaded_file.name)[0]
                st.session_state.download_name = f"{base_name}_results.zip"

                status.update(label="Processing complete.", state="complete")
            else:
                st.session_state.processed = False
                st.session_state.result_zip = None
                status.update(label="Processing failed.", state="error")

                st.error(f"Backend error: {response.status_code}")
                try:
                    st.json(response.json())
                except Exception:
                    st.text(response.text)

if st.session_state.processed and st.session_state.result_zip is not None:
    st.markdown(
        """
        <div class="success-box">
            Processing complete. Your extraction package is ready to download.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    d1, d2 = st.columns([1.25, 1])
    with d1:
        st.download_button(
            label=f"Download {st.session_state.download_name}",
            data=st.session_state.result_zip,
            file_name=st.session_state.download_name,
            mime="application/zip",
        )
    with d2:
        st.info("This ZIP contains your generated CSV exports.")
