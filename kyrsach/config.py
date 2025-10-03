import tkinter as tk
from tkinter import ttk
import math


class AppConfig:
    APP_NAME = "Video Downloader Pro"
    VERSION = "2.1.0"
    AUTHOR = "Курсовая работа 2025"
    DOWNLOAD_FOLDER = "downloads"
    
    # Обновленная цветовая схема с градиентами
    COLORS = {
        'primary': '#6366f1',
        'primary_dark': '#4f46e5',
        'primary_light': '#818cf8',
        'secondary': '#8b5cf6',
        'secondary_dark': '#7c3aed',
        'accent': '#06b6d4',
        'accent_dark': '#0891b2',
        'success': '#10b981',
        'success_dark': '#059669',
        'danger': '#ef4444',
        'danger_dark': '#dc2626',
        'warning': '#f59e0b',
        'warning_dark': '#d97706',
        'info': '#3b82f6',
        'info_dark': '#2563eb',
        
        # Нейтральные цвета
        'white': '#ffffff',
        'gray_50': '#f9fafb',
        'gray_100': '#f3f4f6',
        'gray_200': '#e5e7eb',
        'gray_300': '#d1d5db',
        'gray_400': '#9ca3af',
        'gray_500': '#6b7280',
        'gray_600': '#4b5563',
        'gray_700': '#374151',
        'gray_800': '#1f2937',
        'gray_900': '#111827',
        
        # Дополнительные цвета для эффектов
        'shadow': 'rgba(0, 0, 0, 0.1)',
        'border': '#e5e7eb',
        'hover_overlay': 'rgba(255, 255, 255, 0.1)'
    }
    
    SUPPORTED_SERVICES = {
        'YouTube': {
            'patterns': [r'youtube\.com', r'youtu\.be'],
            'icon': '🎥',
            'color': '#ff0000',
            'formats': ['MP4', 'MP3']
        },
        'TikTok': {
            'patterns': [r'tiktok\.com'],
            'icon': '🎵',
            'color': '#000000',
            'formats': ['MP4', 'MP3']
        },
        'Instagram': {
            'patterns': [r'instagram\.com'],
            'icon': '📸',
            'color': '#e4405f',
            'formats': ['MP4', 'MP3']
        },
        'SoundCloud': {
            'patterns': [r'soundcloud\.com'],
            'icon': '🎶',
            'color': '#ff5500',
            'formats': ['MP3']
        },
        'Twitter/X': {
            'patterns': [r'twitter\.com', r'x\.com'],
            'icon': '🐦',
            'color': '#1da1f2',
            'formats': ['MP4', 'MP3']
        },
        'Facebook': {
            'patterns': [r'facebook\.com', r'fb\.watch'],
            'icon': '👥',
            'color': '#1877f2',
            'formats': ['MP4', 'MP3']
        },
        'Twitch': {
            'patterns': [r'twitch\.tv'],
            'icon': '🎮',
            'color': '#9146ff',
            'formats': ['MP4', 'MP3']
        },
        'Vimeo': {
            'patterns': [r'vimeo\.com'],
            'icon': '📹',
            'color': '#1ab7ea',
            'formats': ['MP4', 'MP3']
        }
    }
    
    VIDEO_QUALITIES = {
        "🏆 4K Ultra HD": "best[height<=2160]",
        "🎬 1080p Full HD": "best[height<=1080]", 
        "📺 720p HD": "best[height<=720]",
        "📱 480p": "best[height<=480]",
        "💾 360p (экономия)": "best[height<=360]",
        "⚡ Автоматически": "best"
    }
