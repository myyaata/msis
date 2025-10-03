import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import yt_dlp
import sys
import platform
from config import AppConfig
from url_validator import URLValidator
from download_manager import DownloadManager
from gui_components import (
    ModernFrame, ModernButton, ModernEntry, StatusIndicator,
    ModernTreeview, InfoDialog
)

if platform.system() == 'Darwin':
    try:
        from Foundation import NSBundle
        bundle = NSBundle.mainBundle()
        if bundle:
            info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
            if info:
                info['NSHighResolutionCapable'] = True
    except ImportError:
        pass

class VideoDownloaderApp:
    """Главное приложение Video Downloader Pro"""

    def __init__(self):
        """Инициализация приложения"""
        self.root = tk.Tk()
        self.setup_window()
        self.create_styles()
        self.create_widgets()

        self.download_manager = DownloadManager(
            progress_callback=self.update_progress,
            completion_callback=self.download_completed
        )
        self.download_items = {}
        self.url_change_timer = None

    def setup_window(self):
        """Настройка главного окна"""
        self.root.title(f"{AppConfig.APP_NAME} v{AppConfig.VERSION}")
        self.root.geometry("1100x800")
        self.root.minsize(900, 600)
        self.root.configure(bg=AppConfig.COLORS['gray_100'])

        self.center_window()

        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self):
        """Центрирует окно на экране"""
        self.root.update_idletasks()
        width = 1100
        height = 800
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_styles(self):
        """Создает стили для ttk виджетов"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.style.configure('Title.TLabel',
                            font=('Arial', 24, 'bold'),
                            foreground=AppConfig.COLORS['primary'],
                            background=AppConfig.COLORS['white'])

        self.style.configure('Subtitle.TLabel',
                            font=('Arial', 12),
                            foreground=AppConfig.COLORS['gray_600'],
                            background=AppConfig.COLORS['white'])

        self.style.configure('Header.TLabel',
                            font=('Arial', 14, 'bold'),
                            foreground=AppConfig.COLORS['gray_800'],
                            background=AppConfig.COLORS['white'])

        self.style.configure('Modern.TCombobox',
                            fieldbackground=AppConfig.COLORS['white'],
                            borderwidth=1,
                            relief='solid')

    def create_widgets(self):
        """Создает все виджеты приложения"""
        main_container = ModernFrame(self.root, bg_color=AppConfig.COLORS['gray_100'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)

        self.create_header(main_container)
        self.create_url_panel(main_container)
        self.create_settings_panel(main_container)
        self.create_downloads_panel(main_container)
        self.create_status_bar(main_container)

    def create_header(self, parent):
        """Создает заголовок приложения"""
        header_frame = ModernFrame(parent, bg_color=AppConfig.COLORS['white'])
        header_frame.pack(fill='x', pady=(0, 20))

        # Увеличиваем высоту градиентной рамки
        gradient_frame = tk.Frame(header_frame, bg=AppConfig.COLORS['primary'], height=150)
        gradient_frame.pack(fill='x')
        gradient_frame.pack_propagate(False)

        content_frame = tk.Frame(gradient_frame, bg=AppConfig.COLORS['primary'])
        content_frame.pack(expand=True, fill='both', padx=30, pady=25)

        title_label = tk.Label(
            content_frame,
            text="🎥 Video Downloader Pro",
            font=('Arial', 28, 'bold'),
            fg='white',
            bg=AppConfig.COLORS['primary']
        )
        title_label.pack()

        subtitle_label = tk.Label(
            content_frame,
            text="Современное решение для загрузки медиа-контента",
            font=('Arial', 13),
            fg='white',
            bg=AppConfig.COLORS['primary']
        )
        subtitle_label.pack(pady=(8, 20))

        # Создаем рамку для сервисов с прокруткой если нужно
        services_frame = tk.Frame(content_frame, bg=AppConfig.COLORS['primary'])
        services_frame.pack(fill='x')

        # Разбиваем сервисы на строки если их много
        services_list = [f"{info['icon']} {name}" for name, info in AppConfig.SUPPORTED_SERVICES.items()]

        # Если сервисов много, разбиваем на 2 строки
        if len(services_list) > 4:
            mid = len(services_list) // 2
            first_row = " • ".join(services_list[:mid])
            second_row = " • ".join(services_list[mid:])

            services_label1 = tk.Label(
                services_frame,
                text=f"Поддерживаемые сервисы: {first_row}",
                font=('Arial', 11),
                fg='white',
                bg=AppConfig.COLORS['primary']
            )
            services_label1.pack()

            services_label2 = tk.Label(
                services_frame,
                text=second_row,
                font=('Arial', 11),
                fg='white',
                bg=AppConfig.COLORS['primary']
            )
            services_label2.pack(pady=(2, 0))
        else:
            services_text = " • ".join(services_list)
            services_label = tk.Label(
                services_frame,
                text=f"Поддерживаемые сервисы: {services_text}",
                font=('Arial', 11),
                fg='white',
                bg=AppConfig.COLORS['primary']
            )
            services_label.pack()

    def create_url_panel(self, parent):
        """Создает панель для ввода URL"""
        url_frame = ModernFrame(parent, bg_color=AppConfig.COLORS['white'])
        url_frame.pack(fill='x', pady=(0, 20))

        section_frame = tk.Frame(url_frame, bg=AppConfig.COLORS['white'])
        section_frame.pack(fill='x', padx=30, pady=(20, 15))

        title_label = tk.Label(
            section_frame,
            text="🔗 Добавить новую загрузку",
            font=('Arial', 16, 'bold'),
            fg=AppConfig.COLORS['gray_800'],
            bg=AppConfig.COLORS['white']
        )
        title_label.pack(side='left')

        input_frame = tk.Frame(url_frame, bg=AppConfig.COLORS['white'])
        input_frame.pack(fill='x', padx=30, pady=(0, 15))
        input_frame.columnconfigure(1, weight=1)

        url_label = tk.Label(
            input_frame,
            text="Ссылка:",
            font=('Arial', 11, 'bold'),
            fg=AppConfig.COLORS['gray_700'],
            bg=AppConfig.COLORS['white']
        )
        url_label.grid(row=0, column=0, sticky='w', padx=(0, 15))

        self.url_var = tk.StringVar()
        self.url_entry = ModernEntry(
            input_frame,
            textvariable=self.url_var,
            placeholder="Вставьте ссылку на видео или аудио..."
        )
        self.url_entry.grid(row=0, column=1, sticky='ew', padx=(0, 15))

        self.url_entry.bind('<KeyRelease>', self.on_url_change)
        self.url_entry.bind('<Control-v>', self.on_paste)
        self.url_entry.bind('<Button-3>', self.show_url_context_menu)

        self.info_button = ModernButton(
            input_frame,
            "📋 Инфо",
            command=self.get_video_info,
            style='info'
        )
        self.info_button.grid(row=0, column=2)

        self.service_indicator = StatusIndicator(url_frame)
        self.service_indicator.pack(anchor='w', padx=30, pady=(0, 20))
        self.service_indicator.set_status('default', "Вставьте ссылку для определения сервиса")

    def create_settings_panel(self, parent):
        """Создает панель настроек загрузки"""
        settings_frame = ModernFrame(parent, bg_color=AppConfig.COLORS['white'])
        settings_frame.pack(fill='x', pady=(0, 20))

        title_frame = tk.Frame(settings_frame, bg=AppConfig.COLORS['white'])
        title_frame.pack(fill='x', padx=30, pady=(20, 15))

        title_label = tk.Label(
            title_frame,
            text="⚙️ Настройка загрузки",
            font=('Arial', 16, 'bold'),
            fg=AppConfig.COLORS['gray_800'],
            bg=AppConfig.COLORS['white']
        )
        title_label.pack(side='left')

        grid_frame = tk.Frame(settings_frame, bg=AppConfig.COLORS['white'])
        grid_frame.pack(fill='x', padx=30, pady=(0, 20))
        grid_frame.columnconfigure(1, weight=1)
        grid_frame.columnconfigure(3, weight=1)

        tk.Label(
            grid_frame,
            text="📱 Тип файла:",
            font=('Arial', 11, 'bold'),
            fg=AppConfig.COLORS['gray_700'],
            bg=AppConfig.COLORS['white']
        ).grid(row=0, column=0, sticky='w', padx=(0, 15), pady=10)

        self.type_var = tk.StringVar(value="Видео (MP4)")
        type_combo = ttk.Combobox(
            grid_frame,
            textvariable=self.type_var,
            values=["Видео (MP4)", "Только аудио (MP3)"],
            state="readonly",
            style='Modern.TCombobox',
            width=20,
            font=('Arial', 11)
        )
        type_combo.grid(row=0, column=1, sticky='w', padx=(0, 30), pady=10)

        tk.Label(
            grid_frame,
            text="⚡ Качество:",
            font=('Arial', 11, 'bold'),
            fg=AppConfig.COLORS['gray_700'],
            bg=AppConfig.COLORS['white']
        ).grid(row=0, column=2, sticky='w', padx=(0, 15), pady=10)

        self.quality_var = tk.StringVar(value="🏆 Лучшее качество")
        quality_combo = ttk.Combobox(
            grid_frame,
            textvariable=self.quality_var,
            values=list(AppConfig.VIDEO_QUALITIES.keys()),
            state="readonly",
            style='Modern.TCombobox',
            width=20,
            font=('Arial', 11)
        )
        quality_combo.grid(row=0, column=3, sticky='w', pady=10)

        tk.Label(
            grid_frame,
            text="📁 Папка:",
            font=('Arial', 11, 'bold'),
            fg=AppConfig.COLORS['gray_700'],
            bg=AppConfig.COLORS['white']
        ).grid(row=1, column=0, sticky='w', padx=(0, 15), pady=10)

        folder_frame = tk.Frame(grid_frame, bg=AppConfig.COLORS['white'])
        folder_frame.grid(row=1, column=1, columnspan=2, sticky='ew', padx=(0, 15), pady=10)
        folder_frame.columnconfigure(0, weight=1)

        self.folder_var = tk.StringVar(value=AppConfig.DOWNLOAD_FOLDER)
        folder_entry = ModernEntry(folder_frame, textvariable=self.folder_var)
        folder_entry.grid(row=0, column=0, sticky='ew', padx=(0, 10))

        folder_button = ModernButton(
            folder_frame,
            "📂 Обзор",
            command=self.choose_folder,
            style='secondary'
        )
        folder_button.grid(row=0, column=1)

        self.download_button = ModernButton(
            grid_frame,
            "⬇️ НАЧАТЬ ЗАГРУЗКУ",
            command=self.start_download,
            style='success',
            width=18
        )
        self.download_button.grid(row=1, column=3, pady=10)

    def create_downloads_panel(self, parent):
        """Создает панель списка загрузок"""
        downloads_frame = ModernFrame(parent, bg_color=AppConfig.COLORS['white'])
        downloads_frame.pack(fill='both', expand=True)

        header_frame = tk.Frame(downloads_frame, bg=AppConfig.COLORS['white'])
        header_frame.pack(fill='x', padx=30, pady=(20, 15))

        title_label = tk.Label(
            header_frame,
            text="📥 Список загрузок",
            font=('Arial', 16, 'bold'),
            fg=AppConfig.COLORS['gray_800'],
            bg=AppConfig.COLORS['white']
        )
        title_label.pack(side='left')

        buttons_frame = tk.Frame(header_frame, bg=AppConfig.COLORS['white'])
        buttons_frame.pack(side='right')

        ModernButton(
            buttons_frame,
            "🗑️ Очистить",
            command=self.clear_downloads,
            style='warning'
        ).pack(side='left', padx=(0, 10))

        ModernButton(
            buttons_frame,
            "📂 Открыть папку",
            command=self.open_downloads_folder,
            style='info'
        ).pack(side='left')

        tree_frame = tk.Frame(downloads_frame, bg=AppConfig.COLORS['white'])
        tree_frame.pack(fill='both', expand=True, padx=30, pady=(0, 20))

        columns = ('service', 'url', 'type', 'status', 'progress', 'speed', 'filename')
        self.downloads_tree = ModernTreeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=10
        )

        headings = {
            'service': '🌐 Сервис',
            'url': '🔗 URL',
            'type': '📱 Тип',
            'status': '📊 Статус',
            'progress': '⚡ Прогресс',
            'speed': '🚀 Скорость',
            'filename': '📄 Файл'
        }

        widths = {
            'service': 100,
            'url': 200,
            'type': 120,
            'status': 120,
            'progress': 100,
            'speed': 100,
            'filename': 250
        }

        for col in columns:
            self.downloads_tree.heading(col, text=headings[col])
            self.downloads_tree.column(col, width=widths[col])

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.downloads_tree.yview)
        self.downloads_tree.configure(yscrollcommand=scrollbar.set)

        self.downloads_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.create_context_menu()

    def create_status_bar(self, parent):
        """Создает статусную строку"""
        status_frame = tk.Frame(parent, bg=AppConfig.COLORS['gray_200'], height=50)
        status_frame.pack(fill='x', pady=(20, 0))
        status_frame.pack_propagate(False)

        content_frame = tk.Frame(status_frame, bg=AppConfig.COLORS['gray_200'])
        content_frame.pack(fill='both', expand=True, padx=20, pady=12)

        self.status_var = tk.StringVar(value="✅ Готов к работе")
        status_label = tk.Label(
            content_frame,
            textvariable=self.status_var,
            font=('Arial', 10),
            fg=AppConfig.COLORS['gray_700'],
            bg=AppConfig.COLORS['gray_200']
        )
        status_label.pack(side='left', anchor='w')

        about_button = ModernButton(
            content_frame,
            "ℹ️ О программе",
            command=self.show_about,
            style='info',
            width=15
        )
        about_button.pack(side='right', anchor='e')

    def create_context_menu(self):
        """Создает контекстное меню для таблицы загрузок"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="📂 Открыть файл", command=self.open_file)
        self.context_menu.add_command(label="📁 Показать в папке", command=self.show_in_folder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="❌ Удалить из списка", command=self.remove_from_list)

        self.downloads_tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Показывает контекстное меню"""
        item = self.downloads_tree.selection()
        if item:
            self.context_menu.post(event.x_root, event.y_root)

    def show_url_context_menu(self, event):
        """Показывает контекстное меню для поля URL"""
        url_menu = tk.Menu(self.root, tearoff=0)
        url_menu.add_command(label="Вставить", command=self.paste_url)
        url_menu.add_command(label="Очистить", command=self.clear_url)

        try:
            url_menu.post(event.x_root, event.y_root)
        finally:
            url_menu.grab_release()

    def on_url_change(self, event=None):
        """Обработчик изменения URL с дебаунсингом"""
        if self.url_change_timer:
            self.root.after_cancel(self.url_change_timer)

        self.url_change_timer = self.root.after(300, self._process_url_change)

    def _process_url_change(self):
        """Обрабатывает изменение URL"""
        url = self.url_entry.get_real_text().strip()

        if len(url) < 10:
            self.service_indicator.set_status('default', "Вставьте ссылку для определения сервиса")
            return

        if URLValidator.validate_url(url):
            service_name, service_info = URLValidator.detect_service(url)
            if service_info:
                icon = service_info['icon']
                self.service_indicator.set_status(
                    'success',
                    f"{icon} {service_name} - Поддерживается ✅"
                )
            else:
                self.service_indicator.set_status(
                    'error',
                    "❌ Сервис не поддерживается"
                )
        else:
            self.service_indicator.set_status(
                'error',
                "❌ Неверный формат URL"
            )

    def on_paste(self, event):
        """Обработчик вставки через Ctrl+V"""
        self.root.after(50, self._process_url_change)

    def paste_url(self):
        """Вставляет URL из буфера обмена"""
        try:
            clipboard_text = self.root.clipboard_get()
            self.url_var.set(clipboard_text)
            if self.url_entry.placeholder_active:
                self.url_entry._hide_placeholder()
            self._process_url_change()
        except:
            pass

    def clear_url(self):
        """Очищает поле URL"""
        self.url_var.set("")
        self.url_entry._show_placeholder()
        self._process_url_change()

    def get_video_info(self):
        """Получает информацию о видео"""
        url = self.url_entry.get_real_text().strip()

        if not url:
            messagebox.showwarning("Предупреждение", "Введите URL видео")
            return

        if not URLValidator.validate_url(url):
            messagebox.showerror("Ошибка", "Неверный формат URL")
            return

        self.status_var.set("🔄 Получение информации...")
        self.info_button.set_enabled(False)

        def get_info_worker():
            error_message = None
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                    'skip_download': True
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)

                title = info.get('title', 'Без названия')
                uploader = info.get('uploader', 'Неизвестно')
                duration = info.get('duration', 0)
                view_count = info.get('view_count', 0)

                if duration:
                    hours = duration // 3600
                    minutes = (duration % 3600) // 60
                    seconds = duration % 60
                    if hours:
                        duration_str = f"{hours}:{minutes:02d}:{seconds:02d}"
                    else:
                        duration_str = f"{minutes}:{seconds:02d}"
                else:
                    duration_str = "Неизвестно"

                if view_count:
                    if view_count >= 1000000:
                        views_str = f"{view_count/1000000:.1f}M просмотров"
                    elif view_count >= 1000:
                        views_str = f"{view_count/1000:.1f}K просмотров"
                    else:
                        views_str = f"{view_count} просмотров"
                else:
                    views_str = "Неизвестно"

                service_name, _ = URLValidator.detect_service(url)

                details = {
                    "📺 Название": title,
                    "👤 Автор": uploader,
                    "⏱️ Длительность": duration_str,
                    "👀 Просмотры": views_str,
                    "🌐 Сервис": service_name
                }

                self.root.after(0, lambda: (
                    self.status_var.set("✅ Информация получена"),
                    self.info_button.set_enabled(True),
                    InfoDialog(self.root, "Информация о видео", details).show()
                ))

            except Exception as e:
                error_message = str(e)
                self.root.after(0, lambda: (
                    self.status_var.set("❌ Ошибка"),
                    self.info_button.set_enabled(True),
                    messagebox.showerror("Ошибка", f"Не удалось получить информацию: {error_message}")
                ))

        threading.Thread(target=get_info_worker, daemon=True).start()

    def start_download(self):
        """Основной метод для начала загрузки видео/аудио.
        Обрабатывает пользовательский ввод, валидирует данные,
        инициирует загрузку и обновляет интерфейс."""

        # Получаем данные из полей ввода
        url = self.url_entry.get_real_text().strip()  # URL из текстового поля
        download_type = self.type_var.get()  # Тип загрузки (аудио/видео)
        quality = self.quality_var.get()  # Выбранное качество
        folder = self.folder_var.get().strip()  # Папка для сохранения

        # Валидация URL
        if not url:
            messagebox.showwarning("Предупреждение", "Введите URL видео")
            return

        # Проверка корректности формата URL
        if not URLValidator.validate_url(url):
            messagebox.showerror("Ошибка", "Неверный формат URL")
            return

        # Проверка существования папки для сохранения
        if not os.path.exists(folder):
            messagebox.showerror("Ошибка", "Указанная папка не существует")
            return

        # Обновление статуса в интерфейсе
        self.status_var.set("🔄 Подготовка к загрузке...")
        self.download_button.set_enabled(False)  # Блокировка кнопки во время загрузки

        # Определение параметров загрузки
        is_audio = (download_type == "Только аудио (MP3)")  # Флаг загрузки аудио
        quality_key = AppConfig.VIDEO_QUALITIES.get(quality, 'best')  # Ключ качества

        # Определение сервиса (YouTube и т.д.)
        service_name, _ = URLValidator.detect_service(url)

        # Добавление новой записи в таблицу загрузок
        tree_item_id = self.downloads_tree.insert('', 'end', values=(
            service_name,  # Название сервиса
            url,  # URL видео
            download_type,  # Тип загрузки
            'Ожидает',  # Статус
            '0%',  # Прогресс
            '0 KB/s',  # Скорость
            'Ожидает...'  # Доп. информация
        ))

        # Запуск загрузки через менеджер загрузок
        download_id = self.download_manager.start_download(
            url=url,
            output_path=folder,
            is_audio=is_audio,
            quality=quality
        )

        # Сохранение связи между ID загрузки и элементом таблицы
        self.download_items[download_id] = tree_item_id

        # Обновление интерфейса после запуска загрузки
        self.root.after(0, lambda: (
            self.status_var.set("⬇️ Загрузка началась"),  # Обновление статуса
            self.download_button.set_enabled(True)  # Разблокировка кнопки
        ))
    
    def update_progress(self, download_id, progress, speed, status, filename):
        """Обновляет прогресс загрузки в таблице"""
        tree_item_id = self.download_items.get(download_id)
        if tree_item_id and self.downloads_tree.exists(tree_item_id):
            self.downloads_tree.item(tree_item_id, values=(
                self.downloads_tree.item(tree_item_id, 'values')[0],  # service
                self.downloads_tree.item(tree_item_id, 'values')[1],  # url
                self.downloads_tree.item(tree_item_id, 'values')[2],  # type
                status,
                f"{progress:.1f}%",
                f"{speed:.1f} KB/s" if speed else "0 KB/s",
                filename
            ))
    
    def download_completed(self, download_id, success, message):
        """Обрабатывает завершение загрузки"""
        tree_item_id = self.download_items.get(download_id)
        if tree_item_id and self.downloads_tree.exists(tree_item_id):
            values = list(self.downloads_tree.item(tree_item_id, 'values'))
            values[3] = 'Завершено' if success else 'Ошибка'
            self.downloads_tree.item(tree_item_id, values=values)
        
        self.root.after(0, lambda: (
            self.status_var.set(f"{'✅ Загрузка завершена' if success else f'❌ Ошибка: {message}'}"),
            self.download_button.set_enabled(True)
        ))
    
    def choose_folder(self):
        """Открывает диалог выбора папки для сохранения"""
        folder = filedialog.askdirectory(initialdir=self.folder_var.get(), title="Выберите папку для сохранения")
        if folder:
            self.folder_var.set(folder)
    
    def clear_downloads(self):
        """Очищает список загрузок"""
        confirm = messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить список загрузок?")
        if confirm:
            for item in self.downloads_tree.get_children():
                self.downloads_tree.delete(item)
            self.download_items.clear()
            self.status_var.set("✅ Список загрузок очищен")
    
    def open_downloads_folder(self):
        """Открывает папку с загрузками"""
        folder = self.folder_var.get()
        if os.path.exists(folder):
            import platform
            if platform.system() == "Windows":
                os.startfile(folder)
            elif platform.system() == "Darwin":
                os.system(f"open '{folder}'")
            else:
                os.system(f"xdg-open '{folder}'")
        else:
            messagebox.showerror("Ошибка", "Папка не существует")
    
    def open_file(self):
        """Открывает выбранный файл"""
        selected = self.downloads_tree.selection()
        if selected:
            filename = self.downloads_tree.item(selected[0], 'values')[6]
            filepath = os.path.join(self.folder_var.get(), filename)
            if os.path.exists(filepath):
                import platform
                if platform.system() == "Windows":
                    os.startfile(filepath)
                elif platform.system() == "Darwin":
                    os.system(f"open '{filepath}'")
                else:
                    os.system(f"xdg-open '{filepath}'")
            else:
                messagebox.showerror("Ошибка", "Файл не найден")
    
    def show_in_folder(self):
        """Показывает файл в папке"""
        selected = self.downloads_tree.selection()
        if selected:
            filename = self.downloads_tree.item(selected[0], 'values')[6]
            filepath = os.path.join(self.folder_var.get(), filename)
            if os.path.exists(filepath):
                import platform
                if platform.system() == "Windows":
                    os.system(f'explorer /select,"{filepath}"')
                elif platform.system() == "Darwin":
                    os.system(f"open -R '{filepath}'")
                else:
                    os.system(f"xdg-open '{os.path.dirname(filepath)}'")
            else:
                messagebox.showerror("Ошибка", "Файл не найден")
    
    def remove_from_list(self):
        """Удаляет выбранную загрузку из списка"""
        selected = self.downloads_tree.selection()
        if selected:
            for item in selected:
                download_id = next((k for k, v in self.download_items.items() if v == item), None)
                if download_id:
                    del self.download_items[download_id]
                self.downloads_tree.delete(item)
            self.status_var.set("✅ Элемент удален из списка")
    
    def show_about(self):
        """Показывает окно 'О программе'"""
        about_info = {
            "🎥 Приложение": f"{AppConfig.APP_NAME} v{AppConfig.VERSION}",
            "📝 Описание": "Современное приложение для загрузки видео и аудио",
            "👨‍💻 Автор": AppConfig.AUTHOR,
            "📅 Год": "2025"
        }
        InfoDialog(self.root, "О программе", about_info).show()
    
    def on_closing(self):
        """Обработчик закрытия приложения"""
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.download_manager.stop_all()
            self.root.destroy()

if __name__ == "__main__":
    app = VideoDownloaderApp()
    app.root.mainloop()