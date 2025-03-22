import json
import re
import pygame

from widgetClasses.widgets import Button, ButtonStyle, FlashTextPanel, Video


class Comix:

    def __init__(self, screen, scenarios_root, staticfiles_root):
        pygame.init()
        pygame.mixer.init()

        self.null_sign = 0
        self.width, self.height = screen.get_size()
        self.screen = screen
        self.scenario = f'{scenarios_root}/main.txt'
        self.staticfiles_root = staticfiles_root
        self.scenarios_root = scenarios_root
        self.command_number = 0
        self.choice_buttons = pygame.sprite.Group()

        #widgets
        self.text_panel = None
        self.video = None
        self.background = None

        self.process_frame()


    def process_events(self, events):

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_LEFT and not self.choice_buttons and not self.video:
                    if self.text_panel:
                        # дописать выводимый текст до конца
                        if self.text_panel.text_index < len(self.text_panel.text):
                            self.text_panel.text_index = len(self.text_panel.text) - 1
                            continue
                    # следующий фрейм
                    self.next_frame()
                    return
        self.choice_buttons.update(events)

    def process_function(self, str_fnc):
        fnc = re.search(r'^(.+)\(.*\)', str_fnc).group(1)
        fnc_params = []
        for param in re.split(r'\s*,\s*', re.search(r'\(([^()]*)\)', str_fnc).group(1).strip()):
            if param.isdigit():
                fnc_params.append(int(param))
            elif re.match(r'^".*"$', param):
                fnc_params.append(param[1:-1])
            else:
                fnc_params.append(param)
        if fnc == 'goto':
            #fnc:goto("new_file.txt", 5)
            self.command_number = fnc_params[-1] if isinstance(fnc_params[-1], int) else 0
            scenario = fnc_params[0] if isinstance(fnc_params[0], str) else None
            if scenario:
                self.scenario = f'{self.scenarios_root}{scenario}'
            self.process_frame()

    def process_frame(self):
        with open(self.scenario, encoding='utf-8') as file:
            frames = [frame for frame in re.split(r'^\d+|(?:\n\d+\n)', ''.join(file.readlines())) if frame]

        current_frame = frames[self.command_number]
        commands = {}
        for command in current_frame.split('\n'):
            if command:
                key, value = command.split(':', 1)
                key = key.strip()
                commands[key] = []
                for params in re.split(r'\s*\|\s*', value.strip()):
                    param_list = []
                    regex = r'\s*,\s*' + ''.join([r'(?=(?:(?:[^{left}\\]|(?:\\{left}))*{right}(?:[^{right}\\]|(?:\\{right}))*{left})*(?!(?:[^{left}\\]|(?:\\{left}))*{right}))'.format(left=sign[0],right=sign[1]) for sign in [['"', '"'], [r'\[', r'\]'], [r'\(', r'\)']] ])

                    for param in re.split(regex, params):
                        if param[0].startswith('['):
                            param_list.append(json.loads(param))
                        elif param[0].startswith('"'):
                            param_list.append(param[1:-1])
                        elif param.isdigit():
                            param_list.append(int(param))
                        else:
                            param_list.append(param)
                    commands[key].append(param_list)

        if 'author' in commands and 'character' in commands: raise Exception('Свойства author и character несовместимы!')

        if 'background' in commands:
            self.background = pygame.transform.scale(pygame.image.load(f'{self.staticfiles_root}{commands['background'][0][0]}'), (self.width, self.height))
        if 'choice' in commands:


            def delete_choice_buttons(func):
                def inner(*args, **kwargs):
                    self.choice_buttons.empty()
                    return func(*args, **kwargs)

                return inner
            for command_params in commands['choice']:
                func, text, position, size, color, font_size = command_params
                button_styles = ButtonStyle(color, [color[0]//2, color[1] // 2, color[2] // 2], pygame.font.SysFont('comicsans', font_size), outline=(0, 0, 0))
                rect = pygame.Rect(self.width * position[0], self.height * position[1], self.width * size[0], self.height * size[1])

                button = Button(button_styles, rect, text=text, callback=delete_choice_buttons(self.process_function), str_fnc=func )
                self.choice_buttons.add(button)
        if 'fnc' in commands:
            self.process_function(commands['fnc'][0][0])
        if 'author' in commands:
            if commands['author'][0][0] == self.null_sign:
                self.text_panel = None
            else:
                place, text = commands['author'][0]

                panel_height = 200
                author_panel = pygame.Surface((self.width, panel_height), flags=pygame.SRCALPHA)
                author_panel.set_alpha(230)
                position = (0,0) if place == 'top' else (0, self.height - panel_height) if place == 'bottom' else None
                if not position: raise Exception('В местоположении надо писать top либо bottom!')
                self.text_panel = FlashTextPanel(self.screen, text, 40, author_panel, position)
        elif 'character' in commands:
            if commands['character'][0][0] == self.null_sign:
                self.text_panel = None
            else:
                text, pos, size, color, fontsize = commands['character'][0]
                self.text_panel = FlashTextPanel(self.screen, text, fontsize, pygame.Surface([self.width * size[0], self.height * size[1]], flags=pygame.SRCALPHA), [self.width * pos[0], self.height * pos[1]], size=[self.width * size[0], self.height * size[1]], color=color)
        if 'video' in commands:
            self.video = Video(commands['video'][0][0], (self.width, self.height))
        if 'sound' in commands:
            if commands['sound'][0][0] == self.null_sign:
                pygame.mixer.music.stop()
            else:
                loops = 0
                if len(commands['sound'][0]) == 2: loops = -1 if commands['sound'][0][-1] == 'loop' else 0
                pygame.mixer.music.load(self.staticfiles_root + commands['sound'][0][0])
                pygame.mixer.music.play(loops=loops)

    def next_frame(self):
        self.video = None
        with open(self.scenario, encoding='utf-8') as file:
            frames = [frame for frame in re.split(r'^\d+|(?:\n\d+\n)', ''.join(file.readlines())) if frame]

        if len(frames) - 1 <= self.command_number: exit()
        self.command_number += 1

        return self.process_frame()

    def update_screen(self):
        if not self.video:
            self.screen.blit(self.background, (0, 0))

        if self.choice_buttons:
            self.choice_buttons.draw(self.screen)

        if self.text_panel:
            self.text_panel.draw()
        if self.video:
            if self.video.update(self.screen): self.next_frame()
        pygame.display.flip()
