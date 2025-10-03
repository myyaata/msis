import threading
import queue
import os
import uuid
from pathlib import Path
import yt_dlp
from config import AppConfig
from url_validator import URLValidator
import logging
import time
import random
import subprocess
import sys

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DownloadManager:
    def __init__(self, progress_callback=None, completion_callback=None):
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        self.download_queue = queue.Queue()
        self.active_downloads = {}
        self._stop_event = threading.Event()
        Path(AppConfig.DOWNLOAD_FOLDER).mkdir(exist_ok=True)

        # Проверяем и обновляем yt-dlp при запуске
        self._check_and_update_ytdlp()

    def _check_and_update_ytdlp(self):
        """Проверяет и обновляет yt-dlp до последней версии"""
        try:
            logger.info("Проверка версии yt-dlp...")
            result = subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp'],
                                    capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                logger.info("yt-dlp успешно обновлен")
            else:
                logger.warning(f"Не удалось обновить yt-dlp: {result.stderr}")
        except Exception as e:
            logger.warning(f"Ошибка при обновлении yt-dlp: {e}")

    def start_download(self, url: str, output_path: str, is_audio: bool, quality: str):
        """Запускает новую загрузку и возвращает её ID"""
        download_type = "Только аудио (MP3)" if is_audio else "Видео (MP4)"
        return self.add_download(url, download_type, quality, output_path)

    def add_download(self, url: str, download_type: str, quality: str, custom_path: str = None):
        """Добавляет новую загрузку"""
        download_id = str(uuid.uuid4())[:8]

        service_name, service_info = URLValidator.detect_service(url)

        download_info = {
            'id': download_id,
            'url': url,
            'type': download_type,
            'quality': quality,
            'path': custom_path or AppConfig.DOWNLOAD_FOLDER,
            'status': 'В очереди',
            'progress': 0,
            'speed': 0.0,
            'eta': '',
            'filename': '',
            'service': service_name,
            'service_icon': service_info['icon'] if service_info else '🌐'
        }

        self.active_downloads[download_id] = download_info

        thread = threading.Thread(
            target=self._download_worker,
            args=(download_info,),
            daemon=True
        )
        thread.start()

        return download_id

    def _get_user_agent(self):
        """Возвращает случайный User-Agent"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        ]
        return random.choice(user_agents)

    def _clean_url(self, url):
        """Очищает URL от потенциально проблемных символов"""
        # Удаляем пробелы и управляющие символы
        cleaned_url = ''.join(char for char in url if ord(char) >= 32 and char not in ['\r', '\n', '\t'])
        return cleaned_url.strip()

    def _download_worker(self, download_info):
        """Воркер для загрузки файлов"""
        download_id = download_info['id']

        try:
            if self._stop_event.is_set():
                download_info['status'] = 'Остановлено'
                self._notify_progress(download_id)
                if self.completion_callback:
                    self.completion_callback(download_id, False, "Загрузка остановлена")
                return

            download_info['status'] = 'Загружается'
            self._notify_progress(download_id)

            # Очищаем URL
            clean_url = self._clean_url(download_info['url'])
            logger.info(f"Очищенный URL: {clean_url}")

            # Добавляем случайную задержку
            time.sleep(random.uniform(0.5, 2.0))



            # Базовые настройки
            ydl_opts = {
                'outtmpl': os.path.join(download_info['path'], '%(title)s.%(ext)s'),
                'noplaylist': True,
                'progress_hooks': [lambda d: self._progress_hook(d, download_id)],
                'quiet': False,  # Включаем вывод для диагностики
                'no_warnings': False,
                'fragment_retries': 10,
                'retries': 5,
                'http_headers': {
                    'User-Agent': self._get_user_agent(),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-us,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none'
                },
                'socket_timeout': 30,
                'nocheckcertificate': True,
                'geo_bypass': True,
                'extractor_retries': 3,
                'file_access_retries': 3,
                'sleep_interval': 1,
                'max_sleep_interval': 5,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'ignoreerrors': False,
                'no_check_certificates': True,
                'prefer_insecure': False,
                # Отключаем прокси принудительно
                'proxy': '',
                'source_address': None
            }

            service_name = download_info['service']

            # Специальные настройки для разных сервисов
            if service_name == 'YouTube':
                ydl_opts.update({
                    'http_headers': {
                        **ydl_opts['http_headers'],
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.youtube.com/',
                        'Origin': 'https://www.youtube.com',
                    },
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['web'],  # Используем только web клиент
                            'skip': ['hls'],
                            'formats': 'missing_pot'  # Разрешаем форматы без PO Token
                        }
                    },
                    # Упрощенные настройки формата
                    'format': 'best[ext=mp4]/best',
                    'no_check_certificates': True,
                    'ignoreerrors': False,
                })
            elif service_name == 'TikTok':
                ydl_opts.update({
                    'http_headers': {
                        **ydl_opts['http_headers'],
                        'Referer': 'https://www.tiktok.com/',
                        'Origin': 'https://www.tiktok.com',
                        'Authority': 'www.tiktok.com',
                        'Cache-Control': 'max-age=0',
                        'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                        'Sec-Ch-Ua-Mobile': '?0',
                        'Sec-Ch-Ua-Platform': '"macOS"'
                    },
                    'extractor_args': {
                        'tiktok': {
                            'webpage_url_basename': 'video',
                            'api_hostname': 'api.tiktokv.com'
                        }
                    }
                })
            elif service_name == 'Instagram':
                ydl_opts.update({
                    'http_headers': {
                        **ydl_opts['http_headers'],
                        'Referer': 'https://www.instagram.com/',
                        'Origin': 'https://www.instagram.com',
                        'X-Instagram-AJAX': '1',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })

            # Обработка аудио загрузок
            if download_info['type'] == 'Только аудио (MP3)':
                if service_name == 'SoundCloud':
                    ydl_opts.update({
                        'format': 'bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '320'
                        }]
                    })
                else:
                    ydl_opts.update({
                        'format': 'bestaudio[ext=m4a]/bestaudio/best',
                        'postprocessors': [{
                            'key': 'FFmpegExtractAudio',
                            'preferredcodec': 'mp3',
                            'preferredquality': '192'
                        }]
                    })
            else:
                # Обработка видео загрузок
                quality_format = AppConfig.VIDEO_QUALITIES.get(
                    download_info['quality'], 'best'
                )

                if service_name == 'YouTube':
                    # Специальные форматы для YouTube
                    format_map = {
                        'best[height<=2160]': 'best[height<=2160][ext=mp4]/best[height<=2160]/best[ext=mp4]/best',
                        'best[height<=1080]': 'best[height<=1080][ext=mp4]/best[height<=1080]/best[ext=mp4]/best',
                        'best[height<=720]': 'best[height<=720][ext=mp4]/best[height<=720]/best[ext=mp4]/best',
                        'best[height<=480]': 'best[height<=480][ext=mp4]/best[height<=480]/best[ext=mp4]/best',
                        'best[height<=360]': 'best[height<=360][ext=mp4]/best[height<=360]/best[ext=mp4]/best',
                        'best': 'best[ext=mp4]/best'
                    }
                    ydl_opts['format'] = format_map.get(quality_format, format_map['best'])
                elif service_name == 'TikTok':
                    ydl_opts['format'] = 'best[ext=mp4]/best'
                else:
                    if quality_format == 'best':
                        ydl_opts['format'] = 'best[ext=mp4]/best'
                    else:
                        ydl_opts['format'] = f'{quality_format}[ext=mp4]/{quality_format}/best[ext=mp4]/best'

                # Постпроцессор для видео
                if 'postprocessors' not in ydl_opts:
                    ydl_opts['postprocessors'] = []

                ydl_opts['postprocessors'].append({
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4'
                })

            # Выполняем загрузку с повторными попытками
            max_attempts = 3
            last_error = None

            for attempt in range(max_attempts):
                try:
                    if self._stop_event.is_set():
                        break

                    logger.info(f"Попытка {attempt + 1}/{max_attempts} для загрузки {download_id}")

                    # Обновляем User-Agent для каждой попытки
                    ydl_opts['http_headers']['User-Agent'] = self._get_user_agent()

                    # Используем очищенный URL
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([clean_url])

                    # Если дошли сюда, загрузка успешна
                    if not self._stop_event.is_set():
                        download_info['status'] = 'Завершено'
                        download_info['progress'] = 100
                        self._notify_progress(download_id)

                        if self.completion_callback:
                            self.completion_callback(download_id, True, "")
                    return

                except Exception as e:
                    last_error = e
                    error_str = str(e).lower()
                    logger.warning(f"Попытка {attempt + 1} неудачна: {str(e)}")

                    # Специфичные ошибки, при которых нет смысла повторять
                    if any(keyword in error_str for keyword in [
                        'private', 'not available', 'removed', 'deleted',
                        'copyright', 'blocked', '404', 'forbidden', 'not found'
                    ]):
                        logger.info(f"Критическая ошибка, не повторяем: {str(e)}")
                        break

                    if attempt < max_attempts - 1:
                        # Увеличиваем задержку с каждой попыткой
                        delay = random.uniform(3, 8) * (attempt + 1)
                        logger.info(f"Ждем {delay:.1f} секунд перед следующей попыткой...")
                        time.sleep(delay)

            # Если все попытки неудачны
            raise last_error or Exception("Неизвестная ошибка")

        except Exception as e:
            download_info['status'] = 'Ошибка'
            download_info['progress'] = 0
            error_msg = str(e)

            # Более информативные сообщения об ошибках
            if "ffmpeg" in error_msg.lower() or "ffprobe" in error_msg.lower():
                error_msg = "Ошибка: Требуется установить FFmpeg для конвертации аудио/видео"
            elif "format" in error_msg.lower():
                error_msg = f"Ошибка: Формат не поддерживается для {service_name}"
            elif "404" in error_msg or "not found" in error_msg.lower():
                error_msg = "Ошибка: Контент не найден или недоступен"
            elif "private" in error_msg.lower():
                error_msg = "Ошибка: Контент является приватным"
            elif "player response" in error_msg.lower():
                error_msg = "Ошибка: Устаревшая версия yt-dlp. Обновите через: pip install --upgrade yt-dlp"
            elif "connection" in error_msg.lower() or "transport" in error_msg.lower():
                error_msg = "Ошибка: Проблема с сетевым подключением. Проверьте интернет"
            elif "control characters" in error_msg:
                error_msg = "Ошибка: Некорректный URL. Проверьте ссылку на наличие лишних символов"
            elif "invalidurl" in error_msg.lower():
                error_msg = "Ошибка: Неверный формат URL. Проверьте правильность ссылки"
            elif "timeout" in error_msg.lower():
                error_msg = "Ошибка: Превышено время ожидания. Попробуйте позже"

            logger.error(f"Ошибка загрузки {download_id}: {error_msg}")

            self._notify_progress(download_id)
            if self.completion_callback:
                self.completion_callback(download_id, False, error_msg)

        finally:
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]

    def _progress_hook(self, d, download_id):
        """Обработчик прогресса загрузки"""
        if download_id not in self.active_downloads or self._stop_event.is_set():
            return

        download_info = self.active_downloads[download_id]

        if d['status'] == 'downloading':
            # Обновляем прогресс
            if 'downloaded_bytes' in d and 'total_bytes' in d and d['total_bytes']:
                progress = (d['downloaded_bytes'] / d['total_bytes']) * 100
                download_info['progress'] = min(progress, 100)
            elif 'downloaded_bytes' in d and 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                progress = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                download_info['progress'] = min(progress, 100)
            elif '_percent_str' in d:
                try:
                    percent_str = d['_percent_str'].strip('%')
                    download_info['progress'] = float(percent_str)
                except:
                    pass

            # Обновляем скорость
            if 'speed' in d and d['speed'] is not None:
                speed_kb = d['speed'] / 1024
                download_info['speed'] = speed_kb

            # Обновляем ETA
            if 'eta' in d and d['eta']:
                if isinstance(d['eta'], (int, float)):
                    eta_min = int(d['eta']) // 60
                    eta_sec = int(d['eta']) % 60
                    download_info['eta'] = f"{eta_min:02d}:{eta_sec:02d}"
                else:
                    download_info['eta'] = str(d['eta'])

            # Обновляем имя файла
            if 'filename' in d:
                filename = os.path.basename(d['filename'])
                if filename.endswith('.part') or filename.endswith('.ytdl'):
                    filename = filename.rsplit('.', 1)[0]
                download_info['filename'] = filename

            self._notify_progress(download_id)

        elif d['status'] == 'finished':
            download_info['progress'] = 100
            if 'filename' in d:
                filename = os.path.basename(d['filename'])
                if filename.endswith('.part') or filename.endswith('.ytdl'):
                    filename = filename.rsplit('.', 1)[0]
                if download_info['type'] == 'Только аудио (MP3)' and not filename.endswith('.mp3'):
                    base_name = os.path.splitext(filename)[0]
                    filename = f"{base_name}.mp3"
                download_info['filename'] = filename
            self._notify_progress(download_id)

    def _notify_progress(self, download_id):
        """Уведомляет о прогрессе"""
        if self.progress_callback and download_id in self.active_downloads:
            download_info = self.active_downloads[download_id]
            self.progress_callback(
                download_id,
                download_info['progress'],
                download_info['speed'],
                download_info['status'],
                download_info['filename']
            )

    def stop_all(self):
        """Останавливает все активные загрузки"""
        self._stop_event.set()
        for download_id in list(self.active_downloads.keys()):
            download_info = self.active_downloads.get(download_id)
            if download_info:
                download_info['status'] = 'Остановлено'
                self._notify_progress(download_id)
                if self.completion_callback:
                    self.completion_callback(download_id, False, "Загрузка остановлена")
                del self.active_downloads[download_id]