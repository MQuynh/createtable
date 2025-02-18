import streamlit as st
import pandas as pd
import re

# Hàm chuẩn hóa tên cột
def normalize_column_name(column_name):
    column_name = column_name.strip()
    column_name = column_name.lower()
    column_name = re.sub(r"[^\w\s]", "", column_name)  # Loại bỏ ký tự đặc biệt
    column_name = re.sub(r"\s+", "_", column_name)  # Thay khoảng trắng bằng dấu gạch dưới
    return column_name

# Hàm kiểm tra định dạng ngày
def is_date_format(value):
    if isinstance(value, str):
        value = value.strip()  # Loại bỏ khoảng trắng thừa
        date_patterns = [
            r'^\d{2}/\d{2}/\d{4}$',          # dd/mm/yyyy
            r'^\d{2}-\d{2}-\d{4}$',          # dd-mm-yyyy
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'  # yyyy-mm-dd hh:mm:ss
        ]
        for pattern in date_patterns:
            if re.match(pattern, value):
                return True
    return False

# Hàm suy luận kiểu dữ liệu
def infer_data_type(sample_value, column_name):
    if "ngay" in column_name.lower():
        # Ưu tiên kiểm tra định dạng ngày
        if is_date_format(sample_value):
            return "DATE"
    if isinstance(sample_value, str) and sample_value.strip().upper() == "INT":
        return "INTEGER"
    elif pd.isna(sample_value):
        return "TEXT"
    elif isinstance(sample_value, str) and is_date_format(sample_value):
        # Nếu giá trị là định dạng ngày, trả về kiểu DATE
        return "DATE"
    elif isinstance(sample_value, (int, float)):
        return "DOUBLE PRECISION"
    elif isinstance(sample_value, str):
        return "TEXT"
    else:
        return "TEXT"

# Hàm chính để tạo câu lệnh SQL
def create_table_sql(df, table_name):
    sql = f"CREATE TABLE {table_name} (\n"
    for _, row in df.iterrows():
        original_column_name = row["Tên cột"]
        sample_value = row["Giá trị mẫu"]
        column_name = normalize_column_name(original_column_name)
        data_type = infer_data_type(sample_value, original_column_name)
        
        # In giá trị để kiểm tra
        print(f"Cột: {original_column_name}, Giá trị mẫu: {sample_value}, Kiểu dữ liệu: {data_type}")
        
        sql += f"    {column_name} {data_type},\n"
    sql = sql.rstrip(",\n") + "\n);"
    return sql

# Giao diện Streamlit
st.title("Tạo câu lệnh SQL từ file Excel")

# Upload file
uploaded_file = st.file_uploader("Tải lên file Excel", type=["xlsx"])

if uploaded_file:
    try:
        # Đọc file
        df = pd.read_excel(uploaded_file)
        st.write("Xem trước dữ liệu:")
        st.dataframe(df)

        # Nhập tên bảng
        table_name = st.text_input("Nhập tên bảng:", "ten_bang")

        if st.button("Tạo câu lệnh SQL"):
            # Tạo câu lệnh SQL
            sql = create_table_sql(df, table_name)
            st.subheader("Câu lệnh SQL:")
            st.code(sql, language="sql")

            # Tải xuống câu lệnh SQL
            st.download_button(
                label="Tải xuống câu lệnh SQL",
                data=sql,
                file_name=f"{table_name}.sql",
                mime="text/sql"
            )
    except Exception as e:
        st.error(f"Lỗi khi xử lý file: {e}")
