import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QFileDialog, QProgressBar, QMessageBox, QListWidget,
                           QListWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import yt_dlp
import time

class LinkedInVideoDownloader:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.driver = None

    def setup_driver(self):
        """Tarayıcı ayarlarını yapılandır"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver

    def login(self):
        """LinkedIn'e giriş yap"""
        try:
            self.driver = self.setup_driver()
            self.driver.get('https://www.linkedin.com/login')
            
            # Email giriş
            email_elem = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_elem.send_keys(self.email)
            
            # Şifre giriş
            password_elem = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "password"))
            )
            password_elem.send_keys(self.password)
            
            # Giriş butonu
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            submit_button.click()
            
            # Giriş kontrolü
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".global-nav"))
            )
            
        except Exception as e:
            if self.driver:
                self.driver.quit()
            raise Exception(f"Giriş sırasında hata: {str(e)}")

    def get_course_videos(self, course_url):
        """Kurs sayfasındaki tüm videoları listele"""
        try:
            self.driver.get(course_url)
            time.sleep(5)  # Sayfa yüklemesi için bekle
            
            # Tüm bölümleri bul
            sections = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".classroom-toc-section"))
            )
            
            videos = []
            for section in sections:
                try:
                    # Bölüm başlığını al
                    section_title = section.find_element(By.CSS_SELECTOR, 
                        "span.classroom-toc-section__toggle-title").text.strip()
                    
                    # Bölümdeki videoları bul (sınavları hariç tut)
                    video_items = section.find_elements(By.CSS_SELECTOR, 
                        ".classroom-toc-item:not([data-toc-content-id*='Assessment'])")
                    
                    for item in video_items:
                        try:
                            # Video başlığı ve süre
                            title = item.find_element(By.CSS_SELECTOR, 
                                ".classroom-toc-item__title").text.strip()
                            duration = item.find_element(By.CSS_SELECTOR, 
                                "._bodyText_1e5nen._default_1i6ulk._sizeXSmall_1e5nen._lowEmphasis_1i6ulk span").text.strip()
                            
                            # Video URL'si
                            url = item.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                            
                            # Quiz ve sınavları atla
                            if not "quiz" in url.lower() and "video" in duration.lower():
                                videos.append({
                                    "section": section_title,
                                    "title": title.replace("(Görüntülendi)", "").strip(),
                                    "duration": duration,
                                    "url": url
                                })
                                
                        except Exception as e:
                            print(f"Video öğesi işlenirken hata: {str(e)}")
                            continue
                            
                except Exception as e:
                    print(f"Bölüm işlenirken hata: {str(e)}")
                    continue
                        
            if not videos:
                raise Exception("Hiç video bulunamadı!")
                
            return videos
                
        except Exception as e:
            raise Exception(f"Video listesi alınırken hata: {str(e)}")

    def download_video(self, video_url, output_path):
        """Video'yu indir"""
        try:
            self.driver.get(video_url)
            time.sleep(5)
            
            # Video elementini bul
            video_elem = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "video"))
            )
            
            # Video URL'sini al
            video_url = video_elem.get_attribute('src')
            if not video_url:
                raise Exception("Video URL'si bulunamadı")
            
            # Video'yu indir
            ydl_opts = {
                'format': 'best',
                'outtmpl': output_path,
                'quiet': False,
                'progress': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
                    
        except Exception as e:
            raise Exception(f"Video indirilirken hata: {str(e)}")

class CourseVideoThread(QThread):
    progress_signal = pyqtSignal(str)
    videos_signal = pyqtSignal(list)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, email, password, course_url):
        super().__init__()
        self.email = email
        self.password = password
        self.course_url = course_url

    def run(self):
        try:
            downloader = LinkedInVideoDownloader(self.email, self.password)
            self.progress_signal.emit("Giriş yapılıyor...")
            downloader.login()
            
            self.progress_signal.emit("Video listesi alınıyor...")
            videos = downloader.get_course_videos(self.course_url)
            
            self.videos_signal.emit(videos)
            self.finished_signal.emit(True, f"{len(videos)} video bulundu!")
            
        except Exception as e:
            self.finished_signal.emit(False, f"Hata: {str(e)}")

class DownloaderThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, email, password, video_url, output_path):
        super().__init__()
        self.email = email
        self.password = password
        self.video_url = video_url
        self.output_path = output_path

    def run(self):
        try:
            downloader = LinkedInVideoDownloader(self.email, self.password)
            self.progress_signal.emit("Giriş yapılıyor...")
            downloader.login()
            
            self.progress_signal.emit("Video indiriliyor...")
            downloader.download_video(self.video_url, self.output_path)
            
            self.finished_signal.emit(True, "Video başarıyla indirildi!")
        except Exception as e:
            self.finished_signal.emit(False, f"Hata: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinkedIn Learning Video İndirici")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.videos = []
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QLabel {
                font-size: 12px;
                font-weight: bold;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton {
                background-color: #0077b5;
                color: white;
                padding: 8px 15px;
                border: none;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #006097;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 3px;
                font-size: 12px;
                padding: 5px;
            }
        """)
        
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Kullanıcı bilgileri
        credentials_group = QWidget()
        credentials_layout = QVBoxLayout()
        credentials_group.setLayout(credentials_layout)
        
        # Email
        email_layout = QHBoxLayout()
        email_label = QLabel("LinkedIn Email:")
        self.email_input = QLineEdit()
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_input)
        credentials_layout.addLayout(email_layout)

        # Şifre
        password_layout = QHBoxLayout()
        password_label = QLabel("LinkedIn Şifre:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        credentials_layout.addLayout(password_layout)
        
        layout.addWidget(credentials_group)

        # Kurs URL
        url_layout = QHBoxLayout()
        url_label = QLabel("Kurs URL:")
        self.url_input = QLineEdit()
        self.get_videos_button = QPushButton("Videoları Listele")
        self.get_videos_button.clicked.connect(self.get_course_videos)
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.get_videos_button)
        layout.addLayout(url_layout)

        # Video listesi
        list_label = QLabel("Video Listesi:")
        layout.addWidget(list_label)
        self.video_list = QListWidget()
        self.video_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.video_list)

        # İndirme klasörü
        save_layout = QHBoxLayout()
        save_label = QLabel("İndirme Klasörü:")
        self.save_path_input = QLineEdit()
        self.save_path_input.setReadOnly(True)
        browse_button = QPushButton("Klasör Seç")
        browse_button.clicked.connect(self.browse_location)
        save_layout.addWidget(save_label)
        save_layout.addWidget(self.save_path_input)
        save_layout.addWidget(browse_button)
        layout.addLayout(save_layout)

        # İndirme butonu
        self.download_button = QPushButton("Seçili Videoları İndir")
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setEnabled(False)
        layout.addWidget(self.download_button)

        # İlerleme çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_bar)

        # Durum etiketi
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

    def browse_location(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Video İndirme Klasörü",
            os.path.expanduser("~/Downloads")
        )
        if folder_path:
            self.save_path_input.setText(folder_path)
            if self.video_list.count() > 0:
                self.download_button.setEnabled(True)

    def update_video_list(self, videos):
        """Video listesini güncelle"""
        self.videos = videos
        self.video_list.clear()
        current_section = None
        
        for video in videos:
            if video['section'] != current_section:
                current_section = video['section']
                section_item = QListWidgetItem(f"\n=== {current_section} ===")
                section_item.setFlags(section_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                self.video_list.addItem(section_item)
            
            self.video_list.addItem(f"{video['title']} ({video['duration']})")

    def get_course_videos(self):
        """Kurs videolarını listele"""
        if not all([self.email_input.text(), self.password_input.text(), self.url_input.text()]):
            QMessageBox.warning(self, "Hata", "Lütfen tüm bilgileri doldurun!")
            return

        self.get_videos_button.setEnabled(False)
        self.progress_bar.setMaximum(0)
        self.video_list.clear()
        
        self.course_thread = CourseVideoThread(
            self.email_input.text(),
            self.password_input.text(),
            self.url_input.text()
        )
        self.course_thread.progress_signal.connect(self.update_progress)
        self.course_thread.videos_signal.connect(self.update_video_list)
        self.course_thread.finished_signal.connect(self.video_list_finished)
        self.course_thread.start()

    def video_list_finished(self, success, message):
        """Video listesi alma işlemi tamamlandığında"""
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100 if success else 0)
        self.status_label.setText(message)
        self.get_videos_button.setEnabled(True)
        
        if success:
            if self.save_path_input.text():
                self.download_button.setEnabled(True)
        else:
            QMessageBox.critical(self, "Hata", message)

    def sanitize_filename(self, filename):
        """Dosya adını güvenli hale getir"""
        # Windows'da kullanılamayan karakterleri temizle
        invalid_chars = '<>:"/\\|?*\n\r\t'
        # Dosya adından geçersiz karakterleri kaldır
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Görüntülendi yazısını ve parantezleri kaldır
        filename = filename.replace('(Görüntülendi)', '').strip()
        filename = filename.replace('(', '').replace(')', '')
        # Boşlukları alt çizgi ile değiştir
        filename = filename.replace(' ', '_')
        
        # Uzunluğu sınırla
        filename = filename[:200]
        
        return filename

    def start_download(self):
        """Seçili videoların indirilmesini başlat"""
        selected_items = []
        for index in range(self.video_list.count()):
            item = self.video_list.item(index)
            if item.flags() & Qt.ItemFlag.ItemIsSelectable and item.isSelected():
                selected_items.append(item)
        
        if not selected_items:
            QMessageBox.warning(self, "Hata", "Lütfen indirilecek videoları seçin!")
            return

        if not self.save_path_input.text():
            QMessageBox.warning(self, "Hata", "Lütfen indirme klasörünü seçin!")
            return

        # İndirilecek videoları belirle
        self.selected_videos = []
        video_index = -1
        for index in range(self.video_list.count()):
            item = self.video_list.item(index)
            if not item.text().startswith("==="):  # Bölüm başlığı değilse
                video_index += 1
                if item.isSelected():
                    self.selected_videos.append(self.videos[video_index])

        # İndirme işlemini başlat
        self.download_button.setEnabled(False)
        self.current_video_index = 0
        self.download_next_video()

    def download_next_video(self):
        """Sıradaki videoyu indir"""
        if self.current_video_index >= len(self.selected_videos):
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(100)
            self.status_label.setText("Tüm videolar indirildi!")
            self.download_button.setEnabled(True)
            QMessageBox.information(self, "Başarılı", "Tüm videolar başarıyla indirildi!")
            return

        video = self.selected_videos[self.current_video_index]
        safe_title = self.sanitize_filename(video['title'])
        output_path = os.path.join(
            self.save_path_input.text(),
            f"{safe_title}.mp4"
        )

        self.progress_bar.setMaximum(0)
        self.status_label.setText(f"İndiriliyor: {video['title']}")

        self.downloader_thread = DownloaderThread(
            self.email_input.text(),
            self.password_input.text(),
            video['url'],
            output_path
        )
        self.downloader_thread.progress_signal.connect(self.update_progress)
        self.downloader_thread.finished_signal.connect(self.video_download_finished)
        self.downloader_thread.start()

    def update_progress(self, message):
        """İlerleme durumunu güncelle"""
        self.status_label.setText(message)

    def video_download_finished(self, success, message):
        """Video indirme işlemi tamamlandığında"""
        if success:
            self.current_video_index += 1
            self.download_next_video()
        else:
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            self.status_label.setText(message)
            self.download_button.setEnabled(True)
            QMessageBox.critical(self, "Hata", f"Video indirme hatası: {message}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
