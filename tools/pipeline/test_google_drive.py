"""
Test Google Drive Access Script
================================
Test 2 trường hợp:
1. Public link - Không cần xác thực (dùng API key hoặc direct download)
2. Private link - Cần xác thực OAuth 2.0

Cách sử dụng:
    python test_google_drive.py --public <DRIVE_URL_OR_FILE_ID>
    python test_google_drive.py --public-folder <FOLDER_URL_OR_ID>
    python test_google_drive.py --private <DRIVE_URL_OR_FILE_ID>
    python test_google_drive.py --setup   # Để thiết lập OAuth credentials
"""

import os
import sys
import re
import argparse
import requests
from pathlib import Path

# Thư mục lưu file tạm
TEMP_DIR = Path(__file__).parent / "temp_cloud"
CREDENTIALS_PATH = Path(__file__).parent / "common" / "credentials.json"
TOKEN_PATH = Path(__file__).parent / "common" / "token.json"


def extract_file_id(url_or_id: str) -> str:
    """
    Trích xuất File ID từ Google Drive URL.
    Hỗ trợ các định dạng:
    - https://drive.google.com/file/d/<FILE_ID>/view
    - https://drive.google.com/open?id=<FILE_ID>
    - https://drive.google.com/uc?id=<FILE_ID>
    - https://drive.google.com/drive/folders/<FOLDER_ID>
    - Hoặc trực tiếp FILE_ID
    """
    patterns = [
        r'/file/d/([a-zA-Z0-9_-]+)',
        r'[?&]id=([a-zA-Z0-9_-]+)',
        r'/folders/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    # Nếu không match pattern nào, giả định đây là file ID trực tiếp
    if re.match(r'^[a-zA-Z0-9_-]+$', url_or_id):
        return url_or_id
    
    raise ValueError(f"Không thể trích xuất File ID từ: {url_or_id}")


def test_public_download(file_id: str, output_name: str = None) -> bool:
    """
    Test tải file từ Google Drive public link.
    Sử dụng phương thức direct download không cần xác thực.
    """
    print(f"\n{'='*60}")
    print("🌐 TEST PUBLIC GOOGLE DRIVE FILE")
    print(f"{'='*60}")
    print(f"📁 File ID: {file_id}")
    
    # Tạo thư mục temp nếu chưa có
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # URL download trực tiếp cho file public
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    try:
        print(f"🔗 Download URL: {download_url}")
        print("⏳ Đang tải file...")
        
        # Gửi request với session để handle cookies
        session = requests.Session()
        response = session.get(download_url, stream=True, allow_redirects=True)
        
        # Kiểm tra nếu có warning page (file lớn)
        if 'text/html' in response.headers.get('Content-Type', ''):
            # Tìm confirm token
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    download_url = f"{download_url}&confirm={value}"
                    response = session.get(download_url, stream=True)
                    break
            else:
                # Thử tìm confirm link trong HTML
                content = response.text
                if 'confirm=' in content:
                    match = re.search(r'confirm=([a-zA-Z0-9_-]+)', content)
                    if match:
                        download_url = f"https://drive.google.com/uc?export=download&id={file_id}&confirm={match.group(1)}"
                        response = session.get(download_url, stream=True)
        
        # Kiểm tra response
        if response.status_code != 200:
            print(f"❌ Lỗi HTTP: {response.status_code}")
            print(f"   Response: {response.text[:500]}")
            return False
        
        # Lấy tên file từ header hoặc dùng file_id
        content_disposition = response.headers.get('Content-Disposition', '')
        if 'filename=' in content_disposition:
            filename = re.search(r'filename="?(.+?)"?(?:;|$)', content_disposition)
            if filename:
                output_name = filename.group(1)
        
        if not output_name:
            # Đoán extension từ content type
            content_type = response.headers.get('Content-Type', 'application/octet-stream')
            ext_map = {
                'application/pdf': '.pdf',
                'audio/mpeg': '.mp3',
                'image/jpeg': '.jpg',
                'image/png': '.png',
            }
            ext = ext_map.get(content_type, '.bin')
            output_name = f"{file_id}{ext}"
        
        output_path = TEMP_DIR / output_name
        
        # Lưu file
        total_size = int(response.headers.get('Content-Length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        progress = (downloaded / total_size) * 100
                        print(f"\r   📥 Progress: {progress:.1f}%", end='', flush=True)
        
        print()  # New line after progress
        
        # Verify file
        file_size = output_path.stat().st_size
        print(f"✅ Tải thành công!")
        print(f"   📄 File: {output_path}")
        print(f"   📊 Kích thước: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_public_folder(folder_id: str) -> bool:
    """
    Test liệt kê và tải files từ public Google Drive folder.
    Sử dụng phương thức scraping HTML (không cần API key).
    """
    print(f"\n{'='*60}")
    print("📂 TEST PUBLIC GOOGLE DRIVE FOLDER")
    print(f"{'='*60}")
    print(f"📁 Folder ID: {folder_id}")
    
    # Tạo thư mục temp
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    folder_temp = TEMP_DIR / folder_id
    folder_temp.mkdir(parents=True, exist_ok=True)
    
    # URL để lấy danh sách files trong folder public
    # Sử dụng Google Drive embedded view
    folder_url = f"https://drive.google.com/embeddedfolderview?id={folder_id}"
    
    try:
        print(f"🔗 Folder URL: {folder_url}")
        print("⏳ Đang lấy danh sách files...")
        
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        response = session.get(folder_url)
        
        if response.status_code != 200:
            print(f"❌ Lỗi HTTP: {response.status_code}")
            return False
        
        html = response.text
        
        # Parse HTML để tìm file IDs và tên
        # Pattern cho file entries trong embedded view
        file_pattern = r'data-id="([a-zA-Z0-9_-]+)"[^>]*>.*?<div class="flip-entry-title">([^<]+)</div>'
        matches = re.findall(file_pattern, html, re.DOTALL)
        
        if not matches:
            # Thử pattern khác
            file_pattern2 = r'\["([a-zA-Z0-9_-]{20,})",\s*"([^"]+)"'
            matches = re.findall(file_pattern2, html)
        
        if not matches:
            # Thử tìm trong script data
            script_pattern = r'"([a-zA-Z0-9_-]{25,})","([^"]+\.(mp3|pdf|jpg|png|mp4))"'
            matches = re.findall(script_pattern, html, re.IGNORECASE)
            matches = [(m[0], m[1]) for m in matches]
        
        if not matches:
            print("⚠️  Không tìm thấy files qua HTML parsing.")
            print("   Đang thử phương pháp khác...")
            
            # Thử dùng Google Drive API không cần auth (chỉ cho public folders)
            api_url = f"https://www.googleapis.com/drive/v3/files"
            params = {
                'q': f"'{folder_id}' in parents",
                'fields': 'files(id,name,mimeType)',
                'key': 'AIzaSyC1qbk75NzWBvSaDh6KnUvKMs7Vt2Ry-lsM'  # Public API key (limited)
            }
            
            # Fallback: Hiển thị hướng dẫn manual
            print("\n📋 HƯỚNG DẪN TẢI THỦ CÔNG:")
            print(f"   1. Mở folder: https://drive.google.com/drive/folders/{folder_id}")
            print("   2. Với mỗi file, click chuột phải → Get link")
            print("   3. Copy link và chạy:")
            print(f"      python {Path(__file__).name} --public <FILE_LINK>")
            
            # Thử liệt kê qua một cách khác
            alt_url = f"https://drive.google.com/drive/folders/{folder_id}"
            print(f"\n🔗 Thử mở trực tiếp: {alt_url}")
            
            alt_response = session.get(alt_url)
            
            # Tìm tất cả file IDs trong response
            all_ids = re.findall(r'"([a-zA-Z0-9_-]{25,45})"', alt_response.text)
            # Lọc ra các ID unique và có vẻ là file
            unique_ids = list(set([id for id in all_ids if len(id) >= 25 and len(id) <= 45]))
            
            if unique_ids:
                print(f"\n📄 Tìm thấy {len(unique_ids)} IDs tiềm năng:")
                for i, fid in enumerate(unique_ids[:10]):  # Chỉ hiện 10 đầu
                    print(f"   {i+1}. {fid}")
                if len(unique_ids) > 10:
                    print(f"   ... và {len(unique_ids) - 10} IDs khác")
                
                print("\n🧪 Thử tải ID đầu tiên...")
                return test_public_download(unique_ids[0])
            
            return False
        
        print(f"\n📄 Tìm thấy {len(matches)} files:")
        print(f"{'Tên File':<50} {'ID'}")
        print("-" * 80)
        
        files_info = []
        for file_id, file_name in matches[:20]:  # Giới hạn 20 files
            name_display = file_name[:48] + '..' if len(file_name) > 50 else file_name
            print(f"{name_display:<50} {file_id}")
            files_info.append((file_id, file_name))
        
        if len(matches) > 20:
            print(f"... và {len(matches) - 20} files khác")
        
        # Thử tải file đầu tiên
        if files_info:
            print(f"\n🧪 Thử tải file đầu tiên: {files_info[0][1]}")
            return test_public_download(files_info[0][0], files_info[0][1])
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_private_download(file_id: str, output_name: str = None) -> bool:
    """
    Test tải file từ Google Drive private link.
    Sử dụng OAuth 2.0 để xác thực.
    """
    print(f"\n{'='*60}")
    print("🔐 TEST PRIVATE GOOGLE DRIVE LINK (OAuth 2.0)")
    print(f"{'='*60}")
    print(f"📁 File ID: {file_id}")
    
    # Kiểm tra credentials
    if not CREDENTIALS_PATH.exists():
        print(f"\n❌ Chưa có credentials.json!")
        print(f"   Vui lòng đặt file credentials.json tại:")
        print(f"   {CREDENTIALS_PATH}")
        print(f"\n   Hoặc chạy: python {__file__} --setup")
        return False
    
    try:
        # Import Google API libraries
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        import io
        
        print("✅ Google API libraries đã được import")
        
    except ImportError as e:
        print(f"\n❌ Chưa cài đặt Google API libraries!")
        print(f"   Chạy lệnh sau để cài đặt:")
        print(f"   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False
    
    # Scopes cần thiết
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    
    creds = None
    
    # Load token nếu đã có
    if TOKEN_PATH.exists():
        print("🔑 Đang load token đã lưu...")
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    
    # Nếu token không hợp lệ hoặc hết hạn
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Token hết hạn, đang refresh...")
            creds.refresh(Request())
        else:
            print("🌐 Mở trình duyệt để đăng nhập Google...")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Lưu token
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
        print(f"💾 Token đã lưu tại: {TOKEN_PATH}")
    
    print("✅ Xác thực thành công!")
    
    # Tạo service
    service = build('drive', 'v3', credentials=creds)
    
    # Lấy metadata của file
    print(f"📋 Đang lấy thông tin file...")
    try:
        file_metadata = service.files().get(fileId=file_id, fields='name, mimeType, size').execute()
        file_name = file_metadata.get('name', f'{file_id}.bin')
        mime_type = file_metadata.get('mimeType', 'application/octet-stream')
        file_size = int(file_metadata.get('size', 0))
        
        print(f"   📄 Tên: {file_name}")
        print(f"   📊 Loại: {mime_type}")
        print(f"   📏 Kích thước: {file_size:,} bytes")
        
    except Exception as e:
        print(f"❌ Không thể lấy thông tin file: {e}")
        print("   Có thể file không tồn tại hoặc bạn không có quyền truy cập.")
        return False
    
    # Tạo thư mục temp
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    output_path = TEMP_DIR / (output_name or file_name)
    
    # Download file
    print(f"⏳ Đang tải file...")
    try:
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"\r   📥 Progress: {int(status.progress() * 100)}%", end='', flush=True)
        
        print()  # New line
        
        # Lưu file
        with open(output_path, 'wb') as f:
            fh.seek(0)
            f.write(fh.read())
        
        print(f"✅ Tải thành công!")
        print(f"   📄 File: {output_path}")
        print(f"   📊 Kích thước: {output_path.stat().st_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ Lỗi khi tải file: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_drive_folder(folder_id: str = "root") -> bool:
    """
    Liệt kê nội dung của một folder trên Google Drive (cần OAuth).
    """
    print(f"\n{'='*60}")
    print("📂 LIỆT KÊ NỘI DUNG GOOGLE DRIVE FOLDER (OAuth)")
    print(f"{'='*60}")
    print(f"📁 Folder ID: {folder_id}")
    
    # Kiểm tra credentials
    if not CREDENTIALS_PATH.exists():
        print(f"\n❌ Chưa có credentials.json!")
        print(f"   Để liệt kê folder private, cần xác thực OAuth.")
        print(f"   Chạy: python {__file__} --setup")
        print(f"\n💡 Nếu folder là PUBLIC, thử:")
        print(f"   python {__file__} --public-folder {folder_id}")
        return False
    
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
    except ImportError:
        print(f"\n❌ Chưa cài đặt Google API libraries!")
        return False
    
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    creds = None
    
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    
    service = build('drive', 'v3', credentials=creds)
    
    # Query files trong folder
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(
        q=query,
        pageSize=50,
        fields="files(id, name, mimeType, size)"
    ).execute()
    
    items = results.get('files', [])
    
    if not items:
        print("📭 Folder trống hoặc không có quyền truy cập.")
        return True
    
    print(f"\n{'Tên File':<40} {'Loại':<30} {'ID'}")
    print("-" * 100)
    
    for item in items:
        name = item['name'][:38] + '..' if len(item['name']) > 40 else item['name']
        mime = item['mimeType'][:28] + '..' if len(item['mimeType']) > 30 else item['mimeType']
        print(f"{name:<40} {mime:<30} {item['id']}")
    
    print(f"\n📊 Tổng cộng: {len(items)} items")
    return True


def setup_credentials():
    """
    Hướng dẫn người dùng thiết lập credentials.
    """
    print(f"\n{'='*60}")
    print("⚙️  HƯỚNG DẪN THIẾT LẬP GOOGLE DRIVE CREDENTIALS")
    print(f"{'='*60}")
    
    print("""
📋 CÁC BƯỚC THỰC HIỆN:

1️⃣  Truy cập Google Cloud Console:
    https://console.cloud.google.com/

2️⃣  Tạo Project mới (hoặc chọn project có sẵn)
    - Click "Select a project" → "New Project"
    - Đặt tên và Create

3️⃣  Enable Google Drive API:
    - Vào APIs & Services → Library
    - Tìm "Google Drive API" → Enable
    - Link: https://console.cloud.google.com/apis/library/drive.googleapis.com

4️⃣  Tạo OAuth Consent Screen:
    - Vào APIs & Services → OAuth consent screen
    - Chọn "External" → Create
    - Điền App name, User support email
    - Add scope: .../auth/drive.readonly
    - Add Test users: email của bạn
    - Save

5️⃣  Tạo Credentials:
    - Vào APIs & Services → Credentials
    - Click "Create Credentials" → "OAuth client ID"
    - Application type: "Desktop app"
    - Đặt tên → Create
    - Download JSON file

6️⃣  Đặt file credentials:
    - Đổi tên file thành: credentials.json
    - Copy vào thư mục:
""")
    print(f"      {CREDENTIALS_PATH.parent}")
    print(f"""
7️⃣  Test lại:
    python {Path(__file__).name} --private <YOUR_FILE_ID>
""")
    
    # Kiểm tra trạng thái hiện tại
    print(f"\n📊 TRẠNG THÁI HIỆN TẠI:")
    print(f"   credentials.json: {'✅ Có' if CREDENTIALS_PATH.exists() else '❌ Chưa có'}")
    print(f"   token.json: {'✅ Có' if TOKEN_PATH.exists() else '⏳ Chưa xác thực'}")
    
    # Kiểm tra libraries
    try:
        import google.oauth2
        import googleapiclient
        print(f"   Google libraries: ✅ Đã cài đặt")
    except ImportError:
        print(f"   Google libraries: ❌ Chưa cài đặt")
        print(f"   👉 Chạy: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")


def main():
    parser = argparse.ArgumentParser(
        description="Test Google Drive Access",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  # Test public file
  python test_google_drive.py --public https://drive.google.com/file/d/xxx/view
  
  # Test public folder
  python test_google_drive.py --public-folder https://drive.google.com/drive/folders/xxx
  
  # Test private file (cần OAuth)
  python test_google_drive.py --private xxx
  
  # Liệt kê folder (cần OAuth)
  python test_google_drive.py --list <FOLDER_ID>
  
  # Xem hướng dẫn setup
  python test_google_drive.py --setup
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--public', metavar='URL', help='Test tải file từ public link')
    group.add_argument('--public-folder', metavar='URL', help='Test liệt kê/tải từ public folder')
    group.add_argument('--private', metavar='URL', help='Test tải file từ private link (cần OAuth)')
    group.add_argument('--list', metavar='FOLDER_ID', help='Liệt kê nội dung folder (cần OAuth, dùng "root" cho My Drive)')
    group.add_argument('--setup', action='store_true', help='Hiển thị hướng dẫn thiết lập credentials')
    
    parser.add_argument('--output', '-o', metavar='NAME', help='Tên file output')
    
    args = parser.parse_args()
    
    if args.setup:
        setup_credentials()
        return
    
    if args.public:
        file_id = extract_file_id(args.public)
        success = test_public_download(file_id, args.output)
        sys.exit(0 if success else 1)
    
    if args.public_folder:
        folder_id = extract_file_id(args.public_folder)
        success = test_public_folder(folder_id)
        sys.exit(0 if success else 1)
    
    if args.private:
        file_id = extract_file_id(args.private)
        success = test_private_download(file_id, args.output)
        sys.exit(0 if success else 1)
    
    if args.list:
        folder_id = args.list if args.list != 'root' else 'root'
        if args.list.startswith('http'):
            folder_id = extract_file_id(args.list)
        success = list_drive_folder(folder_id)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
