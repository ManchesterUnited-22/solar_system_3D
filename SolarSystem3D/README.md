# 🌌 Solar System 3D

## 1. Giới thiệu

**Solar System 3D** là dự án mô phỏng hệ Mặt Trời trong không gian ba chiều, được xây dựng bằng Python và OpenGL.

Dự án giúp minh họa vị trí, quỹ đạo và chuyển động của các hành tinh xung quanh Mặt Trời, đồng thời áp dụng các kiến thức đồ họa máy tính như mô hình hóa 3D, phép biến đổi hình học và phép chiếu phối cảnh.

## 2. Mục tiêu

- Mô phỏng Mặt Trời và 8 hành tinh trong hệ Mặt Trời.
- Xây dựng quỹ đạo chuyển động của các hành tinh.
- Áp dụng các phép biến đổi hình học trong không gian 3D.
- Tìm hiểu cách sử dụng thư viện OpenGL với Python.
- Phát triển các chức năng điều khiển và quan sát mô hình.

## 3. Công nghệ sử dụng

- **Python:** Ngôn ngữ lập trình chính.
- **PyOpenGL:** Thư viện đồ họa OpenGL dành cho Python.
- **GLFW:** Quản lý cửa sổ và sự kiện bàn phím.
- **NumPy:** Hỗ trợ tính toán số học và tọa độ.

## 4. Cấu trúc thư mục

```text
SolarSystem3D/
├── src/
│   ├── main.py
│   ├── planet.py
│   ├── orbit.py
│   ├── animation.py
│   └── camera.py
├── assets/
│   └── textures/
├── requirements.txt
├── README.md
└── .gitignore
```

### Chức năng các file

- `main.py`: Khởi tạo cửa sổ OpenGL và điều phối chương trình.
- `planet.py`: Lưu thông tin, kích thước, màu sắc và vẽ các hành tinh.
- `orbit.py`: Vẽ các đường quỹ đạo.
- `animation.py`: Tính toán và cập nhật chuyển động của các hành tinh.
- `camera.py`: Quản lý góc nhìn và vị trí camera.
- `assets/textures/`: Lưu hình ảnh dùng làm texture cho các hành tinh.
- `requirements.txt`: Danh sách thư viện cần cài đặt.

## 5. Cài đặt môi trường

### Yêu cầu

- Python 3.
- Visual Studio Code hoặc IDE hỗ trợ Python.
- Hệ điều hành Windows, Linux hoặc macOS có hỗ trợ OpenGL.

### Bước 1: Tải mã nguồn

Clone repository hoặc tải project về máy.

```bash
git clone <repository-url>
cd SolarSystem3D
```

Nếu chưa sử dụng Git, có thể mở trực tiếp thư mục project trong Visual Studio Code.

### Bước 2: Cài đặt thư viện

Mở Terminal tại thư mục gốc của project và chạy:

```bash
py -m pip install -r requirements.txt
```

Nếu sử dụng Linux hoặc macOS, có thể dùng:

```bash
python3 -m pip install -r requirements.txt
```

## 6. Khởi chạy chương trình

Từ thư mục gốc `SolarSystem3D`, chạy:

```bash
py src/main.py
```

Trên Linux hoặc macOS:

```bash
python3 src/main.py
```

Cửa sổ mô phỏng sẽ xuất hiện nếu môi trường và các thư viện đã được cài đặt đúng.

## 7. Các kiến thức đồ họa máy tính áp dụng

### 7.1. Mô hình hóa 3D

Sử dụng các hình cầu để biểu diễn Mặt Trời và các hành tinh.

### 7.2. Phép biến đổi hình học

- **Tịnh tiến:** Đưa hành tinh đến vị trí trên quỹ đạo.
- **Quay:** Mô phỏng chuyển động quanh Mặt Trời và chuyển động tự quay.
- **Co giãn:** Thay đổi kích thước của các đối tượng.

### 7.3. Thuật toán quỹ đạo

Tính tọa độ của hành tinh trên quỹ đạo elip bằng các hàm lượng giác. Mặt Trời
được đặt tại một tiêu điểm của mỗi quỹ đạo:

```python
x = semi_major_axis * cos(angle) - semi_major_axis * eccentricity
z = semi_minor_axis * sin(angle)
semi_minor_axis = semi_major_axis * sqrt(1 - eccentricity ** 2)
```

Trong đó `semi_major_axis` là bán trục lớn, `eccentricity` là độ lệch tâm và
`angle` là góc quay hiện tại. Các thông số này được dùng đồng nhất khi vẽ
quỹ đạo và tính vị trí hành tinh.

### 7.4. Phép chiếu phối cảnh

Sử dụng phép chiếu phối cảnh để hiển thị các đối tượng trong không gian ba chiều.

### 7.5. Bộ đệm độ sâu

Sử dụng Depth Testing để xác định đối tượng nào nằm phía trước khi các đối tượng chồng lấp trong không gian.

## 8. Thành viên thực hiện

- **Thành viên 1:** Xây dựng mô hình hành tinh và thuật toán vẽ quỹ đạo.
- **Thành viên 2:** Xây dựng thuật toán chuyển động và cập nhật tọa độ.
- **Thành viên 3:** Xây dựng camera, chương trình chính, tích hợp và kiểm thử.

## 9. Hướng phát triển

- Bổ sung texture bề mặt cho các hành tinh.
- Cải thiện ánh sáng và hiệu ứng phát sáng của Mặt Trời.
- Thêm chức năng điều chỉnh tốc độ mô phỏng.
- Bổ sung điều khiển camera bằng chuột và bàn phím.
- Hiển thị tên và thông tin của từng hành tinh.

## 10. Lưu ý

Mô hình sử dụng các kích thước, khoảng cách và tốc độ được điều chỉnh để thuận tiện quan sát. Các thông số mô phỏng không nhất thiết phản ánh chính xác tỷ lệ thiên văn thực tế.

---

**Môn học:** Đồ họa máy tính

**Đề tài:** Mô phỏng hệ Mặt Trời 3D bằng Python và OpenGL
