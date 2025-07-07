import streamlit as st
import pandas as pd
import unicodedata
import re
import datetime
from io import BytesIO

# Hiển thị logo ở đầu giao diện
st.image("logo.png", use_container_width=False, width=150)  # width: điều chỉnh kích thước logo

# Hàm chuẩn hóa tên cột
def normalize_column_name(column_name):
    column_name = column_name.replace('đ', 'd').replace('Đ', 'd')
    column_name = unicodedata.normalize('NFKD', column_name)
    column_name = ''.join(c for c in column_name if not unicodedata.combining(c))
    column_name = column_name.replace('%', 'pc')
    column_name = re.sub(r'\W+', '_', column_name.strip().lower())
    return column_name

# Hàm kiểm tra định dạng ngày
def is_date_format(value):
    if isinstance(value, str):
        value = value.strip()
        date_patterns = [
            r'^\d{2}/\d{2}/\d{4}$',          # dd/mm/yyyy
            r'^\d{2}-\d{2}-\d{4}$',          # dd-mm-yyyy
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$',  # yyyy-mm-dd hh:mm:ss
            r'^\d{2}/\d{2}/\d{2}$',          # dd/mm/yy
            r'^\d{2}-\d{2}-\d{2}$',          # dd-mm-yy
            r'^\d{4}/\d{2}/\d{2}$',          # yyyy/mm/dd
            r'^\d{4}-\d{2}-\d{2}$'           # yyyy-mm-dd
        ]
        for pattern in date_patterns:
            if re.match(pattern, value):
                return True
    return False


# Hàm suy luận kiểu dữ liệu
def infer_data_type(sample_value, column_name):
    if "ngay" in column_name.lower():
        return "DATE"
    if isinstance(sample_value, str) and sample_value.strip().upper() == "INT":
        return "INTEGER"
    if isinstance(sample_value, pd.Timestamp) or isinstance(sample_value, datetime.datetime):
        return "DATE"
    try:
        int(sample_value)
        return "DOUBLE PRECISION"
    except (ValueError, TypeError):
        pass
    try:
        float(sample_value)
        return "DOUBLE PRECISION"
    except (ValueError, TypeError):
        pass
    if isinstance(sample_value, str) and is_date_format(sample_value):
        return "DATE"
    return "TEXT"

# Hàm tạo Code CREATE TABLE
def generate_create_table_sql(data, full_table_name):
    sql = f"CREATE TABLE {full_table_name} (\n"
    sql += "    id SERIAL PRIMARY KEY,\n"
    for row in data:
        column_name = normalize_column_name(row["Tên cột"])
        data_type = infer_data_type(row["Giá trị mẫu"], row["Tên cột"])
        sql += f"    {column_name} {data_type},\n"
    sql = sql.rstrip(",\n") + "\n);"
    return sql

# Giao diện Streamlit
st.title("Tạo Code SQL CREATE TABLE")

schema_name = st.text_input("Nhập tên schema", placeholder="Ví dụ: subpublic") or "public"
table_name = st.text_input("Nhập tên bảng", placeholder="Ví dụ: my_table") or "table_name"

schema_name = normalize_column_name(schema_name)
table_name = normalize_column_name(table_name)
full_table_name = f"{schema_name}.{table_name}"
tab1, tab2 = st.tabs(["Nhập dữ liệu trực tiếp", "Đính kèm tệp"])

with tab1:
    col1, col2 = st.columns(2)
    column_names_input = col1.text_area("Tên cột", height=200)
    sample_values_input = col2.text_area("Giá trị mẫu", height=200)

    column_names = column_names_input.strip().split("\n") if column_names_input.strip() else []
    sample_values = sample_values_input.strip().split("\n") if sample_values_input.strip() else []

    data_preview = {
        "Tên cột": column_names + [""] * (max(len(column_names), len(sample_values)) - len(column_names)),
        "Giá trị mẫu": sample_values + [""] * (max(len(column_names), len(sample_values)) - len(sample_values)),
    }
    st.write("### Dữ liệu đã nhập:")
    st.table(pd.DataFrame(data_preview))

    if len(column_names) == len(sample_values) and column_names:
        if st.button("Tạo code SQL và xuất Excel"):
            data = [{"Tên cột": col_name.strip(), "Giá trị mẫu": sample_value.strip()} 
                    for col_name, sample_value in zip(column_names, sample_values)]
            
            sql_output = generate_create_table_sql(data, full_table_name)
            st.subheader("Câu lệnh CREATE TABLE:")
            st.code(sql_output, language="sql")

            sql_file_name = f"{table_name}.sql"
            st.download_button("Tải xuống file SQL", sql_output, sql_file_name, "text/sql", key="download_sql")

            normalized_columns = [normalize_column_name(col) for col in column_names]
            df_export = pd.DataFrame(columns=["action_type", "id"] + normalized_columns)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name="Converted Data")
            output.seek(0)

            excel_file_name = f"{table_name}_converted.xlsx"
            st.download_button("Tải xuống file Excel", output.getvalue(), excel_file_name, 
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                               key="download_excel")

with tab2:
    uploaded_file = st.file_uploader("Tải lên tệp Excel hoặc CSV", type=["xlsx", "csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        if df.shape[1] >= 2:
            df.columns = ["Tên cột", "Giá trị mẫu"]
            data = df.to_dict(orient="records")
            sql_output = generate_create_table_sql(data, full_table_name)
            st.subheader("Code SQL CREATE TABLE:")
            st.code(sql_output, language="sql")

            sql_file_name = f"{table_name}.sql"
            st.download_button("Tải xuống file SQL", sql_output, sql_file_name, "text/sql", key="download_sql_file")

            normalized_columns = [normalize_column_name(col) for col in df["Tên cột"]]
            df_export = pd.DataFrame(columns=["action_type", "id"] + normalized_columns)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name="Converted Data")
            output.seek(0)

            excel_file_name = f"{table_name}_converted.xlsx"
            st.download_button("Tải xuống file Excel", output.getvalue(), excel_file_name, 
                               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                               key="download_excel_file")
        else:
            st.error("Tệp không hợp lệ. Định dạng phải có ít nhất 2 cột: 'Tên cột' và 'Giá trị mẫu'.")
