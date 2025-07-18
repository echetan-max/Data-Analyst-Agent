# pip install streamlit together pandas matplotlib python-docx openpyxl pymupdf easyocr pillow
# Run this code using: streamlit run da.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from docx import Document
import fitz
from PIL import Image
import easyocr
import together
import tempfile
import os

st.set_page_config(page_title="Data Analyst Agent", layout="wide")

# --- Hardcoded API Key ---
TOGETHER_API_KEY = "0357f4e3014d4d9183adb943e8d0aa0fe146034c20a12e408bd6a0ee748d45fe"
client = together.Together(api_key=TOGETHER_API_KEY)

# --- File Handlers ---
def read_txt(f): 
    return f.read().decode("utf-8", errors="ignore")

def read_csv(f): 
    return pd.read_csv(f)

def read_xlsx(f): 
    return pd.read_excel(f)

def read_docx(f):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(f.read()); path = tmp.name
    doc = Document(path)
    text = "\n".join(p.text for p in doc.paragraphs)
    os.unlink(path)
    return text

def read_pdf(f):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(f.read()); path = tmp.name
    pdf = fitz.open(path)
    text = "".join(page.get_text() for page in pdf)
    pdf.close()
    os.unlink(path)
    return text

def read_image(f):
    img_bytes = f.read()
    reader = easyocr.Reader(['en'], gpu=False)
    results = reader.readtext(img_bytes)
    return "\n".join(r[1] for r in results) or "[No text detected]"

def process_upload(uploaded_file):
    ext = uploaded_file.name.lower().split('.')[-1]
    if ext=="txt":      return read_txt(uploaded_file), None
    if ext=="csv":      return None, read_csv(uploaded_file)
    if ext=="xlsx":     return None, read_xlsx(uploaded_file)
    if ext=="docx":     return read_docx(uploaded_file), None
    if ext=="pdf":      return read_pdf(uploaded_file), None
    if ext in ["png","jpg","jpeg"]: return read_image(uploaded_file), None
    st.error("Unsupported file type!"); st.stop()

# --- Together AI query ---
@st.cache_data(show_spinner=False)
def llama4_query(prompt, context, api_key):
    full = f"Context:\n{context}\n\nQuestion:\n{prompt}"
    resp = together.Together(api_key=api_key).chat.completions.create(
        model="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        messages=[{"role":"user","content":full}]
    )
    return resp.choices[0].message.content.strip()

# --- App UI ---
st.title("Data Analyst Agent")
uploaded = st.file_uploader(
    "Upload (.txt, .csv, .xlsx, .docx, .pdf, .png, .jpg)", 
    type=["txt","csv","xlsx","docx","pdf","png","jpg","jpeg"]
)

data_text, data_df, context = None, None, ""
if uploaded:
    try:
        data_text, data_df = process_upload(uploaded)
        if data_df is not None:
            # clean & convert
            data_df = data_df.dropna(how='all').dropna(axis=1, how='all')
            for c in data_df.columns:
                data_df[c] = pd.to_numeric(data_df[c], errors="ignore")
            st.subheader("Table Preview")
            st.dataframe(data_df.head(10), use_container_width=True)
            context = data_df.head(10).to_string(index=False)
        else:
            st.subheader("Text Preview")
            st.code(data_text[:1000])
            context = data_text[:4000]
        st.success("File loaded. Ask questions below or visualize numeric data.")
    except Exception as e:
        st.error(f"Error loading file: {e}")

    st.divider()
    # Q&A
    st.header("Ask a Question")
    q = st.text_input("Your question about the data:")
    if st.button("Ask") and q.strip():
        if not context:
            st.warning("No data to analyze.")
        else:
            with st.spinner("Analyzing..."):
                ans = llama4_query(q, context, TOGETHER_API_KEY)
            st.markdown("**Answer:**")
            st.write(ans)

    # --- Visualization ---
    if data_df is not None:
        st.divider()
        st.header("Visualize Your Data")

        # Identify numeric and categorical columns
        numeric_cols   = data_df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = data_df.select_dtypes(include=['object', 'category']).columns.tolist()

        # Tabs for different plot types
        tab1, tab2, tab3 = st.tabs(["Histogram", "Bar Chart", "Scatter Plot"])

        # 1) Histogram
        with tab1:
            if not numeric_cols:
                st.info("No numeric columns available for histogram.")
            else:
                hist_col = st.selectbox("Select numeric column", numeric_cols, key="hist_col")
                bins     = st.slider("Number of bins", 5, 100, 30, key="hist_bins")
                if st.button("Plot Histogram", key="hist_btn"):
                    fig, ax = plt.subplots()
                    ax.hist(data_df[hist_col].dropna(), bins=bins, edgecolor='black')
                    ax.set_title(f"Histogram of {hist_col}", fontsize=14)
                    ax.set_xlabel(hist_col, fontsize=12)
                    ax.set_ylabel("Frequency", fontsize=12)
                    st.pyplot(fig)

        # 2) Bar Chart
        with tab2:
            if not categorical_cols or not numeric_cols:
                st.info("Need at least one categorical and one numeric column for a bar chart.")
            else:
                cat_col = st.selectbox("Categorical column", categorical_cols, key="bar_cat")
                num_col = st.selectbox("Numeric column", numeric_cols, key="bar_num")
                agg_fcn = st.selectbox("Aggregation function", ["mean", "sum", "count"], key="bar_agg")
                if st.button("Plot Bar Chart", key="bar_btn"):
                    grouped = data_df.groupby(cat_col)[num_col]
                    if agg_fcn == "mean":
                        plot_data = grouped.mean()
                    elif agg_fcn == "sum":
                        plot_data = grouped.sum()
                    else:
                        plot_data = grouped.count()
                    fig, ax = plt.subplots(figsize=(8,4))
                    plot_data.plot(kind='bar', ax=ax, edgecolor='black')
                    ax.set_title(f"{agg_fcn.title()} of {num_col} by {cat_col}", fontsize=14)
                    ax.set_xlabel(cat_col, fontsize=12)
                    ax.set_ylabel(f"{agg_fcn.title()} of {num_col}", fontsize=12)
                    plt.xticks(rotation=45, ha='right')
                    st.pyplot(fig)

        # 3) Scatter Plot
        with tab3:
            if len(numeric_cols) < 2:
                st.info("Need at least two numeric columns for scatter plot.")
            else:
                x_col = st.selectbox("X axis", numeric_cols, key="scatter_x")
                y_options = [c for c in numeric_cols if c != x_col]
                y_col = st.selectbox("Y axis", y_options, key="scatter_y")
                if st.button("Plot Scatter", key="scatter_btn"):
                    fig, ax = plt.subplots()
                    ax.scatter(data_df[x_col], data_df[y_col], alpha=0.7, edgecolor='w')
                    ax.set_title(f"Scatter: {y_col} vs {x_col}", fontsize=14)
                    ax.set_xlabel(x_col, fontsize=12)
                    ax.set_ylabel(y_col, fontsize=12)
                    st.pyplot(fig)
