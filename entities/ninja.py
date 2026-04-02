import pygame
from settings import *
from entities.player import Player
from utils.audio import SoundManager

class Ninja(Player):
    def __init__(self, x, y):
        super().__init__(x, y, color=(50, 50, 50)) # Dark gray / black
        self.projectiles = []
        self.slash_active = False
        self.slash_timer = 0
        self.slash_rect = pygame.Rect(0, 0, 50, 20)
        self.attack_rect = None
        
    def trigger_combo(self, controls):
        # Sends a tornado when jump + direction combo is triggered !
        t = {
            'x': self.rect.centerx,
            'y': self.rect.bottom - 40,
            'vx': 600 if self.facing_right else -600,
            'height_activation': self.rect.y,
            'rect': pygame.Rect(0, 0, 40, 60),
            'active': True
        }
        self.projectiles.append(t)
        self.is_attacking = True
        SoundManager.play('attack')
        
        # Quick slash
        if not self.slash_active:
            self.slash_active = True
            self.slash_timer = 0.25
            self.is_attacking = True
            self.has_hit = False
        
    def update(self, dt, platforms):
        super().update(dt, platforms)
        
        if self.slash_active:
            self.slash_timer -= dt
            if self.slash_timer <= 0:
                self.slash_active = False
                self.is_attacking = False
                self.attack_rect = None
            else:
                if self.facing_right:
                    self.slash_rect.left = self.rect.right
                else:
                    self.slash_rect.right = self.rect.left
                self.slash_rect.centery = self.rect.centery
                self.attack_rect = self.slash_rect

        # Update projectiles
        for t in self.projectiles:
            if t['active']:
                t['x'] += t['vx'] * dt
                t['rect'].x = t['x']
                t['rect'].y = t['y']
                
                # Check off screen
                if t['x'] < -200 or t['x'] > WIDTH + 200:
                    t['active'] = False
                    
        self.projectiles = [t for t in self.projectiles if t['active']]

    def draw(self, surface, font, cam_x=0, cam_y=0):
        super().draw(surface, font, cam_x, cam_y)
        
        if self.slash_active:
            sr = self.slash_rect.move(-cam_x, -cam_y)
            pygame.draw.rect(surface, (150, 150, 180), sr, border_radius=4)

        for t in self.projectiles:
            # Tornado visual
            color = (180, 180, 200)
            dr = t['rect'].move(-cam_x, -cam_y)
            pygame.draw.ellipse(surface, color, dr)
            pygame.draw.ellipse(surface, WHITE, dr, 2)
