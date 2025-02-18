import streamlit as st
import pandas as pd
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

# Hàm tạo câu lệnh CREATE TABLE từ dữ liệu nhập
def generate_create_table_sql(data, table_name):
    table_name = normalize_column_name(table_name)
    sql = f"CREATE TABLE {table_name} (\n"
    sql += "    id SERIAL PRIMARY KEY,\n"

    for row in data:
        column_name = normalize_column_name(row["Tên cột"])
        data_type = infer_data_type(row["Giá trị mẫu"], row["Tên cột"])
        sql += f"    {column_name} {data_type},\n"

    sql = sql.rstrip(",\n") + "\n);"
    return sql

# Giao diện Streamlit
st.title("Tạo câu lệnh CREATE TABLE từ dữ liệu nhập hoặc tệp")

# Nhập tên bảng (không bắt buộc)
table_name = st.text_input("Nhập tên bảng (tùy chọn, mặc định là 'table_name')", placeholder="Ví dụ: my_table")

# Nếu không nhập, sử dụng tên bảng mặc định
if not table_name.strip():
    table_name = "table_name"

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

    # Xử lý dữ liệu khi người dùng nhấn nút
    if st.button("Tạo câu lệnh SQL từ dữ liệu nhập"):
        if not column_names_input.strip() or not sample_values_input.strip():
            st.error("Vui lòng nhập đầy đủ cả danh sách tên cột và giá trị mẫu!")
        else:
            try:
                # Chuyển dữ liệu từ text area thành danh sách
                column_names = column_names_input.strip().split("\n")
                sample_values = sample_values_input.strip().split("\n")

                # Kiểm tra số lượng dòng
                if len(column_names) != len(sample_values):
                    st.error("Số lượng dòng giữa 'Tên cột' và 'Giá trị mẫu' không khớp!")
                else:
                    # Tạo danh sách dữ liệu
                    data = [{"Tên cột": col_name.strip(), "Giá trị mẫu": sample_value.strip()} 
                            for col_name, sample_value in zip(column_names, sample_values)]

                    # Sinh câu lệnh SQL
                    sql_output = generate_create_table_sql(data, table_name)
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
                sql_output = generate_create_table_sql(data, table_name)
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
            st.error(f"Lỗi khi xử lý tệp: {e}")

# Hướng dẫn (đưa xuống cuối)
st.markdown("---")
st.write("""
### Hướng dẫn nhập liệu
Nhập danh sách **tên cột** và **giá trị mẫu** tương ứng theo cách song song:
- Mỗi dòng của ô "Tên cột" tương ứng với một dòng của ô "Giá trị mẫu".
- Số lượng dòng trong hai ô phải bằng nhau.

**Ví dụ:**
- Ô "Tên cột":
    ```
    Họ và tên
    Ngày sinh
    Điểm trung bình
    ```
- Ô "Giá trị mẫu":
    ```
    Nguyễn Văn A
    01/01/2000
    8.5
    ```

---

### Hướng dẫn đính kèm tệp
Tải lên tệp Excel (.xlsx) hoặc CSV (.csv) với cấu trúc:
- **Cột 1**: Tên cột.
- **Cột 2**: Giá trị mẫu.

**Ví dụ:**
| Tên cột         | Giá trị mẫu   |
|------------------|---------------|
| Họ và tên       | Nguyễn Văn A  |
| Ngày sinh       | 01/01/2000    |
| Điểm trung bình | 8.5           |
""")
