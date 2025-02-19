import streamlit as st
import pandas as pd
import unicodedata
import re
import datetime

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
            r'^\d{2}-\d{2}-\d{2}$'           # dd-mm-yy
        ]
        for pattern in date_patterns:
            if re.match(pattern, value):
                return True
    return False

# Hàm suy luận kiểu dữ liệu
def infer_data_type(sample_value, column_name):
    # Nếu tên cột chứa từ "ngay", suy luận kiểu DATE
    if "ngay" in column_name.lower():
        return "DATE"
    
    # Kiểm tra nếu giá trị mẫu là chuỗi "INT"
    if isinstance(sample_value, str) and sample_value.strip().upper() == "INT":
        return "INTEGER"
    
    # Kiểm tra nếu giá trị mẫu là kiểu datetime
    if isinstance(sample_value, pd.Timestamp) or isinstance(sample_value, datetime.datetime):
        return "DATE"
        
    # Chuyển đổi các giá trị mẫu thành số nếu có thể
    df['Giá trị mẫu'] = pd.to_numeric(df['Giá trị mẫu'], errors='ignore')
    
    # Loại bỏ các ký tự phân cách hàng nghìn (.,) và kiểm tra kiểu số
    if isinstance(sample_value, str):
        normalized_value = sample_value.replace(",", "").replace(".", "")
        try:
            # Kiểm tra nếu là số nguyên (integer)
            int(normalized_value)
            return "INTEGER"
        except ValueError:
            pass

        try:
            # Kiểm tra nếu là số thực (floating point)
            float(normalized_value)
            return "DOUBLE PRECISION"
        except ValueError:
            pass

    # Kiểm tra nếu là ngày tháng dưới dạng chuỗi
    if isinstance(sample_value, str) and is_date_format(sample_value):
        return "DATE"

    # Nếu không khớp bất kỳ điều kiện nào, mặc định là TEXT
    return "TEXT"

# Hàm chuẩn hóa và xử lý dữ liệu sau khi tải lên tệp
def process_uploaded_file(df):
    # Chuẩn hóa lại dữ liệu từ file Excel
    for index, row in df.iterrows():
        # Kiểm tra và ép kiểu đối với giá trị mẫu
        sample_value = row['Giá trị mẫu']
        if isinstance(sample_value, str):
            # Kiểm tra xem giá trị có phải là số không (loại bỏ dấu phân cách nghìn)
            normalized_value = sample_value.replace(",", "").replace(".", "")
            if normalized_value.isdigit():
                df.at[index, 'Giá trị mẫu'] = int(normalized_value)
            else:
                try:
                    # Kiểm tra nếu giá trị có thể là một số thực
                    df.at[index, 'Giá trị mẫu'] = float(normalized_value)
                except ValueError:
                    pass  # Nếu không phải số, giữ lại giá trị ban đầu
    
    # Đảm bảo các cột có kiểu dữ liệu phù hợp sau khi xử lý
    return df

# Hàm tạo Code CREATE TABLE từ dữ liệu nhập
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

# Nhập tên schema (không bắt buộc)
schema_name = st.text_input("Nhập tên schema (tùy chọn, mặc định là 'public')", placeholder="Ví dụ: subpublic")

# Nếu không nhập, sử dụng schema mặc định
if not schema_name.strip():
    schema_name = "public"

# Nhập tên bảng (không bắt buộc)
table_name = st.text_input("Nhập tên bảng (tùy chọn, mặc định là 'table_name')", placeholder="Ví dụ: my_table")

# Nếu không nhập, sử dụng tên bảng mặc định
if not table_name.strip():
    table_name = "table_name"

# Chuẩn hóa tên schema và tên bảng
schema_name = normalize_column_name(schema_name)
table_name = normalize_column_name(table_name)

# Tên bảng đầy đủ với schema
full_table_name = f"{schema_name}.{table_name}"

# Tab điều hướng
tab1, tab2 = st.tabs(["Nhập dữ liệu trực tiếp", "Đính kèm tệp"])

# Tab 2: Đính kèm tệp
with tab2:
    # Khu vực tải lên tệp
    uploaded_file = st.file_uploader("Tải lên tệp Excel hoặc CSV", type=["xlsx", "csv"])

    if uploaded_file is not None:
        try:
            # Đọc dữ liệu từ tệp
            if uploaded_file.name.endswith(".csv"):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)

            # Kiểm tra định dạng tệp
            if df.shape[1] < 2:
                st.error("Tệp phải có ít nhất 2 cột: 'Tên cột' và 'Giá trị mẫu'.")
            else:
                # Chuẩn hóa và xử lý dữ liệu
                df.columns = ["Tên cột", "Giá trị mẫu"]
                df = process_uploaded_file(df)  # Chạy hàm chuẩn hóa dữ liệu

                # Tạo dữ liệu từ dataframe đã chuẩn hóa
                data = df.to_dict(orient="records")

                # Sinh câu lệnh SQL
                sql_output = generate_create_table_sql(data, full_table_name)
                st.subheader("Code SQL CREATE TABLE:")
                st.code(sql_output, language="sql")

                # Nút tải xuống file SQL
                sql_file_name = f"{table_name}.sql"
                st.download_button(
                    label="Tải xuống file SQL",
                    data=sql_output,
                    file_name=sql_file_name,
                    mime="text/sql",
                )
        except Exception as e:
            st.error(f"Lỗi khi xử lý tệp: {e}")

    # Hướng dẫn đính kèm tệp (chỉ trong tab đính kèm tệp)
    st.markdown("---")
    st.write("""
    ### Hướng dẫn đính kèm tệp
    Tải lên tệp Excel (.xlsx) hoặc CSV (.csv) với cấu trúc:
    - **Cột 1**: Tên cột.
    - **Cột 2**: Giá trị mẫu.
    - Định dạng INTEGER giá trị mẫu điền chữ INT, mặc định số ở định dạng DOUBLE PRECISION

    **Ví dụ:**
    | Tên cột         | Giá trị mẫu   |
    |------------------|---------------|
    | Ngân hàng       | ACB  |
    | Ngày giao dịch       | 01/01/2025    |
    | Số tiền | 1000           |
    """)
