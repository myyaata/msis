import tkinter as tk
from tkinter import ttk
import math


class ModernButton(tk.Button):
    """Современная кнопка с градиентом и анимацией"""

    def __init__(self, parent, text, command=None, style='primary', width=None, **kwargs):
        self.style_name = style
        self.original_text = text
        self.is_enabled = True

        # Определяем цвета для каждого стиля
        style_colors = {
            'primary': ('#6366f1', '#4f46e5', '#ffffff'),
            'secondary': ('#8b5cf6', '#7c3aed', '#ffffff'),
            'success': ('#10b981', '#059669', '#ffffff'),
            'danger': ('#ef4444', '#dc2626', '#ffffff'),
            'warning': ('#f59e0b', '#d97706', '#ffffff'),
            'info': ('#3b82f6', '#2563eb', '#ffffff')
        }

        self.bg_color, self.hover_color, self.text_color = style_colors.get(style, style_colors['primary'])

        super().__init__(
            parent,
            text=text,
            command=command,
            bg=self.bg_color,
            fg=self.text_color,
            font=('Arial', 10, 'bold'),
            bd=0,
            relief='flat',
            cursor='hand2',
            width=width if width else len(text) + 2,
            height=2,
            highlightthickness=0,
            borderwidth=0,
            activebackground=self.hover_color,
            activeforeground=self.text_color,
            **kwargs
        )

        # Для macOS убираем системное оформление
        try:
            self.configure(highlightbackground=self.bg_color)
        except:
            pass

        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Button-1>', self._on_click)
        self.bind('<ButtonRelease-1>', self._on_release)


class ModernButton(tk.Frame):
    """Современная кнопка с градиентом и анимацией - версия для macOS"""

    def __init__(self, parent, text, command=None, style='primary', width=None, **kwargs):
        self.style_name = style
        self.original_text = text
        self.is_enabled = True
        self.command = command

        # Определяем цвета для каждого стиля
        style_colors = {
            'primary': ('#6366f1', '#4f46e5', '#ffffff'),
            'secondary': ('#8b5cf6', '#7c3aed', '#ffffff'),
            'success': ('#10b981', '#059669', '#ffffff'),
            'danger': ('#ef4444', '#dc2626', '#ffffff'),
            'warning': ('#f59e0b', '#d97706', '#ffffff'),
            'info': ('#3b82f6', '#2563eb', '#ffffff')
        }

        self.bg_color, self.hover_color, self.text_color = style_colors.get(style, style_colors['primary'])

        # Создаем Frame как основу
        super().__init__(
            parent,
            bg=self.bg_color,
            relief='flat',
            bd=0,
            highlightthickness=0,
            cursor='hand2',
            **kwargs
        )

        # Создаем внутренний Label для текста
        self.label = tk.Label(
            self,
            text=text,
            bg=self.bg_color,
            fg=self.text_color,
            font=('Arial', 10, 'bold'),
            cursor='hand2',
            relief='flat',
            bd=0
        )

        # Устанавливаем размеры
        button_width = width if width else max(len(text) + 4, 12)
        self.configure(width=button_width * 8, height=32)
        self.pack_propagate(False)

        self.label.pack(expand=True, fill='both', padx=10, pady=6)

        # Привязываем события к обоим элементам
        for widget in [self, self.label]:
            widget.bind('<Enter>', self._on_enter)
            widget.bind('<Leave>', self._on_leave)
            widget.bind('<Button-1>', self._on_click)
            widget.bind('<ButtonRelease-1>', self._on_release)

    def _on_enter(self, event):
        if self.is_enabled:
            self.configure(bg=self.hover_color)
            self.label.configure(bg=self.hover_color)

    def _on_leave(self, event):
        if self.is_enabled:
            self.configure(bg=self.bg_color)
            self.label.configure(bg=self.bg_color)

    def _on_click(self, event):
        if self.is_enabled:
            # Эффект нажатия - затемняем цвет
            darker_color = self._darken_color(self.hover_color)
            self.configure(bg=darker_color)
            self.label.configure(bg=darker_color)

    def _on_release(self, event):
        if self.is_enabled:
            self.configure(bg=self.hover_color)
            self.label.configure(bg=self.hover_color)
            # Выполняем команду
            if self.command:
                self.command()

    def _darken_color(self, color):
        """Затемняет цвет для эффекта нажатия"""
        try:
            # Простое затемнение путем уменьшения яркости
            if color.startswith('#'):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)

                r = max(0, int(r * 0.8))
                g = max(0, int(g * 0.8))
                b = max(0, int(b * 0.8))

                return f"#{r:02x}{g:02x}{b:02x}"
        except:
            pass
        return color

    def set_enabled(self, enabled):
        """Включает/отключает кнопку"""
        self.is_enabled = enabled
        if enabled:
            self.configure(bg=self.bg_color, cursor='hand2')
            self.label.configure(
                bg=self.bg_color,
                fg=self.text_color,
                cursor='hand2'
            )
        else:
            self.configure(bg='#9ca3af', cursor='arrow')
            self.label.configure(
                bg='#9ca3af',
                fg='#6b7280',
                cursor='arrow'
            )

    def configure(self, **kwargs):
        """Переопределяем configure для совместимости"""
        # Разделяем опции для Frame и Label
        frame_options = {}
        label_options = {}

        for key, value in kwargs.items():
            if key in ['text']:
                label_options[key] = value
            else:
                frame_options[key] = value

        if frame_options:
            super().configure(**frame_options)
        if label_options and hasattr(self, 'label'):
            self.label.configure(**label_options)


class ModernFrame(tk.Frame):
    """Современная рамка с тенью"""

    def __init__(self, parent, bg_color='#ffffff', shadow=True, corner_radius=10, **kwargs):
        super().__init__(parent, bg=bg_color, relief='flat', bd=0, **kwargs)

        if shadow:
            # Создаем эффект тени с помощью дополнительных рамок
            shadow_frame = tk.Frame(parent, bg='#e5e7eb', height=2)
            shadow_frame.place(in_=self, relx=0.02, rely=0.02, relwidth=1, relheight=1)
            self.lift()


class ModernEntry(tk.Entry):
    """Современное поле ввода с placeholder"""

    def __init__(self, parent, placeholder="", textvariable=None, **kwargs):
        self.placeholder = placeholder
        self.placeholder_active = False

        if textvariable is None:
            textvariable = tk.StringVar()

        super().__init__(
            parent,
            textvariable=textvariable,
            font=('Arial', 11),
            bg='#ffffff',
            fg='#374151',
            relief='solid',
            bd=1,
            highlightthickness=2,
            highlightcolor='#6366f1',
            highlightbackground='#e5e7eb',
            insertbackground='#374151',
            **kwargs
        )

        self.textvariable = textvariable

        if placeholder:
            self._show_placeholder()

        self.bind('<FocusIn>', self._on_focus_in)
        self.bind('<FocusOut>', self._on_focus_out)

    def _show_placeholder(self):
        if not self.get():
            self.placeholder_active = True
            self.configure(fg='#9ca3af')
            self.textvariable.set(self.placeholder)

    def _hide_placeholder(self):
        if self.placeholder_active:
            self.placeholder_active = False
            self.configure(fg='#374151')
            self.textvariable.set("")

    def _on_focus_in(self, event):
        if self.placeholder_active:
            self._hide_placeholder()

    def _on_focus_out(self, event):
        if not self.get():
            self._show_placeholder()

    def get_real_text(self):
        """Возвращает реальный текст без placeholder"""
        if self.placeholder_active:
            return ""
        return self.get()


class StatusIndicator(tk.Frame):
    """Индикатор статуса с цветовой кодировкой"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=parent.cget('bg'), **kwargs)

        self.indicator = tk.Label(
            self,
            text="●",
            font=('Arial', 12),
            bg=self.cget('bg')
        )
        self.indicator.pack(side='left', padx=(0, 8))

        self.message = tk.Label(
            self,
            font=('Arial', 10),
            bg=self.cget('bg')
        )
        self.message.pack(side='left')

    def set_status(self, status_type, message):
        """Устанавливает статус и сообщение"""
        colors = {
            'success': '#10b981',
            'error': '#ef4444',
            'warning': '#f59e0b',
            'info': '#3b82f6',
            'default': '#6b7280'
        }

        color = colors.get(status_type, colors['default'])
        self.indicator.configure(fg=color)
        self.message.configure(text=message, fg='#374151')


class ModernTreeview(ttk.Treeview):
    """Современная таблица с улучшенным стилем"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Настройка стилей
        style = ttk.Style()

        # Стиль заголовков
        style.configure(
            'Treeview.Heading',
            background='#f3f4f6',
            foreground='#374151',
            font=('Arial', 10, 'bold'),
            relief='flat'
        )

        # Стиль строк
        style.configure(
            'Treeview',
            background='#ffffff',
            foreground='#374151',
            fieldbackground='#ffffff',
            font=('Arial', 9),
            rowheight=30
        )

        # Альтернативные строки
        self.tag_configure('oddrow', background='#f9fafb')
        self.tag_configure('evenrow', background='#ffffff')

        # Привязываем обновление тегов
        self.bind('<Map>', self._update_row_tags)

    def _update_row_tags(self, event=None):
        """Обновляет теги строк для альтернативной раскраски"""
        for i, item in enumerate(self.get_children()):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.item(item, tags=(tag,))


class InfoDialog:
    """Современное диалоговое окно с информацией"""

    def __init__(self, parent, title, info_dict):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.configure(bg='#ffffff')
        self.dialog.resizable(False, False)

        # Центрируем окно
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Заголовок
        header_frame = tk.Frame(self.dialog, bg='#6366f1', height=60)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text=title,
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#6366f1'
        )
        title_label.pack(expand=True)

        # Содержимое
        content_frame = tk.Frame(self.dialog, bg='#ffffff')
        content_frame.pack(fill='both', expand=True, padx=30, pady=20)

        for key, value in info_dict.items():
            row_frame = tk.Frame(content_frame, bg='#ffffff')
            row_frame.pack(fill='x', pady=8)

            key_label = tk.Label(
                row_frame,
                text=key + ":",
                font=('Arial', 11, 'bold'),
                fg='#374151',
                bg='#ffffff',
                anchor='w'
            )
            key_label.pack(side='left')

            value_label = tk.Label(
                row_frame,
                text=str(value),
                font=('Arial', 11),
                fg='#6b7280',
                bg='#ffffff',
                anchor='w',
                wraplength=300
            )
            value_label.pack(side='right', padx=(20, 0))

        # Кнопка закрытия
        close_button = ModernButton(
            content_frame,
            "Закрыть",
            command=self.dialog.destroy,
            style='primary'
        )
        close_button.pack(pady=(20, 0))

    def show(self):
        """Показывает диалог"""
        # Центрируем относительно родительского окна
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"500x400+{x}+{y}")

        self.dialog.wait_window()