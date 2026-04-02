import pygame
import random
import math
from settings import *

class Item:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.type = random.choice(['heal', 'ultimate_sword', 'laser_gun'])
        self.vel_y = 0
        self.on_ground = False
        self.active = True
        self.timer = 20.0 # Despawns after 20s
        
    def update(self, dt, platforms):
        self.timer -= dt
        if self.timer <= 0:
            self.active = False
            
        if not self.on_ground:
            self.vel_y += GRAVITY * dt
            
        self.rect.y += self.vel_y * dt
        self.on_ground = False
        
        for p in platforms:
            if self.rect.colliderect(p.get_rect()):
                if self.vel_y > 0:
                    self.rect.bottom = p.get_rect().top
                    self.on_ground = True
                self.vel_y = 0
                
    def draw(self, surface, cam_x, cam_y):
        dr = self.rect.move(-cam_x, -cam_y)
        
        time_ms = pygame.time.get_ticks()
        glimmer = (math.sin(time_ms / 150.0) + 1) / 2.0  # 0 to 1
        
        # Float animation
        float_y = math.sin(time_ms / 300.0) * 15
        dr.y += float_y
        
        color = (255, 255, 255)
        text = "?"
        
        if self.type == 'heal': 
            color = (0, 255, 100)
            text = "❤"
        elif self.type == 'ultimate_sword': 
            color = (255, 50, 50)
            text = "⚔️"
        elif self.type == 'laser_gun': 
            color = (0, 200, 255)
            text = "🔫"
            
        # Magnificent Aura (Golden glowing back)
        s = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, int(80 + 70 * glimmer)), (50, 50), 30 + 10 * glimmer)
        pygame.draw.circle(s, (*color, int(150)), (50, 50), 20)
        surface.blit(s, (dr.centerx - 50, dr.centery - 50))
        
        # Inner core
        pygame.draw.circle(surface, WHITE, dr.center, 12)
        
        # A beam of light pointing up to make it super visible and magnificent!
        beam_rect = pygame.Rect(dr.centerx - 2, dr.centery - 800, 4, 800)
        pygame.draw.rect(surface, (*color, 128), beam_rect)

class ItemManager:
    def __init__(self):
        self.items = []
        self.spawn_timer = 0
        self.spawn_interval = 8.0 # Drop a weapon every 8 seconds
        
    def update(self, dt, platforms, players, effect_manager):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = self.spawn_interval
            # Spawn random weapon from sky
            x = random.randint(WIDTH//2 - 400, WIDTH//2 + 400)
            self.items.append(Item(x, -200))
            effect_manager.add_shockwave(x, 100, (255, 255, 100)) # Warn it's falling!

        for item in self.items:
            item.update(dt, platforms)
            
            # Check pickup
            for p in players:
                if item.active and p.rect.colliderect(item.rect):
                    self.apply_effect(item, p, effect_manager)
                    item.active = False
                    
        self.items = [i for i in self.items if i.active]
        
    def apply_effect(self, item, player, effect_manager):
        effect_manager.add_blast_particles(player.rect.centerx, player.rect.centery, (255, 255, 255))
        effect_manager.add_shockwave(player.rect.centerx, player.rect.centery, (200, 255, 200))
        
        if item.type == 'heal':
            player.damage = max(0, player.damage - 50)
            
        elif item.type == 'ultimate_sword':
            # Temporary omega knockback
            player.temp_damage_mult = 2.5
            player.buff_timer = 10.0
            
        elif item.type == 'laser_gun':
            # Shoots an instant death beam across the screen! (One time use)
            # We'll just execute it instantly here for visual juice
            beam_y = player.rect.centery
            direction = 1 if player.facing_right else -1
            effect_manager.add_slash(player.rect.centerx, player.rect.centery, WIDTH, 80, direction, "laser", (0, 255, 255))
            
            # Also deal massive damage
            # We don't have access to OTHER player here easily, but we can set a flag on the player.
            player.fire_laser = True 
            
    def draw(self, surface, cam_x, cam_y):
        for item in self.items:
            item.draw(surface, cam_x, cam_y)
