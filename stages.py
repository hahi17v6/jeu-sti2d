import pygame
import math
from settings import *
from physics import Platform

class BaseStage:
    def __init__(self):
        self.platforms = []
        self.hazards = [] # e.g. lava rects
        
    def update(self, dt, players):
        pass
        
    def draw(self, surface, cam_x, cam_y):
        if hasattr(self, 'bg_img') and self.bg_img:
            # Parallax scrolling
            px = (-cam_x * 0.2) % WIDTH
            py = max(-100, min((-cam_y * 0.2), 0))
            # Draw twice horizontally for wrapping
            surface.blit(self.bg_img, (px, py))
            surface.blit(self.bg_img, (px - WIDTH, py))
            surface.blit(self.bg_img, (px + WIDTH, py))
            
        for plat in self.platforms:
            drawn_rect = plat.rect.move(-cam_x, -cam_y)
            pygame.draw.rect(surface, plat.color, drawn_rect)
            
            # Neon edge
            pygame.draw.rect(surface, (100, 255, 255), (drawn_rect.x, drawn_rect.y, drawn_rect.width, 3))
            
        for hz in self.hazards:
            dr = hz['rect'].move(-cam_x, -cam_y)
            # Lava visual
            pygame.draw.rect(surface, hz['color'], dr)
            pygame.draw.rect(surface, (255, 255, 0), (dr.x, dr.y, dr.width, 4)) # Lava crest 

class MagmaCave(BaseStage):
    def __init__(self):
        super().__init__()
        self.platforms = [
            Platform(WIDTH//2 - 400, HEIGHT - 150, 800, 40, color=(80, 40, 40)),
            Platform(WIDTH//2 - 300, HEIGHT - 350, 200, 20, color=(80, 40, 40)),
            Platform(WIDTH//2 + 100, HEIGHT - 350, 200, 20, color=(80, 40, 40)),
            Platform(WIDTH//2 - 100, HEIGHT - 550, 200, 20, color=(80, 40, 40))
        ]
        
        try:
            self.bg_img = pygame.image.load("/home/hahi17/.gemini/antigravity/brain/7ae9cebb-7176-479f-b5ec-1e2dd035771f/bg_magma_1775157392012.png").convert()
            self.bg_img = pygame.transform.scale(self.bg_img, (WIDTH, HEIGHT))
        except:
            self.bg_img = None
        
        # Lava starts offscreen
        self.lava_y = HEIGHT + 400
        self.lava_speed = 40 # pixels per second
        self.hazards.append({
            'rect': pygame.Rect(-1000, self.lava_y, WIDTH + 2000, 1000),
            'color': (255, 80, 0),
            'damage': 25,
            'knockback': (0, -1500) # huge up knockback
        })
        
    def update(self, dt, players):
        # Oscillate lava
        time_sec = pygame.time.get_ticks() / 1000.0
        
        # Slowly rises globally
        if self.lava_y > HEIGHT - 300:
            self.lava_y -= self.lava_speed * dt
            
        y_offset = math.sin(time_sec * 2) * 20
        self.hazards[0]['rect'].y = self.lava_y + y_offset
        
        # Check overlaps
        for p in players:
            if not getattr(p, 'invuln_timer', 0) > 0:
                if p.rect.colliderect(self.hazards[0]['rect']):
                    p.take_damage(self.hazards[0]['damage'], self.hazards[0]['knockback'])

class MovingSky(BaseStage):
    def __init__(self):
        super().__init__()
        self.plat1 = Platform(WIDTH//2 - 450, HEIGHT - 200, 400, 30, color=(50, 100, 200))
        self.plat2 = Platform(WIDTH//2 + 50, HEIGHT - 200, 400, 30, color=(50, 100, 200))
        self.plat3 = Platform(WIDTH//2 - 150, HEIGHT - 400, 300, 20, color=(50, 150, 200))
        self.platforms = [self.plat1, self.plat2, self.plat3]
        self.time = 0
        
        try:
            self.bg_img = pygame.image.load("/home/hahi17/.gemini/antigravity/brain/7ae9cebb-7176-479f-b5ec-1e2dd035771f/bg_sky_1775157413923.png").convert()
            self.bg_img = pygame.transform.scale(self.bg_img, (WIDTH, HEIGHT))
        except:
            self.bg_img = None
        
    def update(self, dt, players):
        self.time += dt
        
        # Platforms shift
        shift1 = math.sin(self.time) * 120 * dt
        shift2 = math.cos(self.time) * 120 * dt
        shift3 = math.sin(self.time * 1.5) * 80 * dt
        
        self.plat1.rect.x += shift1
        self.plat2.rect.x += shift2
        self.plat3.rect.x += shift3
        
        # Prevent jittery players by moving them if they are standing on it
        for p in players:
            if p.on_ground:
                # Basic check: if standing on plat1
                if p.rect.bottom == self.plat1.rect.top:
                    p.rect.x += shift1
                elif p.rect.bottom == self.plat2.rect.top:
                    p.rect.x += shift2
                elif p.rect.bottom == self.plat3.rect.top:
                    p.rect.x += shift3

class TargetSmash(BaseStage):
    def __init__(self):
        super().__init__()
        self.platforms = [
            Platform(WIDTH//2 - 500, HEIGHT - 100, 1000, 40, color=(60, 80, 60)),
            Platform(WIDTH//2 - 300, HEIGHT - 250, 100, 20, color=(60, 80, 60)),
            Platform(WIDTH//2 + 200, HEIGHT - 350, 100, 20, color=(60, 80, 60)),
            Platform(WIDTH//2 - 400, HEIGHT - 500, 150, 20, color=(60, 80, 60)),
        ]
        self.targets = [
            pygame.Rect(WIDTH//2 - 280, HEIGHT - 300, 40, 40),
            pygame.Rect(WIDTH//2 + 230, HEIGHT - 400, 40, 40),
            pygame.Rect(WIDTH//2 - 350, HEIGHT - 550, 40, 40),
            pygame.Rect(WIDTH//2 + 400, HEIGHT - 150, 40, 40)
        ]
        self.targets_destroyed = 0
        self.total_targets = len(self.targets)
        
    def update(self, dt, players):
        if not players: return
        p = players[0]
        
        # Check attacks against targets
        if getattr(p, 'is_attacking', False):
            hitbox = p.attack_rect if hasattr(p, 'attack_rect') else None
            # Legacy support
            if not hitbox:
                if hasattr(p, 'sword_rect') and p.sword_active: hitbox = p.sword_rect
                elif hasattr(p, 'tiger_rect') and p.tiger_active: hitbox = p.tiger_rect
            
            if hitbox:
                for t in self.targets[:]:
                    if hitbox.colliderect(t):
                        self.targets.remove(t)
                        self.targets_destroyed += 1
                        
            if hasattr(p, 'projectiles'):
                for proj in p.projectiles:
                    if proj['active']:
                        pr = proj['rect']
                        for t in self.targets[:]:
                            if pr.colliderect(t):
                                self.targets.remove(t)
                                self.targets_destroyed += 1
                                proj['active'] = False
                                
    def draw(self, surface, cam_x, cam_y):
        super().draw(surface, cam_x, cam_y)
        for t in self.targets:
            dr = t.move(-cam_x, -cam_y)
            pygame.draw.rect(surface, (255, 0, 0), dr, border_radius=20)
            pygame.draw.circle(surface, WHITE, dr.center, 10, 3) 

class CyberCity(BaseStage):
    def __init__(self):
        super().__init__()
        self.platforms = [
            Platform(WIDTH//2 - 500, HEIGHT - 120, 1000, 40, color=(30, 30, 60)),
            Platform(WIDTH//2 - 300, HEIGHT - 300, 200, 20, color=(100, 50, 200)),
            Platform(WIDTH//2 + 100, HEIGHT - 300, 200, 20, color=(100, 50, 200)),
            Platform(WIDTH//2 - 100, HEIGHT - 450, 200, 20, color=(0, 255, 255))
        ]
        self.time = 0
        
    def update(self, dt, players):
        self.time += dt
        # Platforms blink / flicker
        if int(self.time * 2) % 2 == 0:
            self.platforms[3].color = (0, 100, 100) # dimmed
        else:
            self.platforms[3].color = (0, 255, 255) # bright

class CrystalVoid(BaseStage):
    def __init__(self):
        super().__init__()
        # Small floating islands
        self.platforms = [
            Platform(WIDTH//2 - 100, HEIGHT//2, 200, 30, color=(150, 200, 255)),
            Platform(WIDTH//2 - 400, HEIGHT//2 - 150, 150, 20, color=(180, 220, 255)),
            Platform(WIDTH//2 + 250, HEIGHT//2 - 150, 150, 20, color=(180, 220, 255)),
        ]
        
    def update(self, dt, players):
        # Low gravity zone? 
        for p in players:
            # If player is in the "void" (middle section), they fall slower
            if abs(p.rect.centerx - WIDTH//2) < 400:
                p.vel_y -= 400 * dt # Counter gravity slightly
