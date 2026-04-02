import pygame
from settings import *
from entities.player import Player
from utils.audio import SoundManager

class Knight(Player):
    def __init__(self, x, y):
        super().__init__(x, y, color=(150, 150, 150)) # Gray silver
        self.sword_active = False
        self.sword_timer = 0
        self.sword_rect = pygame.Rect(0, 0, 70, 15)
        self.sword_color = (200, 200, 255) # Clean light blue sword
        
        try:
            self.sprite_img = pygame.image.load("/home/hahi17/.gemini/antigravity/brain/7ae9cebb-7176-479f-b5ec-1e2dd035771f/realistic_knight_1775158394874.png").convert_alpha()
            # Advanced transparency: convert any pixel that is "mostly green" to transparent
            for x in range(self.sprite_img.get_width()):
                for y in range(self.sprite_img.get_height()):
                    r, g, b, a = self.sprite_img.get_at((x, y))
                    if g > r + 30 and g > b + 30: # If green is significantly higher than R and B
                        self.sprite_img.set_at((x, y), (0, 0, 0, 0))
            self.sprite_img = pygame.transform.scale(self.sprite_img, (120, 120))
        except:
            self.sprite_img = None
            
        self.skin_color = None
        
    def trigger_attack(self):
        if not self.sword_active:
            self.sword_active = True
            self.sword_timer = 0.25 # Active for 0.25s
            self.is_attacking = True
            self.has_hit = False
            SoundManager().play('attack')
        
    def trigger_special(self):
        # Teleport: moderate height, controllable via direction
        # Dash teleport mapping: move 250px horizontally, 75px up
        tx = 250 if self.facing_right else -250
        self.rect.x += tx
        self.rect.y -= 75
        
        # Reset velocity to act like a warp
        self.vel_y = 0
        
        # Give brief invulnerability when teleporting
        self.invuln_timer = max(self.invuln_timer, 0.2)
        
    def update(self, dt, platforms):
        super().update(dt, platforms)
        
        if self.sword_active:
            self.sword_timer -= dt
            if self.sword_timer <= 0:
                self.sword_active = False
                self.is_attacking = False
            else:
                # Sword follows player
                if self.facing_right:
                    self.sword_rect.left = self.rect.right
                else:
                    self.sword_rect.right = self.rect.left
                # Sword can appear slightly below center
                self.sword_rect.centery = self.rect.centery + 10

    def draw(self, surface, font, cam_x=0, cam_y=0):
        super().draw(surface, font, cam_x, cam_y)
        
        if self.sword_active:
            drawn_sword = self.sword_rect.move(-cam_x, -cam_y)
            pygame.draw.rect(surface, self.sword_color, drawn_sword, border_radius=4)
            # Add visual flair with a highlight
            highlight = pygame.Rect(drawn_sword.x + 2, drawn_sword.y + 2, drawn_sword.width - 4, 3)
            pygame.draw.rect(surface, (255, 255, 255), highlight)
