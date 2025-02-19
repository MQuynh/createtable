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
            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$'  # yyyy-mm-dd hh:mm:ss
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
    
    # Kiểm tra nếu là số nguyên
    try:
        int(sample_value)
        return "DOUBLE PRECISION"
    except (ValueError, TypeError):
        pass

    # Kiểm tra nếu là số thực
    try:
        float(sample_value)
        return "DOUBLE PRECISION"
    except (ValueError, TypeError):
        pass

    # Kiểm tra nếu là ngày tháng dưới dạng chuỗi
    if isinstance(sample_value, str) and is_date_format(sample_value):
        return "DATE"

    # Nếu không khớp bất kỳ điều kiện nào, mặc định là TEXT
    return "TEXT"



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

# Tab 1: Nhập dữ liệu trực tiếp
with tab1:
    # Khu vực nhập liệu
    col1, col2 = st.columns(2)
    with col1:
        column_names_input = st.text_area("Tên cột", height=200, placeholder="Nhập danh sách tên cột, mỗi dòng một cột")
    with col2:
        sample_values_input = st.text_area("Giá trị mẫu", height=200, placeholder="Nhập danh sách giá trị mẫu, mỗi dòng một giá trị")

    # Hiển thị dữ liệu đã nhập (ngay cả khi không hợp lệ)
    column_names = column_names_input.strip().split("\n") if column_names_input.strip() else []
    sample_values = sample_values_input.strip().split("\n") if sample_values_input.strip() else []

    # Tạo bảng hiển thị dữ liệu đã nhập
    data_preview = {
        "STT": list(range(1, max(len(column_names), len(sample_values)) + 1)),
        "Tên cột": column_names + [""] * (max(len(column_names), len(sample_values)) - len(column_names)),
        "Giá trị mẫu": sample_values + [""] * (max(len(column_names), len(sample_values)) - len(sample_values)),
    }
    st.write("### Dữ liệu đã nhập:")
    st.table(pd.DataFrame(data_preview))

    # Kiểm tra tính hợp lệ của dữ liệu
    if len(column_names) != len(sample_values):
        st.error("Số lượng dòng giữa 'Tên cột' và 'Giá trị mẫu' không khớp!")
    else:
        # Xử lý dữ liệu khi người dùng nhấn nút
        if st.button("Tạo code SQL từ dữ liệu nhập"):
            if not column_names_input.strip() or not sample_values_input.strip():
                st.error("Vui lòng nhập đầy đủ cả danh sách tên cột và giá trị mẫu!")
            else:
                try:
                    # Tạo danh sách dữ liệu
                    data = [{"Tên cột": col_name.strip(), "Giá trị mẫu": sample_value.strip()} 
                            for col_name, sample_value in zip(column_names, sample_values)]

                    # Sinh câu lệnh SQL
                    sql_output = generate_create_table_sql(data, full_table_name)
                    st.subheader("Câu lệnh CREATE TABLE:")
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
                    st.error(f"Lỗi: {e}")

    # Hướng dẫn nhập liệu (chỉ trong tab nhập liệu trực tiếp)
    st.markdown("---")
    st.write("""
    ### Hướng dẫn nhập liệu
    Nhập danh sách **tên cột** và **giá trị mẫu** tương ứng theo cách song song:
    - Mỗi dòng của ô "Tên cột" tương ứng với một dòng của ô "Giá trị mẫu".
    - Số lượng dòng trong hai ô phải bằng nhau.
    - Định dạng INTEGER giá trị mẫu điền chữ INT, mặc định số ở định dạng DOUBLE PRECISION

    **Ví dụ:**
    - Ô "Tên cột":
        ```
        Ngân hàng
        Ngày giao dịch
        Số tiền
        ```
    - Ô "Giá trị mẫu":
        ```
        ACB
        01/01/2025
        8000
        ```
    """)


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
                # Đổi tên cột để đồng nhất
                df.columns = ["Tên cột", "Giá trị mẫu"]
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
