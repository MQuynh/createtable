import streamlit as st
import unicodedata
import re

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
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'  # yyyy-mm-dd hh:mm:ss
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
    elif sample_value == "":
        return "TEXT"
    elif isinstance(sample_value, str) and is_date_format(sample_value):
        return "DATE"
    elif isinstance(sample_value, (int, float)):
        return "DOUBLE PRECISION"
    elif isinstance(sample_value, str):
        return "TEXT"
    else:
        return "TEXT"

# Hàm tạo câu lệnh CREATE TABLE từ dữ liệu nhập hàng loạt
def generate_create_table_sql_from_bulk_input(data):
    table_name = "bulk_table"
    sql = f"CREATE TABLE {table_name} (\n"
    sql += "    id SERIAL PRIMARY KEY,\n"

    for row in data:
        column_name = normalize_column_name(row["Tên cột"])
        data_type = infer_data_type(row["Giá trị mẫu"], row["Tên cột"])
        sql += f"    {column_name} {data_type},\n"

    sql = sql.rstrip(",\n") + "\n);"
    return sql

# Giao diện Streamlit
st.title("Tạo câu lệnh CREATE TABLE từ dữ liệu nhập hàng loạt")

# Hướng dẫn nhập liệu
st.write("""
### Hướng dẫn nhập liệu:
Nhập dữ liệu hàng loạt với định dạng sau:
- Mỗi dòng tương ứng với một cột.
- Mỗi dòng gồm **Tên cột** và **Giá trị mẫu**, cách nhau bởi dấu phẩy (,).

**Ví dụ:**
Tên cột 1, Giá trị mẫu 1
Tên cột 2, Giá trị mẫu 2
Tên cột 3, Giá trị mẫu 3
""")

# Khu vực nhập liệu
bulk_input = st.text_area("Nhập dữ liệu hàng loạt", height=200, placeholder="Tên cột 1, Giá trị mẫu 1\nTên cột 2, Giá trị mẫu 2")

# Xử lý dữ liệu khi người dùng nhấn nút
if st.button("Tạo câu lệnh SQL"):
    if not bulk_input.strip():
        st.error("Vui lòng nhập dữ liệu!")
    else:
        try:
            # Chuyển dữ liệu từ text area thành danh sách các cột
            rows = bulk_input.strip().split("\n")
            data = []
            for row in rows:
                parts = row.split(",", 1)  # Tách thành 2 phần: Tên cột và Giá trị mẫu
                if len(parts) != 2:
                    raise ValueError(f"Dòng không hợp lệ: {row}")
                col_name = parts[0].strip()
                sample_value = parts[1].strip()
                data.append({"Tên cột": col_name, "Giá trị mẫu": sample_value})

            # Sinh câu lệnh SQL
            sql_output = generate_create_table_sql_from_bulk_input(data)
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
