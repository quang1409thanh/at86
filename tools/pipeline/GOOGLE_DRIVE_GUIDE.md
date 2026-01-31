# Hướng dẫn tích hợp Google Drive

## 📋 Mục lục
1. [Trường hợp 1: Link Public](#trường-hợp-1-link-public)
2. [Trường hợp 2: Link Private (OAuth)](#trường-hợp-2-link-private-oauth)
3. [Cách lấy Credentials từ Google Cloud Console](#cách-lấy-credentials-từ-google-cloud-console)

---

## Trường hợp 1: Link Public

### Yêu cầu
- File/Folder phải được chia sẻ với chế độ **"Anyone with the link"**

### Cách chia sẻ file/folder public
1. Mở Google Drive
2. Click chuột phải vào file/folder → **Share**
3. Trong phần "General access", chọn **"Anyone with the link"**
4. Chọn quyền **"Viewer"**
5. Click **Done**

### Cách test

```bash
# Test file public
python test_google_drive.py --public "https://drive.google.com/file/d/xxx/view"

# Test folder public
python test_google_drive.py --public-folder "https://drive.google.com/drive/folders/xxx"
```

### Lưu ý
- Không cần credentials.json
- Không cần đăng nhập
- Chỉ hoạt động với file/folder đã được public

---

## Trường hợp 2: Link Private (OAuth)

### Yêu cầu
- File `credentials.json` từ Google Cloud Console
- Đăng nhập Google lần đầu tiên

### Cách test

```bash
# Test file private
python test_google_drive.py --private "https://drive.google.com/file/d/xxx/view"

# Liệt kê folder
python test_google_drive.py --list <FOLDER_ID>
python test_google_drive.py --list root  # My Drive
```

---

## Cách lấy Credentials từ Google Cloud Console

### Bước 1: Tạo Project

1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Click **"Select a project"** → **"New Project"**
3. Đặt tên project (ví dụ: `TOEIC-Pipeline`)
4. Click **Create**

![Step 1](https://i.imgur.com/placeholder1.png)

### Bước 2: Enable Google Drive API

1. Trong menu bên trái, vào **APIs & Services** → **Library**
2. Tìm kiếm **"Google Drive API"**
3. Click vào kết quả → Click **Enable**

**Link trực tiếp:** https://console.cloud.google.com/apis/library/drive.googleapis.com

### Bước 3: Tạo OAuth Consent Screen

1. Vào **APIs & Services** → **OAuth consent screen**
2. Chọn **External** → Click **Create**
3. Điền thông tin:
   - **App name:** TOEIC Pipeline
   - **User support email:** Email của bạn
   - **Developer contact:** Email của bạn
4. Click **Save and Continue**
5. Ở trang **Scopes**, click **Add or Remove Scopes**
6. Tìm và chọn: `.../auth/drive.readonly`
7. Click **Update** → **Save and Continue**
8. Ở trang **Test users**, click **Add Users**
9. Thêm email Google của bạn
10. Click **Save and Continue** → **Back to Dashboard**

### Bước 4: Tạo OAuth Client ID

1. Vào **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Chọn **Application type:** **Desktop app**
4. Đặt tên: `TOEIC Pipeline Desktop`
5. Click **Create**
6. **QUAN TRỌNG:** Click **Download JSON**

### Bước 5: Cài đặt Credentials

1. Đổi tên file vừa tải thành: `credentials.json`
2. Copy vào thư mục:
   ```
   /home/thanhyk14/Desktop/at86/tools/pipeline/common/credentials.json
   ```

### Bước 6: Xác thực lần đầu

```bash
cd ~/Desktop/at86/tools/pipeline
python test_google_drive.py --private <FILE_ID_BẤT_KỲ>
```

- Trình duyệt sẽ mở lên
- Đăng nhập Google
- Cho phép quyền truy cập
- Token sẽ được lưu tự động vào `token.json`
- **Lần sau không cần đăng nhập lại!**

---

## ⚠️ Lưu ý quan trọng

### Folder của bạn chưa public!

Link bạn cung cấp: 
```
https://drive.google.com/drive/folders/1T9flm4zIISZmVuPtsu208Aan8SuYMnuY
```

**Đang yêu cầu đăng nhập!** Bạn cần:

**Cách 1: Chia sẻ public**
1. Mở folder trên Google Drive
2. Click **Share** → **"Anyone with the link"** → **Done**

**Cách 2: Sử dụng OAuth** (recommend)
1. Làm theo hướng dẫn lấy credentials ở trên
2. Đặt `credentials.json` vào đúng thư mục
3. Chạy test với `--private` hoặc `--list`

---

## 📁 Cấu trúc file

```
tools/pipeline/
├── test_google_drive.py      # Script test
├── temp_cloud/               # Thư mục lưu file tải về
└── common/
    ├── credentials.json      # [BẠN CẦN TẠO] OAuth credentials
    └── token.json            # [TỰ ĐỘNG TẠO] Access token
```

---

## 🧪 Các lệnh test

```bash
# Xem hướng dẫn setup
python test_google_drive.py --setup

# Test file public
python test_google_drive.py --public <FILE_URL>

# Test folder public
python test_google_drive.py --public-folder <FOLDER_URL>

# Test file private (cần credentials.json)
python test_google_drive.py --private <FILE_URL>

# Liệt kê folder (cần credentials.json)
python test_google_drive.py --list <FOLDER_ID>
python test_google_drive.py --list root
```

---

## ❓ Troubleshooting

### Lỗi: "credentials.json không tìm thấy"
- Đảm bảo file nằm đúng đường dẫn: `tools/pipeline/common/credentials.json`

### Lỗi: "Access Denied" khi OAuth
- Đảm bảo email của bạn được thêm vào Test Users
- Đợi vài phút sau khi thêm

### Lỗi: "API not enabled"
- Enable Google Drive API tại Console

### Lỗi: "Token expired"
- Script tự động refresh token
- Nếu vẫn lỗi, xóa `token.json` và chạy lại

---

## 🔗 Các link hữu ích

- [Google Cloud Console](https://console.cloud.google.com/)
- [Google Drive API Documentation](https://developers.google.com/drive/api/v3/about-sdk)
- [OAuth 2.0 Playground](https://developers.google.com/oauthplayground/)
