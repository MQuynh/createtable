import streamlit as st
import pandas as pd
import unicodedata
import re

# Các hàm chuẩn hóa và xử lý dữ liệu (giữ nguyên như trước)
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
            r'^\d{2}/\d{2}/\d{4}$',          # dd/mm/yyyy
            r'^\d{2}-\d{2}-\d{4}$',          # dd-mm-yyyy
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'  # yyyy-mm-dd hh:mm:ss
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

def generate_create_table_sql_from_manual_input(columns):
    table_name = "manual_table"
    sql = f"CREATE TABLE {table_name} (\n"
    sql += "    id SERIAL PRIMARY KEY,\n"

    for col in columns:
        column_name = normalize_column_name(col["Tên cột"])
        data_type = infer_data_type(col["Giá trị mẫu"], col["Tên cột"])
        sql += f"    {column_name} {data_type},\n"

    sql = sql.rstrip(",\n") + "\n);"
    return sql

# Giao diện Streamlit
st.title("Tạo câu lệnh CREATE TABLE từ dữ liệu nhập tay hoặc file")

# Lựa chọn cách nhập liệu
option = st.radio("Chọn cách nhập liệu:", ["Nhập tay", "Tải lên file"])

if option == "Tải lên file":
    st.write("### Tải lên file Excel hoặc CSV")
    uploaded_file = st.file_uploader("Tải lên file", type=["xlsx", "csv"])

    if uploaded_file is not None:
        try:
            # Đọc file và sinh câu lệnh SQL
            sql_output = generate_create_table_sql(uploaded_file)
            st.subheader("Câu lệnh CREATE TABLE:")
            st.code(sql_output, language="sql")

            # Nút tải xuống file SQL
            sql_file_name = "create_table.sql"
            st.download_button(
                label="Tải xuống file SQL",
                data=sql_output,
                file_name=sql_file_name,
                mime="text/sql",
            )
        except Exception as e:
            st.error(f"Lỗi: {e}")

elif option == "Nhập tay":
    st.write("### Nhập thông tin cột và giá trị mẫu")

    # Tạo danh sách để lưu các cột
    columns = []

    # Form nhập liệu
    with st.form("manual_input_form"):
        num_columns = st.number_input("Số lượng cột", min_value=1, step=1, value=1)
        for i in range(num_columns):
            st.write(f"#### Cột {i + 1}")
            col_name = st.text_input(f"Tên cột {i + 1}", key=f"col_name_{i}")
            sample_value = st.text_input(f"Giá trị mẫu {i + 1}", key=f"sample_value_{i}")
            columns.append({"Tên cột": col_name, "Giá trị mẫu": sample_value})

        # Nút submit
        submitted = st.form_submit_button("Tạo câu lệnh SQL")

    # Xử lý khi người dùng nhấn submit
    if submitted:
        try:
            sql_output = generate_create_table_sql_from_manual_input(columns)
            st.subheader("Câu lệnh CREATE TABLE:")
            st.code(sql_output, language="sql")

            # Nút tải xuống file SQL
            sql_file_name = "create_table.sql"
            st.download_button(
                label="Tải xuống file SQL",
                data=sql_output,
                file_name=sql_file_name,
                mime="text/sql",
            )
        except Exception as e:
            st.error(f"Lỗi: {e}")
