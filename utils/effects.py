import pygame
import random
import math
from settings import *
from settings import *

class Particle:
    def __init__(self, x, y, color, size, velocity, life):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.vx = velocity[0]
        self.vy = velocity[1]
        self.life = life
        self.max_life = life
        
    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += GRAVITY * 0.5 * dt # Particles have half gravity
        self.life -= dt
        
    def draw(self, surface, cam_x, cam_y):
        if self.life > 0:
            ratio = self.life / self.max_life
            s = int(self.size * ratio)
            if s > 0:
                pygame.draw.circle(surface, self.color, (int(self.x - cam_x), int(self.y - cam_y)), s)

class HitFlash:
    def __init__(self, rect, color, duration):
        self.rect = rect.copy()
        self.color = color
        self.duration = duration
        self.life = duration
        
    def update(self, dt):
        self.life -= dt
        
    def draw(self, surface, cam_x, cam_y):
        if self.life > 0:
            ratio = max(0, self.life / self.duration)
            s = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            s.fill((*self.color, int(255 * ratio)))
            surface.blit(s, (self.rect.x - cam_x, self.rect.y - cam_y))

class Slash:
    def __init__(self, x, y, w, h, facing, type, color):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.facing = facing
        self.type = type
        self.color = color
        self.life = 12
        self.max_life = 12
        
    def update(self, dt):
        self.life -= dt * 60
        
    def draw(self, surface, cam_x, cam_y):
        if self.life > 0:
            ratio = self.life / self.max_life
            
            bx = self.x - cam_x
            by = self.y - cam_y - self.h/2
            bw = self.w
            if self.facing == -1:
                bx -= bw
                
            s = pygame.Surface((abs(bw), self.h), pygame.SRCALPHA)
            s.fill((*self.color[:3], int(255 * ratio)))
            surface.blit(s, (bx, by))
            
            # bright center
            if ratio > 0.5:
                pygame.draw.line(surface, WHITE, (bx, self.y - cam_y), (bx + bw + (bw if self.facing == 1 else -bw), self.y - cam_y), 5)

class Shockwave:
    def __init__(self, x, y, color, duration):
        self.x = x
        self.y = y
        self.color = color
        self.life = duration
        self.max_life = duration
        self.radius = 10
        
    def update(self, dt):
        self.life -= dt
        self.radius += 800 * dt
        
    def draw(self, surface, cam_x, cam_y):
        if self.life > 0:
            width = max(1, int((self.life / self.max_life) * 10))
            pygame.draw.circle(surface, self.color, (int(self.x - cam_x), int(self.y - cam_y)), int(self.radius), width)

class FunnyParticle(Particle):
    def __init__(self, x, y, symbol, color, size, velocity, life):
        super().__init__(x, y, color, size, velocity, life)
        self.symbol = symbol
        self.font = pygame.font.SysFont('Arial', size, bold=True)
        
    def draw(self, surface, cam_x, cam_y):
        if self.life > 0:
            ratio = self.life / self.max_life
            s = self.font.render(self.symbol, True, self.color)
            s.set_alpha(int(255 * ratio))
            surface.blit(s, (int(self.x - cam_x - s.get_width()//2), int(self.y - cam_y - s.get_height()//2)))

class BackgroundFlash:
    def __init__(self, color, duration):
        self.color = color
        self.duration = duration
        self.life = duration
        
    def update(self, dt):
        self.life -= dt
        
    def draw(self, surface):
        if self.life > 0:
            ratio = (self.life / self.duration) * 0.4 # max 40% opacity
            s = pygame.Surface((WIDTH, HEIGHT))
            s.fill(self.color)
            s.set_alpha(int(255 * ratio))
            surface.blit(s, (0, 0))

class EffectManager:
    def __init__(self):
        self.particles = []
        self.flashes = []
        self.shockwaves = []
        self.slashes = []
        self.bg_flashes = []
        
    def add_hit_sparks(self, x, y, count=10):
        for _ in range(count):
            vx = random.uniform(-600, 600)
            vy = random.uniform(-600, 200)
            color = random.choice([(255, 255, 0), (255, 150, 0), (255, 255, 255)])
            self.particles.append(Particle(x, y, color, random.randint(4, 8), (vx, vy), random.uniform(0.2, 0.5)))
            
    def add_dust(self, x, y, count=5):
        for _ in range(count):
            vx = random.uniform(-100, 100)
            vy = random.uniform(-50, 0)
            self.particles.append(Particle(x, y, (150, 150, 150), random.randint(3, 10), (vx, vy), random.uniform(0.3, 0.6)))
            
    def add_blast_particles(self, x, y, color):
        for i in range(26):
            angle = (math.pi * 2) * (i / 26.0)
            speed = 400 + (i % 5) * 100
            self.particles.append(Particle(x, y, color, random.randint(4, 9), (math.cos(angle)*speed, math.sin(angle)*speed), random.uniform(0.2, 0.4)))
            
    def add_shockwave(self, x, y, color=(255, 255, 255)):
        self.shockwaves.append(Shockwave(x, y, color, 0.40))
        
    def add_slash(self, x, y, w, h, facing, type, color):
        self.slashes.append(Slash(x, y, w, h, facing, type, color))
            
    def add_flash(self, rect, color=(255,255,255), duration=0.15):
        self.flashes.append(HitFlash(rect, color, duration))
        
    def add_bg_flash(self, color, duration=0.4):
        self.bg_flashes.append(BackgroundFlash(color, duration))
        
    def add_funny_impact(self, x, y):
        symbols = ["WTF", "BOOM", "OOF", "LOL", "KO!", "✨", "🔥", "💥"]
        for _ in range(5):
            sym = random.choice(symbols)
            vx = random.uniform(-400, 400)
            vy = random.uniform(-800, -200)
            col = (random.randint(100, 255), random.randint(100, 255), random.randint(100, 255))
            self.particles.append(FunnyParticle(x, y, sym, col, random.randint(20, 50), (vx, vy), random.uniform(0.5, 1.0)))
        
    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        
        for f in self.flashes:
            f.update(dt)
        self.flashes = [f for f in self.flashes if f.life > 0]
        
        for s in self.shockwaves:
            s.update(dt)
        self.shockwaves = [s for s in self.shockwaves if s.life > 0]
        
        for sl in self.slashes:
            sl.update(dt)
        self.slashes = [sl for sl in self.slashes if sl.life > 0]
        
        for bgf in self.bg_flashes:
            bgf.update(dt)
        self.bg_flashes = [b for b in self.bg_flashes if b.life > 0]
        
    def draw(self, surface, cam_x, cam_y):
        for bgf in self.bg_flashes:
            bgf.draw(surface)
        for f in self.flashes:
            f.draw(surface, cam_x, cam_y)
        for sl in self.slashes:
            sl.draw(surface, cam_x, cam_y)
        for s in self.shockwaves:
            s.draw(surface, cam_x, cam_y)
        for p in self.particles:
            p.draw(surface, cam_x, cam_y)
