import pygame

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
