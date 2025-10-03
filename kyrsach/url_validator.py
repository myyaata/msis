import re
import requests
from urllib.parse import urlparse, parse_qs
from config import AppConfig
import logging
from typing import Tuple, Optional, Dict, Any

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class URLValidator:
    """Улучшенный валидатор URL с расширенной поддержкой сервисов и надежной проверкой"""
    
    # Расширенные паттерны для различных сервисов
    EXTENDED_PATTERNS = {
        'YouTube': [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/|youtube\.com/v/)',
            r'youtube\.com/playlist\?list=',
            r'youtube\.com/shorts/',
            r'm\.youtube\.com'
        ],
        'Twitch': [
            r'twitch\.tv/videos/',
            r'twitch\.tv/\w+/clip/',
            r'clips\.twitch\.tv/',
            r'm\.twitch\.tv'
        ],
        'TikTok': [
            r'tiktok\.com/@[\w.-]+/video/',
            r'vm\.tiktok\.com/',
            r'm\.tiktok\.com',
            r'tiktok\.com/t/'
        ],
        'Instagram': [
            r'instagram\.com/p/',
            r'instagram\.com/reel/',
            r'instagram\.com/tv/',
            r'instagr\.am'
        ],
        'VK': [
            r'vk\.com/video',
            r'vk\.com/clip',
            r'm\.vk\.com'
        ],
        'Rutube': [
            r'rutube\.ru/video/',
            r'm\.rutube\.ru'
        ]
    }
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """
        Улучшенная проверка корректности URL с дополнительными проверками.
        
        Args:
            url (str): URL для проверки
            
        Returns:
            bool: True, если URL корректен
        """
        if not url or not isinstance(url, str):
            logger.debug("URL пустой или не является строкой")
            return False
            
        url = url.strip()
        
        # Минимальная длина URL
        if len(url) < 10:
            logger.debug(f"URL слишком короткий: {len(url)} символов")
            return False
        
        # Максимальная длина URL (RFC 2616 рекомендует не более 2048)
        if len(url) > 2048:
            logger.debug(f"URL слишком длинный: {len(url)} символов")
            return False
        
        try:
            # Парсинг URL
            parsed = urlparse(url)
            
            # Проверка схемы
            if parsed.scheme not in ('http', 'https'):
                logger.debug(f"Неподдерживаемая схема: {parsed.scheme}")
                return False
            
            # Проверка домена
            if not parsed.netloc or len(parsed.netloc) < 3:
                logger.debug(f"Некорректный домен: {parsed.netloc}")
                return False
            
            # Проверка на наличие недопустимых символов
            invalid_chars = ['<', '>', '"', '|', '^', '`', '{', '}', '\\']
            if any(char in url for char in invalid_chars):
                logger.debug("URL содержит недопустимые символы")
                return False
            
            # Дополнительная проверка домена
            if not cls._is_valid_domain(parsed.netloc):
                logger.debug(f"Недопустимый домен: {parsed.netloc}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при валидации URL {url}: {str(e)}")
            return False
    
    @classmethod
    def _is_valid_domain(cls, domain: str) -> bool:
        """
        Проверяет корректность домена.
        
        Args:
            domain (str): Домен для проверки
            
        Returns:
            bool: True, если домен корректен
        """
        try:
            # Удаляем порт, если есть
            domain_part = domain.split(':')[0]
            
            # Проверка на IP-адрес (базовая)
            if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', domain_part):
                return True
            
            # Проверка доменного имени
            domain_pattern = re.compile(
                r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$'
            )
            
            return bool(domain_pattern.match(domain_part))
            
        except Exception:
            return False
    
    @classmethod
    def detect_service(cls, url: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Улучшенное определение сервиса с поддержкой расширенных паттернов.
        
        Args:
            url (str): URL для анализа
            
        Returns:
            Tuple[str, Optional[Dict]]: (название сервиса, информация о сервисе)
        """
        if not url or not isinstance(url, str):
            logger.debug("Пустой URL в detect_service")
            return "Неизвестно", None
        
        url_lower = url.lower().strip()
        
        try:
            # Сначала проверяем стандартные паттерны из конфига
            if hasattr(AppConfig, 'SUPPORTED_SERVICES'):
                for service_name, service_info in AppConfig.SUPPORTED_SERVICES.items():
                    if not isinstance(service_info, dict):
                        continue
                    
                    patterns = service_info.get('patterns', [])
                    for pattern in patterns:
                        try:
                            if re.search(pattern, url_lower):
                                logger.info(f"Сервис определен: {service_name}")
                                return service_name, service_info
                        except re.error as e:
                            logger.warning(f"Некорректный regex паттерн {pattern}: {e}")
                            continue
            
            # Затем проверяем расширенные паттерны
            for service_name, patterns in cls.EXTENDED_PATTERNS.items():
                for pattern in patterns:
                    try:
                        if re.search(pattern, url_lower):
                            # Создаем базовую информацию о сервисе
                            service_info = cls._get_default_service_info(service_name)
                            logger.info(f"Сервис определен через расширенные паттерны: {service_name}")
                            return service_name, service_info
                    except re.error as e:
                        logger.warning(f"Некорректный regex паттерн {pattern}: {e}")
                        continue
            
            # Если не удалось определить, пытаемся по домену
            parsed = urlparse(url_lower)
            domain = parsed.netloc.lower()
            
            for service_name in cls.EXTENDED_PATTERNS.keys():
                if service_name.lower() in domain:
                    service_info = cls._get_default_service_info(service_name)
                    logger.info(f"Сервис определен по домену: {service_name}")
                    return service_name, service_info
                    
        except Exception as e:
            logger.error(f"Ошибка при определении сервиса для URL {url}: {str(e)}")
        
        logger.debug(f"Сервис не поддерживается для URL: {url}")
        return "Неподдерживаемый сервис", None
    
    @classmethod
    def _get_default_service_info(cls, service_name: str) -> Dict[str, Any]:
        """
        Возвращает базовую информацию о сервисе.
        
        Args:
            service_name (str): Название сервиса
            
        Returns:
            Dict[str, Any]: Информация о сервисе
        """
        icons = {
            'YouTube': '📺',
            'Twitch': '🎮',
            'TikTok': '🎵',
            'Instagram': '📷',
            'VK': '🔵',
            'Rutube': '🎬'
        }
        
        return {
            'icon': icons.get(service_name, '🌐'),
            'formats': ['MP4', 'MP3'],  # Базовые форматы
            'patterns': cls.EXTENDED_PATTERNS.get(service_name, [])
        }
    
    @classmethod
    def get_service_icon(cls, url: str) -> str:
        """
        Возвращает иконку сервиса для URL.
        
        Args:
            url (str): URL для анализа
            
        Returns:
            str: Иконка сервиса
        """
        try:
            service_name, service_info = cls.detect_service(url)
            if service_info and 'icon' in service_info:
                return service_info['icon']
        except Exception as e:
            logger.error(f"Ошибка при получении иконки для {url}: {e}")
        
        return '🌐'
    
    @classmethod
    def extract_video_id(cls, url: str) -> Optional[str]:
        """
        Извлекает ID видео из URL (полезно для некоторых сервисов).
        
        Args:
            url (str): URL видео
            
        Returns:
            Optional[str]: ID видео или None
        """
        try:
            parsed = urlparse(url.lower())
            
            # YouTube
            if 'youtube.com' in parsed.netloc:
                if 'watch' in parsed.path:
                    return parse_qs(parsed.query).get('v', [None])[0]
                elif 'embed' in parsed.path:
                    return parsed.path.split('/')[-1]
            elif 'youtu.be' in parsed.netloc:
                return parsed.path.lstrip('/')
            
            # Для других сервисов можно добавить аналогичную логику
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении ID видео из {url}: {e}")
        
        return None
    
    @classmethod
    def is_playlist(cls, url: str) -> bool:
        """
        Проверяет, является ли URL плейлистом.
        
        Args:
            url (str): URL для проверки
            
        Returns:
            bool: True, если это плейлист
        """
        try:
            url_lower = url.lower()
            
            # YouTube плейлисты
            if 'youtube.com' in url_lower and 'list=' in url_lower:
                return True
            
            # Можно добавить проверки для других сервисов
            
        except Exception as e:  
            logger.error(f"Ошибка при проверке плейлиста {url}: {e}")
        
        return False
    
    @classmethod
    def check_url_accessibility(cls, url: str, timeout: int = 10) -> bool:
        """
        Проверяет доступность URL (опциональная функция).
        
        Args:
            url (str): URL для проверки
            timeout (int): Таймаут в секундах
            
        Returns:
            bool: True, если URL доступен
        """
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code < 400
        except Exception as e:
            logger.warning(f"URL недоступен {url}: {e}")
            return False