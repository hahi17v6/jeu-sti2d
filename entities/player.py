import pygame
import math
from settings import *
from utils.audio import SoundManager

class HumanoidRenderer:
    def __init__(self, color):
        self.color = color
        
    def draw(self, surface, rect, facing_right, vel_x, vel_y, on_ground, is_attacking, run_cycle, cam_x=0, cam_y=0, skin_color=None):
        # Body color
        color = skin_color if skin_color else self.color
        center_x = rect.centerx - cam_x
        center_y = rect.centery - cam_y
        
        skin = (255, 200, 150)
        shirt = self.color
        pants = (40, 40, 60)
        
        # Walk cycle swing calculation
        swing = math.sin(run_cycle) * 20 # degrees of swing
        if not on_ground:
            swing = 0 # Static air pose
            
        dir_mult = 1 if facing_right else -1
        
        # HEAD
        pygame.draw.circle(surface, skin, (center_x, center_y - 12), 10)
        
        # TORSO
        torso_rect = pygame.Rect(0, 0, 16, 22)
        torso_rect.centerx = center_x
        torso_rect.top = center_y - 8
        pygame.draw.rect(surface, shirt, torso_rect, border_radius=4)
        
        shoulder_y = torso_rect.top + 4
        hip_y = torso_rect.bottom - 4
        
        # Angles
        f_arm_a = swing
        b_arm_a = -swing
        f_leg_a = -swing
        b_leg_a = swing
        
        if is_attacking:
            f_arm_a = 90 * dir_mult # Punch straight out
            
        if not on_ground:
            f_leg_a = 20 * dir_mult if vel_y < 0 else 10 * dir_mult
            b_leg_a = -10 * dir_mult if vel_y < 0 else -30 * dir_mult
            f_arm_a = 150 * dir_mult if vel_y < 0 else 45 * dir_mult
            b_arm_a = -150 * dir_mult if vel_y < 0 else -45 * dir_mult
            
        def draw_limb(col, start_x, start_y, angle, length, thickness):
            end_x = start_x + math.sin(math.radians(angle)) * length
            end_y = start_y + math.cos(math.radians(angle)) * length
            pygame.draw.line(surface, col, (start_x, start_y), (end_x, end_y), thickness)
            
        # Draw Background Limbs
        draw_limb(skin, center_x, shoulder_y, b_arm_a, 16, 6)
        draw_limb(pants, center_x, hip_y, b_leg_a, 20, 7)
        # Draw Foreground Limbs
        draw_limb(pants, center_x, hip_y, f_leg_a, 20, 7)
        draw_limb(skin, center_x, shoulder_y, f_arm_a, 16, 6)
        
        # Direction eye
        eye_offset = 4 * dir_mult
        pygame.draw.circle(surface, BLACK, (center_x + eye_offset, center_y - 14), 2)

class Player:
    def __init__(self, x, y, width=40, height=50, color=RED):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.renderer = HumanoidRenderer(color)
        
        # Physics
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        
        # Stats
        self.damage = 0   # Percentage
        
        # Combat states
        self.facing_right = True
        self.is_attacking = False
        self.hitstun_timer = 0
        self.invuln_timer = 0
        
        # Input/Combo buffers
        self.jump_buffer = 0  # In frames / seconds
        self.jump_debounce = 0
        self.combo_timer = 0
        self.combo_frames = 8
        self.frame_dt = 1.0/60.0
        
        self.run_cycle = 0
        
        # Track input state changes
        self.prev_keys = set()
        
        self.jumps_left = 2
        self.max_jumps = 2
        
    def handle_input(self, keys, controls, dt):
        if self.hitstun_timer > 0:
            return # Can't move while in hitstun
            
        # Extract inputs mapped to logical actions
        i_left = keys[controls['left']]
        i_right = keys[controls['right']]
        i_jump = keys[controls['jump']]
        i_down = keys[controls['down']]
        i_attack = keys[controls['attack']]
        i_special = keys[controls['special']]
        
        # Check newly pressed keys
        new_jump = i_jump and 'jump' not in self.prev_keys
        new_special = i_special and 'special' not in self.prev_keys
        new_attack = i_attack and 'attack' not in self.prev_keys
        new_dir = (i_left and 'left' not in self.prev_keys) or (i_right and 'right' not in self.prev_keys)
        
        # Update prev keys
        self.prev_keys = set()
        if i_left: self.prev_keys.add('left')
        if i_right: self.prev_keys.add('right')
        if i_jump: self.prev_keys.add('jump')
        if i_down: self.prev_keys.add('down')
        if i_attack: self.prev_keys.add('attack')
        if i_special: self.prev_keys.add('special')

        # COMBO CHECK: Jump + Direction within 8 frames
        # We start the combo timer when either is pressed. If the other is pressed within 8 frames, Boom ! Special combo.
        # But this depends on character. The base player just tracks the inputs.
        combo_triggered = False
        
        if new_jump and (i_left or i_right):
            combo_triggered = True
        elif new_dir and i_jump:
            combo_triggered = True
            
        if combo_triggered:
            self.trigger_combo(controls)
        
        # Horizontal moving
        if i_left:
            self.vel_x = -BASE_SPEED
            self.facing_right = False
        elif i_right:
            self.vel_x = BASE_SPEED
            self.facing_right = True
            
        # Jumping
        if controls:
            if keys[controls['jump']] and self.jumps_left > 0 and self.jump_debounce <= 0:
                self.vel_y = BASE_JUMP_FORCE
                self.jumps_left -= 1
                self.on_ground = False
                self.jump_debounce = 0.2
                SoundManager().play('jump')
            
        # Down attack 
        if i_down and new_attack:
            self.trigger_down_attack()
            
        # Normal & Special logic
        if new_attack and not i_down:
            self.trigger_attack()
            
        if new_special:
            self.trigger_special()
            
    def trigger_attack(self):
        pass
        
    def trigger_special(self):
        pass
        
    def trigger_down_attack(self):
        pass
        
    def trigger_combo(self, controls):
        # Override in subclass (e.g. Ninja tornado)
        pass
        
    def take_damage(self, amount, knockback_vector):
        if self.invuln_timer > 0:
            return
            
        self.damage += amount
        SoundManager().play('hit')
        
        # Knockback formula inspired by Smash
        # Base knockback + (damage multiplier)
        kb_multiplier = 1.0 + (self.damage / 100.0)
        
        self.vel_x = knockback_vector[0] * kb_multiplier
        self.vel_y = knockback_vector[1] * kb_multiplier
        
        # Reset ground state if hit upwards
        if self.vel_y < 0:
            self.on_ground = False
            
        # Hitstun proportional to knockback
        self.hitstun_timer = 0.5 * kb_multiplier
        
    def apply_gravity(self, dt):
        if not self.on_ground:
            self.vel_y += GRAVITY * dt
            if self.vel_y > MAX_FALL_SPEED:
                self.vel_y = MAX_FALL_SPEED
                
    def apply_friction(self, dt):
        if self.on_ground:
            friction = FRICTION_GROUND * dt
            self.vel_x += (0 - self.vel_x) * min(friction, 1.0)
        else:
            friction = FRICTION_AIR * dt
            self.vel_x += (0 - self.vel_x) * min(friction, 1.0)

    def move_and_collide(self, dt, platforms):
        # Apply X velocity
        self.rect.x += self.vel_x * dt
        
        # X collisions
        for p in platforms:
            if self.rect.colliderect(p.get_rect()):
                if self.vel_x > 0:
                    self.rect.right = p.get_rect().left
                elif self.vel_x < 0:
                    self.rect.left = p.get_rect().right
                self.vel_x = 0
                
        # Apply Y velocity
        self.rect.y += self.vel_y * dt
        self.on_ground = False
        
        # Y collisions (handle platform top/bottom interactions)
        for p in platforms:
            if self.rect.colliderect(p.get_rect()):
                if self.vel_y > 0:
                    self.rect.bottom = p.get_rect().top
                    self.on_ground = True
                    self.jumps_left = self.max_jumps
                elif self.vel_y < 0:
                    self.rect.top = p.get_rect().bottom
                self.vel_y = 0

    def check_blast_zones(self):
        if (self.rect.right < -BLAST_ZONE_PADDING or 
            self.rect.left > WIDTH + BLAST_ZONE_PADDING or
            self.rect.top > HEIGHT + BLAST_ZONE_PADDING or
            self.rect.bottom < -BLAST_ZONE_PADDING):
            self.die()

    def die(self):
        # Respawn logic
        self.rect.center = (WIDTH // 2, 100)
        self.vel_x = 0
        self.vel_y = 0
        self.damage = 0
        self.invuln_timer = 2.0  # 2 seconds respawn invulnerability
        self.hitstun_timer = 0

    def update(self, dt, platforms):
        if self.hitstun_timer > 0:
            self.hitstun_timer -= dt
            
        if self.invuln_timer > 0:
            self.invuln_timer -= dt
            
        if self.jump_debounce > 0:
            self.jump_debounce -= dt
            
        if getattr(self, 'buff_timer', 0) > 0:
            self.buff_timer -= dt
            if self.buff_timer <= 0:
                self.temp_damage_mult = 1.0
        self.skin_color = None
            
        # Run cycle animation
        if self.on_ground and abs(self.vel_x) > 10:
            self.run_cycle += abs(self.vel_x) * 0.05 * dt
        else:
            self.run_cycle = 0
            
        self.apply_gravity(dt)
        self.apply_friction(dt)
        self.move_and_collide(dt, platforms)
        self.check_blast_zones()

    def draw(self, surface, font, cam_x=0, cam_y=0):
        # Flicker if invulnerable
        if self.invuln_timer > 0:
            if int(pygame.time.get_ticks() / 100) % 2 == 0:
                return
                
        # Drop shadow for modern feel
        shadow_rect = self.rect.move(-cam_x + 6, -cam_y + 6)
        pygame.draw.rect(surface, (20, 20, 20, 128), shadow_rect, border_radius=8)
                
        # Draw realistic humanoid or sprite
        if hasattr(self, 'sprite_img') and self.sprite_img:
            img = self.sprite_img
            if not self.facing_right:
                img = pygame.transform.flip(img, True, False)
            
            # Bobbing effect when running
            bob_y = math.sin(self.run_cycle) * 5 if self.on_ground and abs(self.vel_x) > 10 else 0
            
            drawn_rect = self.rect.move(-cam_x, -cam_y + bob_y)
            px = drawn_rect.centerx - img.get_width()//2
            py = drawn_rect.bottom - img.get_height()
            
            # Apply skin tint if any
            if self.skin_color:
                img_copy = img.copy()
                # Create a colored surface to multiply
                tint = pygame.Surface(img_copy.get_size(), pygame.SRCALPHA)
                tint.fill((*self.skin_color, 255))
                img_copy.blit(tint, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(img_copy, (px, py))
            else:
                surface.blit(img, (px, py))
        else:
            self.renderer.draw(surface, self.rect, self.facing_right, self.vel_x, self.vel_y, 
                               self.on_ground, self.is_attacking, self.run_cycle, cam_x, cam_y, self.skin_color)
