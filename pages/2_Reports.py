import io
import pandas as pd
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

st.set_page_config(page_title="Reports", layout="wide")
st.title("Reports")

st.info("Next: we’ll wire this page to your live scenario inputs. For now, this is a working export skeleton.")


def make_sample_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"Metric": "AOV", "Value": 249.00},
        {"Metric": "COGS", "Value": 65.00},
        {"Metric": "Gross Profit / Order", "Value": 152.12},
        {"Metric": "Target Ratio", "Value": 12},
        {"Metric": "Max CAC", "Value": 16.88},
    ])


def export_excel(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Scenario")
    return buffer.getvalue()


def export_pdf(df: pd.DataFrame, title: str = "White Owl Scenario Report") -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, title)
    y -= 28

    c.setFont("Helvetica", 11)
    c.drawString(72, y, "Summary Metrics")
    y -= 18

    c.setFont("Helvetica", 10)
    for _, row in df.iterrows():
        c.drawString(72, y, f"{row['Metric']}: {row['Value']}")
        y -= 14
        if y < 72:
            c.showPage()
            y = height - 72
            c.setFont("Helvetica", 10)

    c.showPage()
    c.save()
    return buffer.getvalue()


df = make_sample_df()
st.dataframe(df, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    xlsx = export_excel(df)
    st.download_button("Download Excel", data=xlsx, file_name="white_owl_report.xlsx")

with col2:
    pdf = export_pdf(df)
    st.download_button("Download PDF", data=pdf, file_name="white_owl_report.pdf")
