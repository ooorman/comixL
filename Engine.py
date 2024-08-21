import json
import re

import pygame

from widgetClasses.widgets import Button, ButtonStyle, FlashTextPanel


class Comix:

    def __init__(self, screen, scenarios_root, staticfiles_root):
        pygame.init()

        self.width, self.height = screen.get_size()
        self.screen = screen
        self.scenario = f'{scenarios_root}/main.txt'
        self.staticfiles_root = staticfiles_root
        self.scenarios_root = scenarios_root
        self.command_number = 0
        self.choice_buttons = pygame.sprite.Group()
        #widgets
        self.text_panel = None

        self.process_frame()


    def process_events(self, events):

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_LEFT and not self.choice_buttons:
                    if self.text_panel:
                        # дописать выводимый текст до конца
                        if self.text_panel.text_index < len(self.text_panel.text):
                            self.text_panel.text_index = len(self.text_panel.text) - 1
                            continue
                    # следующий фрейм
                    self.command_number += 1
                    self.process_frame()
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
            #fnc:goto("new_file.txt", 5);
            self.command_number = fnc_params[-1] if isinstance(fnc_params[-1], int) else 0
            scenario = fnc_params[0] if isinstance(fnc_params[0], str) else None
            if scenario:
                self.scenario = f'{self.scenarios_root}{scenario}'

            self.process_frame()

    def process_frame(self):

        with open(self.scenario, encoding='utf-8') as file:
            frames = [frame for frame in re.split(r'\d+\n', ''.join(file.readlines())) if frame]
            current_frame = frames[self.command_number].replace('\n', '')
            commands = {}
            for command in current_frame.split(';'):
                if command:
                    key, value = command.split(':', 1)
                    key = key.strip()
                    commands[key] = []
                    for params in re.split(r'\s*\|\s*', value.strip()):
                        param_list = []
                        regex = r'\s*,\s*' + ''.join([r'(?=(?:(?:[^{left}\\]|(?:\\{left}))*{right}(?:[^{right}\\]|(?:\\{right}))*{left})*(?!(?:[^{left}\\]|(?:\\{left}))*{right}))'.format(left=sign[0],right=sign[1]) for sign in [['"', '"'], [r'\[', r'\]'], [r'\(', r'\)']] ])
                        for param in re.split(regex, params):
                            if re.match(r'^[\["]', param):
                                param_list.append(json.loads(param))
                            elif param.isdigit():
                                param_list.append(int(param))
                            else:
                                param_list.append(param)
                        commands[key].append(param_list)
        if 'author' in commands and 'character' in commands: raise Exception('Свойства author и character несовместимы!')

        if 'background' in commands:
            self.background = pygame.transform.scale(pygame.image.load(f'{self.staticfiles_root}{commands['background'][0][0]}'), (self.width, self.height))
        if 'choice' in commands:
            button_styles = ButtonStyle((0, 255, 0), (0, 128, 0), pygame.font.SysFont('comicsans', 18), outline=(0, 0, 0))

            def delete_choice_buttons(func):
                def inner(*args, **kwargs):
                    self.choice_buttons.empty()
                    return func(*args, **kwargs)

                return inner
            for command_params in commands['choice']:
                func, text, position = command_params
                rect = pygame.Rect(*position, 200, 70)

                button = Button(button_styles, rect, text=text, callback=delete_choice_buttons(self.process_function), str_fnc=func )
                self.choice_buttons.add(button)
        if 'fnc' in commands:
            self.process_function(commands['fnc'][0][0])
        if 'author' in commands:
            place, text = commands['author'][0]
            author_panel = pygame.Surface((self.width, 150), flags=pygame.SRCALPHA)
            author_panel.set_alpha(200)
            position = (0,0) if place == 'top' else (0, self.height - self.text_panel.get_height()) if place == 'bottom' else None
            if not position: raise Exception('В местоположении надо писать top либо bottom!')
            self.text_panel = FlashTextPanel(self.screen, text, 40, author_panel, position)
        elif 'character' in commands:
            pos, size, fontsize, text = commands['character'][0]
            self.text_panel = FlashTextPanel(self.screen, text, fontsize, pygame.Surface(size, flags=pygame.SRCALPHA), pos, size=size)


    def update_screen(self):
        self.screen.fill((255,255,255))
        self.screen.blit(self.background, (0, 0))
        self.choice_buttons.draw(self.screen)

        if self.text_panel:
            self.text_panel.draw()


        pygame.display.flip()


