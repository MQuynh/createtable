import streamlit as st
import pandas as pd
import os
import unicodedata
import re

def normalize_column_name(column_name):
    column_name = column_name.replace('đ', 'd').replace('Đ', 'd')
    column_name = unicodedata.normalize('NFKD', column_name)
    column_name = ''.join(c for c in column_name if not unicodedata.combining(c))
    column_name = column_name.replace('%', 'pc')
    column_name = re.sub(r'\W+', '_', column_name.strip().lower())
    return column_name

def is_date_format(value):
    if isinstance(value, str):
        value = value.strip()
        date_patterns = [
            r'^\d{2}/\d{2}/\d{4}$',
            r'^\d{2}-\d{2}-\d{4}$',
        ]
        for pattern in date_patterns:
            if re.match(pattern, value):
                return True
    return False

def infer_data_type(sample_value, column_name):
    if "ngay" in column_name.lower():
        return "DATE"
    if isinstance(sample_value, str) and sample_value.strip().upper() == "INT":
        return "INTEGER"
    elif pd.isna(sample_value):
        return "TEXT"
    elif isinstance(sample_value, str) and is_date_format(sample_value):
        return "DATE"
    elif isinstance(sample_value, (int, float)):
        return "DOUBLE PRECISION"
    elif isinstance(sample_value, str):
        return "TEXT"
    else:
        return "TEXT"

def generate_create_table_sql(file):
    table_name = "uploaded_table"

    # Xác định định dạng file và đọc dữ liệu
    if file.name.endswith('.xlsx'):
        df = pd.read_excel(file, sheet_name=0)
    elif file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        raise ValueError("Định dạng file không được hỗ trợ. Vui lòng tải lên file Excel (.xlsx) hoặc CSV (.csv).")

    required_columns = ["Tên cột", "Giá trị mẫu"]
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Thiếu cột bắt buộc: {col}")

    sql = f"CREATE TABLE {table_name} (\n"
    sql += "    id SERIAL PRIMARY KEY,\n"

    for _, row in df.iterrows():
        original_column_name = row["Tên cột"]
        sample_value = row["Giá trị mẫu"]
        column_name = normalize_column_name(original_column_name)
        data_type = infer_data_type(sample_value, original_column_name)
        sql += f"    {column_name} {data_type},\n"

    sql = sql.rstrip(",\n") + "\n);"
    return sql

# Giao diện Streamlit
st.title("Tạo câu lệnh CREATE TABLE từ file Excel hoặc CSV")
st.write(
    """
    Ứng dụng này cho phép bạn tải lên file Excel (.xlsx) hoặc CSV (.csv) chứa thông tin cột và giá trị mẫu,
    sau đó tự động tạo câu lệnh SQL để tạo bảng.
    """
)

uploaded_file = st.file_uploader("Tải lên file Excel hoặc CSV", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        # Chuyển đối tượng UploadedFile thành file-like object
        sql_output = generate_create_table_sql(uploaded_file)
        st.subheader("Câu lệnh CREATE TABLE:")
        st.code(sql_output, language="sql")

        # Tải xuống file SQL
        sql_file_name = "create_table.sql"
        st.download_button(
            label="Tải xuống file SQL",
            data=sql_output,
            file_name=sql_file_name,
            mime="text/sql",
        )
    except Exception as e:
        st.error(f"Lỗi: {e}")
