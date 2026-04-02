import pygame
from settings import *
from entities.player import Player
from utils.audio import SoundManager

class Mage(Player):
    def __init__(self, x, y):
        super().__init__(x, y, color=(200, 50, 255)) # Purple
        
        # Attack entities
        self.tiger_active = False
        self.tiger_timer = 0
        self.tiger_rect = pygame.Rect(0, 0, 50, 50)
        
        self.projectiles = []
        
        # Meteor state
        self.is_meteor = False
        
        try:
            self.sprite_img = pygame.image.load("/home/hahi17/.gemini/antigravity/brain/7ae9cebb-7176-479f-b5ec-1e2dd035771f/realistic_mage_1775158414951.png").convert_alpha()
            for x in range(self.sprite_img.get_width()):
                for y in range(self.sprite_img.get_height()):
                    r, g, b, a = self.sprite_img.get_at((x, y))
                    if g > r + 30 and g > b + 30:
                        self.sprite_img.set_at((x, y), (0, 0, 0, 0))
            self.sprite_img = pygame.transform.scale(self.sprite_img, (120, 120))
        except:
            self.sprite_img = None
            
        self.skin_color = None
        
    def trigger_attack(self):
        if not self.tiger_active:
            self.tiger_active = True
            self.tiger_timer = 0.3
            self.is_attacking = True
            self.has_hit = False
            SoundManager().play('attack')
            
    def trigger_special(self):
        # Fire growing projectile
        SoundManager().play('special')
        proj = {
            'x': self.rect.right if self.facing_right else self.rect.left - 20,
            'y': self.rect.centery - 10,
            'radius': 10,
            'vx': 500 if self.facing_right else -500,
            'active': True
        }
        self.projectiles.append(proj)
        
    def trigger_down_attack(self):
        # Transform into meteor if in air
        if not self.on_ground:
            self.is_meteor = True
            self.vel_x = 0
            self.vel_y = 1500 # Heavy slam down
            
    def update(self, dt, platforms):
        super().update(dt, platforms)
        
        if self.is_meteor:
            if self.on_ground:
                # Slam impact!
                self.is_meteor = False
                # Do AOE damage placeholder
        
        if self.tiger_active:
            self.tiger_timer -= dt
            if self.tiger_timer <= 0:
                self.tiger_active = False
                self.is_attacking = False
            else:
                if self.facing_right:
                    self.tiger_rect.left = self.rect.right + 5
                else:
                    self.tiger_rect.right = self.rect.left - 5
                self.tiger_rect.centery = self.rect.centery
                
        # Update projectiles
        for p in self.projectiles:
            if p['active']:
                p['x'] += p['vx'] * dt
                p['radius'] += 20 * dt # Grows over time
                
                # Despawn if outside map wide bounds
                if p['x'] < -1000 or p['x'] > WIDTH + 1000:
                    p['active'] = False
                    
        self.projectiles = [p for p in self.projectiles if p['active']]

    def draw(self, surface, font, cam_x=0, cam_y=0):
        super().draw(surface, font, cam_x, cam_y)
        
        # Draw tiger bite
        if self.tiger_active:
            dr = self.tiger_rect.move(-cam_x, -cam_y)
            pygame.draw.rect(surface, (255, 150, 0), dr, border_radius=15)
            # Tiger stripes or face mock
            pygame.draw.ellipse(surface, BLACK, dr, 2)
            
        # Draw projectiles
        for p in self.projectiles:
            dx = int(p['x'] - cam_x)
            dy = int(p['y'] - cam_y)
            pygame.draw.circle(surface, (0, 255, 255), (dx, dy), int(p['radius']))
            pygame.draw.circle(surface, WHITE, (dx, dy), int(p['radius']-2), 1)
