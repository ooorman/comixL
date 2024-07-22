import json
import re

import pygame

from widgetClasses.choice_button import Button, ButtonStyle

class Comix:

    def __init__(self, screen, scenarios_root, staticfiles_root):
        pygame.init()

        self.width, self.height = screen.get_size()
        self.screen = screen
        self.scenario = f'{scenarios_root}/main.txt'
        self.staticfiles_root = staticfiles_root
        self.scenarios_root = scenarios_root
        self.command_number = 0
        self.variables = {}
        self.choice_buttons = pygame.sprite.Group()
        self.is_listing = True

        self.text_font = None
        self.text_text = None
        self.text_panel = None
        self.text_position = None

        self.text_index = 0
        self.text_speed = 0.002
        self.last_update_time = pygame.time.get_ticks()

        self.character_talking = False
        self.author_talking = False


    def process_event(self, events):
        just_list = False
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.MOUSEBUTTONUP:
                if self.text_text:
                    if self.text_index < len(self.text_text):
                        self.text_index = len(self.text_text)-1
                        continue
                if event.button == pygame.BUTTON_LEFT and self.is_listing:
                    just_list = True
                    self.next_frame()
        if not just_list:
            self.choice_buttons.update(events)

    def process_function(self, str_fnc):
        if str_fnc.endswith('choice'):
            self.is_listing = True
            self.choice_buttons.empty()

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
        self.character_talking = False
        self.author_talking = False

        with open(self.scenario, encoding='utf-8') as file:
            frames = [frame for frame in re.split(r'\d\n', ''.join(file.readlines())) if frame]
            current_frame = frames[self.command_number].replace('\n', '')
            commands = {}
            for command in current_frame.split(';'):
                if command:
                    key, value = command.split(':', 1)
                    key = key.strip()
                    commands[key] = []
                    for params in re.split(r'\s*\|\s*', value.strip()):
                        param_list = []
                        regex = '\s*,\s*' + ''.join([r'(?=(?:(?:[^{left}\\]|(?:\\{left}))*{right}(?:[^{right}\\]|(?:\\{right}))*{left})*(?!(?:[^{left}\\]|(?:\\{left}))*{right}))'.format(left=sign[0],right=sign[1]) for sign in [['"', '"'], ['\[', '\]'], ['\(', '\)']] ])
                        print(regex)
                        for param in re.split(regex, params):
                            if re.match(r'^[\["]', param):
                                param_list.append(json.loads(param))
                            elif param.isdigit():
                                param_list.append(int(param))
                            else:
                                param_list.append(param)
                        commands[key].append(param_list)
            # commands = {command.split(':')[0].strip(): [[json.loads(param) if re.match(r'^[\["]', param) else param for param in re.split(r'(\s*,\s*)(?=([^"\]\)]*["\[\(][^"\[\(]*["\]\)])*(?![^"\[\(]*["\]\)]))', params)] for params in re.split(r'\s*\|\s*', command.split(':')[1].strip())] for command in current_frame.split(';') if command}
        print(commands)
        if 'author' in commands and 'character' in commands: raise Exception('Свойства author и character несовместимы!')

        if 'background' in commands:
            self.background = pygame.transform.scale(pygame.image.load(f'{self.staticfiles_root}{commands['background'][0][0]}'), (self.width, self.height))
        if 'choice' in commands:

            button_styles = ButtonStyle((0, 255, 0), (0, 128, 0), pygame.font.SysFont('comicsans', 18), outline=(0, 0, 0))
            for command_params in commands['choice']:
                var, text, position = command_params
                rect = pygame.Rect(*position, 200, 70)
                button = Button(button_styles, rect, text=text, callback=self.process_function, str_fnc=f'{commands[var][0][0]} choice')

                self.is_listing = False
                self.choice_buttons.add(button)
        if 'fnc' in commands:
            self.process_function(commands['fnc'][0][0])

        if 'author' in commands:
            author_text_params = commands['author'][0]

            author_panel = pygame.Surface((self.width, 150), flags=pygame.SRCALPHA)
            author_panel.set_alpha(200)

            self.text_index = 0
            self.text_text = author_text_params[1]
            self.text_font = pygame.font.SysFont('Roboto', 40)
            self.text_panel = author_panel
            self.author_talking = True

            if author_text_params[0] == 'top':
                self.text_position = (0,0)
            elif author_text_params[0] == 'bottom':
                self.text_position = (0, self.height - self.text_panel.get_height())
            else:
                raise Exception('Необходимо указать top или bottom!')


        elif 'character' in commands:
            pos, size, fontsize, text = commands['character'][0]

            character_panel = pygame.Surface(size, flags=pygame.SRCALPHA)

            self.text_index = 0
            self.text_text = text
            self.text_position = pos
            self.text_font = pygame.font.SysFont('Roboto', fontsize)
            self.text_panel = character_panel

            self.character_size = size
            self.character_talking = True



    def next_frame(self):
        self.command_number += 1
        self.process_frame()

    def render_text_wrapped(self, color, position):
        if self.character_talking:
            border_width = 4
            pygame.draw.rect(self.text_panel, (0, 0, 0), pygame.Rect(0, 0, *self.character_size), border_radius=10)
            pygame.draw.rect(self.text_panel, (255, 255, 255),pygame.Rect(border_width, border_width, self.character_size[0] - border_width * 2, self.character_size[1] - border_width * 2), border_radius=10)

        elif self.author_talking:
            self.text_panel.fill((0,0,0,200))

        words = self.text_text[:self.text_index].split(' ')
        space_width, _ = self.text_font.size(' ')
        max_width = self.text_panel.get_width() - position[0]*2
        x, y = position
        line_height = self.text_font.get_linesize()

        for word in words:
            word_surface = self.text_font.render(word, True, color)
            word_width = word_surface.get_size()[0]

            if x + word_width >= max_width:
                x = position[0]  # Reset the x.
                y += line_height  # Start on new.txt row.
            self.text_panel.blit(word_surface, (x, y))
            x += word_width + space_width

    def update_screen(self):
        self.screen.fill((255,255,255))
        self.screen.blit(self.background, (0, 0))
        self.choice_buttons.draw(self.screen)

        if self.character_talking or self.author_talking:

            current_time = pygame.time.get_ticks()
            if current_time - self.last_update_time > self.text_speed * 1000:
                self.last_update_time = current_time
                if self.text_index < len(self.text_text):
                    self.text_index += 1
                    self.text_panel.fill((0,0,0,0))
                    self.render_text_wrapped((0,0,0), (10, 10))
            self.screen.blit(self.text_panel, self.text_position)


        pygame.display.flip()





