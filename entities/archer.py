import pygame
import math
from settings import *
from entities.player import Player
from utils.audio import SoundManager

class Archer(Player):
    def __init__(self, x, y):
        super().__init__(x, y, color=(50, 180, 50)) # Forest Green
        self.projectiles = []
        self.dagger_active = False
        self.dagger_timer = 0
        self.dagger_rect = pygame.Rect(0, 0, 45, 12)
        self.attack_rect = None
        
    def trigger_attack(self):
        # Quick dagger stab
        if not self.dagger_active:
            self.dagger_active = True
            self.dagger_timer = 0.2
            self.is_attacking = True
            self.has_hit = False
            SoundManager().play('attack')
            
    def trigger_special(self):
        # Fire a fast arrow
        arrow = {
            'x': self.rect.right if self.facing_right else self.rect.left - 20,
            'y': self.rect.centery - 2,
            'vx': 900 if self.facing_right else -900,
            'active': True,
            'rect': pygame.Rect(0, 0, 20, 4)
        }
        self.projectiles.append(arrow)
        self.is_attacking = True
        SoundManager().play('attack')
        
    def trigger_down_attack(self):
        # Quick roll / dodge (placeholder for movement-based attack or just a defensive move)
        self.vel_x = (800 if self.facing_right else -800)
        self.invuln_timer = max(self.invuln_timer, 0.3)
        
    def update(self, dt, platforms):
        super().update(dt, platforms)
        
        if self.dagger_active:
            self.dagger_timer -= dt
            if self.dagger_timer <= 0:
                self.dagger_active = False
                self.is_attacking = False
                self.attack_rect = None
            else:
                if self.facing_right:
                    self.dagger_rect.left = self.rect.right
                else:
                    self.dagger_rect.right = self.rect.left
                self.dagger_rect.centery = self.rect.centery + 5
                self.attack_rect = self.dagger_rect
                
        # Update projectiles
        for a in self.projectiles:
            if a['active']:
                a['x'] += a['vx'] * dt
                a['rect'].x = a['x']
                a['rect'].y = a['y']
                
                # Despawn if outside map wide bounds
                if a['x'] < -1000 or a['x'] > WIDTH + 1000:
                    a['active'] = False
                    
        self.projectiles = [a for a in self.projectiles if a['active']]

    def draw(self, surface, font, cam_x=0, cam_y=0):
        super().draw(surface, font, cam_x, cam_y)
        
        # Draw dagger
        if self.dagger_active:
            dr = self.dagger_rect.move(-cam_x, -cam_y)
            pygame.draw.rect(surface, (200, 200, 200), dr, border_radius=2)
            pygame.draw.rect(surface, (150, 75, 0), (dr.x if self.facing_right else dr.right-5, dr.y, 5, dr.height)) # Hilt
            
        # Draw projectiles
        for a in self.projectiles:
            dr = a['rect'].move(-cam_x, -cam_y)
            pygame.draw.rect(surface, (255, 255, 255), dr)
            # Arrow head
            head_x = dr.right if a['vx'] > 0 else dr.left - 4
            pygame.draw.polygon(surface, (255, 255, 0), 
                                [(head_x, dr.centery-3), (head_x + (4 if a['vx'] > 0 else -4), dr.centery), (head_x, dr.centery+3)])
