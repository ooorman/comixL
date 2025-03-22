import os.path
import queue
import subprocess

import cv2
import pygame
import threading

class ButtonStyle:
    def __init__(self, color, color_hover, font, outline=None):
        self.color = color
        self.color_hover = color_hover
        self.font = font
        self.outline = outline

class Button(pygame.sprite.Sprite):
    def __init__(self, styles, rect, text='', callback=None, str_fnc=None):
        super().__init__()
        self.text = text
        tmp_rect = pygame.Rect(0, 0, *rect.size)
        self.idle_image = self.create_image(styles.color, styles.outline, text, styles.font, tmp_rect)
        self.hover_image = self.create_image(styles.color_hover, styles.outline, text, styles.font, tmp_rect)
        self.image = self.idle_image
        self.rect = rect

        self.str_fnc = str_fnc
        self.callback = callback
    def create_image(self, color, outline, text, font, rect):
        img = pygame.Surface(rect.size)
        if outline:
            img.fill(outline)
            img.fill(color, rect.inflate(-4, -4))
        else:
            img.fill(color)

        if text != '':
            text_surf = font.render(text, True, pygame.Color('black'))
            text_rect = text_surf.get_rect(center=rect.center)
            img.blit(text_surf, text_rect)
        return img
    def update(self, events):
        pos = pygame.mouse.get_pos()
        hit = self.rect.collidepoint(pos)

        self.image = self.hover_image if hit else self.idle_image
        for event in events:
            if event.type == pygame.MOUSEBUTTONUP and hit:
                return self.callback(self.str_fnc)

class FlashTextPanel:
    def __init__(self, screen, text, font_size, panel, position, size=None, color=None):
        self.color = color
        self.text = text
        self.font = pygame.font.SysFont('Roboto', font_size)
        self.panel = panel
        self.position = position
        self.text_index = 0
        self.text_speed = 0.01
        self.last_update_time = pygame.time.get_ticks()
        self.size = size
        self.is_character_talking = not(size is None)
        self.screen = screen

    def render_text_wrapped(self, color, margin):
        if self.is_character_talking:
            border_width = 2
            pygame.draw.rect(self.panel, (0, 0, 0), pygame.Rect(0, 0, *self.size), border_radius=3)
            pygame.draw.rect(self.panel, (255, 255, 255) or self.color,
                             pygame.Rect(border_width, border_width, self.size[0] - border_width * 2,
                                         self.size[1] - border_width * 2), border_radius=3)
        else:
            self.panel.fill((0, 0, 0, 200))

        words = self.text[:self.text_index].split(' ')
        space_width = self.font.size(' ')[0]
        max_width = self.panel.get_width() - margin[0] * 2
        x, y = margin
        line_height = self.font.get_linesize()

        for word in words:
            word_surface = self.font.render(word, True, color)
            word_width = word_surface.get_size()[0]

            if x + word_width >= max_width:
                x = margin[0]
                y += line_height
            self.panel.blit(word_surface, (x, y))
            x += word_width + space_width

    def draw(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_update_time > self.text_speed * 1000:
            self.last_update_time = current_time
            if self.text_index < len(self.text):
                self.text_index += 1
                self.panel.fill((0, 0, 0, 0))
                if self.is_character_talking:
                    color = (0, 0, 0)
                else:
                    color = (255, 255, 255)
                self.render_text_wrapped(color, (10, 10))
        self.screen.blit(self.panel, self.position)

class Video:
    def __init__(self, path, size):
        if not os.path.exists(path):
            raise Exception(f'Файл "{path}" не найден!')

        self.cap = cv2.VideoCapture(path)
        self.size = size

        # Получение параметров видео
        self.frame_rate = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_duration = 1000 / self.frame_rate

        # Инициализация переменных
        self.surface = None
        self.start_time = None
        self.frame_index = 0
        self.frame_queue = queue.Queue(maxsize=10)  # Буфер для кадров
        self.stop_flag = False

        # Поток для декодирования видео
        self.video_thread = threading.Thread(target=self.decode_frames)
        self.video_thread.start()

        # Поток для воспроизведения звука
        self.sound_thread = threading.Thread(target=self.play_sound, args=(path,))
        self.sound_thread.start()

    def play_sound(self, path):
        sound_path = path.replace('.mp4', '.wav')

        # Извлечение аудио с помощью FFmpeg и перезапись в тот же файл
        command = [
            "ffmpeg", "-i", path, "-vn", "-ar", "44100", "-ac", "2", "-b:a", "192k", sound_path, "-y"
        ]
        subprocess.run(command, stderr=subprocess.DEVNULL)

        pygame.mixer.init()
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()


    def decode_frames(self):
        while not self.stop_flag:
            if self.frame_queue.full():
                continue

            ret, frame = self.cap.read()
            if not ret:
                self.stop_flag = True
                break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, self.size)
            self.frame_queue.put(frame)

        self.cap.release()

    def update(self, screen):
        if self.start_time is None:
            self.start_time = pygame.time.get_ticks()

        # Синхронизация видео с аудио
        current_time = pygame.time.get_ticks() - self.start_time
        expected_frame_index = int(current_time / self.frame_duration)

        if self.frame_index < expected_frame_index:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                self.surface = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
                self.frame_index += 1

        if self.surface:
            screen.blit(self.surface, (0, 0))
