import pygame
import sys
import random
from settings import *
from physics import Platform
from entities.player import Player
from utils.audio import SoundManager
from entities.knight import Knight
from entities.mage import Mage
from entities.ninja import Ninja
from entities.archer import Archer
from utils.effects import EffectManager
from items import ItemManager
from network import NetworkManager

def draw_player_panel(surface, font, title, damage, color, wins, x, y, panel_w=300, panel_h=100):
    # Dark modern panel with semi-transparent background
    s = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 0, 0, 180), (0, 0, panel_w, panel_h), border_radius=12)
    surface.blit(s, (x, y))
    
    # Neon border
    pygame.draw.rect(surface, color, (x, y, panel_w, panel_h), 2, border_radius=12)
    
    title_surf = font.render(title, True, color)
    surface.blit(title_surf, (x + 20, y + 15))
    
    # Draw win dots
    for i in range(wins):
        pygame.draw.circle(surface, (255, 200, 0), (x + panel_w - 20 - (i*20), y + 25), 6)
        
    dmg_color = (255, 255, 255)
    if damage > 50: dmg_color = (255, 200, 0)
    if damage > 100: dmg_color = (255, 50, 50)
    
    damage_text = font.render(f"{int(damage)} %", True, dmg_color)
    surface.blit(damage_text, (x + 20, y + 55))
    
    # Danger bar representing knockback scaling
    ratio = min(1.0, damage / 200.0)
    pygame.draw.rect(surface, (50, 50, 50), (x + 120, y + 60, 150, 15), border_radius=8)
    
    if ratio > 0:
        pygame.draw.rect(surface, dmg_color, (x + 120, y + 60, 150 * ratio, 15), border_radius=8)

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Arthur Jeu - Smash Bros Clone")
        self.clock = pygame.time.Clock()
        self.running = True
        self.audio = SoundManager()
        
        # UI Font
        self.font = pygame.font.SysFont(None, 36)
        self.large_font = pygame.font.SysFont('Arial', 60, bold=True)
        
        self.state = 'MENU'
        self.current_stage = None
        self.players = []
        self.item_manager = ItemManager()
        
        # Character selection info
        self.available_chars = [
            {'name': 'Chevalier', 'class': Knight, 'color': (100, 100, 255)},
            {'name': 'Mage', 'class': Mage, 'color': (255, 100, 100)}
        ]
        
        # Pre-load preview sprites
        for char in self.available_chars:
            try:
                # Create a temp instance to get sprite or use known paths
                temp = char['class'](0, 0)
                char['preview'] = temp.sprite_img
            except:
                char['preview'] = None
                
        self.p1_selection = random.randint(0, len(self.available_chars)-1)
        self.p2_selection = random.randint(0, len(self.available_chars)-1)
        
        from stages import MagmaCave, MovingSky, CyberCity, CrystalVoid
        self.available_stages = [
            {'name': 'Caverne Magmatique', 'class': MagmaCave},
            {'name': 'Ciel Mouvant', 'class': MovingSky},
            {'name': 'Cyber Ville', 'class': CyberCity},
            {'name': 'Vide de Cristal', 'class': CrystalVoid}
        ]
        self.stage_selection = 0
        
        # Juice properties
        self.effect_manager = EffectManager()
        self.hit_freeze_timer = 0
        self.screen_shake_timer = 0
        
        # Camera
        self.cam_x = 0
        self.cam_y = 0
        
        # Networking
        self.network = NetworkManager()
        self.net_ip_input = ""
        
        # Default controls
        self.controls_p1 = {
            'left': pygame.K_q, 'right': pygame.K_d, 
            'jump': pygame.K_z, 'down': pygame.K_s,
            'attack': pygame.K_f, 'special': pygame.K_g
        }
        self.controls_p2 = {
            'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 
            'jump': pygame.K_UP, 'down': pygame.K_DOWN,
            'attack': pygame.K_k, 'special': pygame.K_l
        }
        
        self.remapping = False
        self.remapping_target = None # (player_num, action_key)
        
        self.p1_skin = 0
        self.p2_skin = 0
        self.available_skins = [None, (255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]
        
        # Match settings
        self.round_time_left = 120.0
        self.max_wins = 5
        
        try:
            self.menu_bg = pygame.image.load("/home/hahi17/.gemini/antigravity/brain/7ae9cebb-7176-479f-b5ec-1e2dd035771f/bg_menu_1775157540215.png").convert()
            self.menu_bg = pygame.transform.scale(self.menu_bg, (WIDTH, HEIGHT))
        except:
            self.menu_bg = None
        
    def start_game(self, mode):
        self.state = mode
        self.p1_wins = 0
        self.p2_wins = 0
        self.round_end_timer = 0
        self.winner_text = ""
        
        if mode == 'VERSUS':
            self.p1_wins = 0
            self.p2_wins = 0
            self.round_time_left = 120.0
            
            self.p1 = self.available_chars[self.p1_selection]['class'](WIDTH//2 - 200, 100)
            self.p2 = self.available_chars[self.p2_selection]['class'](WIDTH//2 + 200, 100)
            self.p1.skin_color = self.available_skins[self.p1_skin]
            self.p2.skin_color = self.available_skins[self.p2_skin]
            self.players = [self.p1, self.p2]
            self.item_manager = ItemManager()
            
            self.current_stage = self.available_stages[self.stage_selection]['class']()
            
        elif mode == 'CHALLENGE_TARGETS':
            self.p1 = Knight(WIDTH//2, 100)
            self.players = [self.p1]
            from stages import TargetSmash
            self.current_stage = TargetSmash()
            self.challenge_start_time = pygame.time.get_ticks()

    def reset_round(self, winner_num=0):
        # Increment wins 
        if winner_num == 1: self.p1_wins += 1
        elif winner_num == 2: self.p2_wins += 1
        
        if self.p1_wins >= self.max_wins or self.p2_wins >= self.max_wins:
            self.state = 'VICTORY'
            self.winner_text = ("JOUEUR 1" if self.p1_wins >= self.max_wins else "JOUEUR 2") + " TRIOMPHE !"
            return
            
        # Change map automatically
        self.stage_selection = (self.stage_selection + 1) % len(self.available_stages)
            
        self.p1 = self.available_chars[self.p1_selection]['class'](WIDTH//2 - 200, 100)
        self.p2 = self.available_chars[self.p2_selection]['class'](WIDTH//2 + 200, 100)
        self.p1.skin_color = self.available_skins[self.p1_skin]
        self.p2.skin_color = self.available_skins[self.p2_skin]
        self.players = [self.p1, self.p2]
        self.item_manager = ItemManager()
        self.round_time_left = 120.0
        
        self.current_stage = self.available_stages[self.stage_selection]['class']()
            
    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                
            # Key events
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                
                elif self.state == 'MENU':
                    if event.key == pygame.K_1:
                        self.state = 'CHAR_SELECT'
                    elif event.key == pygame.K_2:
                        self.start_game('CHALLENGE_TARGETS')
                    elif event.key == pygame.K_3:
                        self.network.host()
                        self.state = 'CHAR_SELECT'
                    elif event.key == pygame.K_4:
                        self.state = 'NET_JOIN'
                        self.net_ip_input = ""
                    elif event.key == pygame.K_5:
                        self.state = 'SETTINGS'
                    elif event.key == pygame.K_m:
                        self.audio.toggle()
                        
                elif self.state == 'SETTINGS':
                    if self.remapping:
                        player_num, action = self.remapping_target
                        if player_num == 1:
                            self.controls_p1[action] = event.key
                        else:
                            self.controls_p2[action] = event.key
                        self.remapping = False
                    elif event.key == pygame.K_ESCAPE:
                        self.state = 'MENU'
                    elif event.key == pygame.K_7:
                        self.audio.toggle()
                    else:
                        # Map keys 1-6 for P1, 7-0 for P2 remapping triggers? 
                        # Or use a cursor. Let's use simple number shortcuts for now.
                        actions = ['left', 'right', 'jump', 'down', 'attack', 'special']
                        # P1: 1, 2, 3, 4, 5, 6
                        if event.key >= pygame.K_1 and event.key <= pygame.K_6:
                            idx = event.key - pygame.K_1
                            self.remapping = True
                            self.remapping_target = (1, actions[idx])
                        # P2: F1, F2, F3, F4, F5, F6
                        elif event.key >= pygame.K_F1 and event.key <= pygame.K_F6:
                            idx = event.key - pygame.K_F1
                            self.remapping = True
                            self.remapping_target = (2, actions[idx])

                elif self.state == 'CHAR_SELECT':
                    # P1 selection (ZQSD)
                    if event.key == pygame.K_q:
                        self.p1_selection = (self.p1_selection - 1) % len(self.available_chars)
                    elif event.key == pygame.K_d:
                        self.p1_selection = (self.p1_selection + 1) % len(self.available_chars)
                    
                    # P2 selection (Arrows)
                    if event.key == pygame.K_LEFT:
                        self.p2_selection = (self.p2_selection - 1) % len(self.available_chars)
                    elif event.key == pygame.K_RIGHT:
                        self.p2_selection = (self.p2_selection + 1) % len(self.available_chars)
                    
                    # Shortcuts 1-2 for P1, 6-7 for P2
                    if event.key == pygame.K_1: self.p1_selection = 0
                    elif event.key == pygame.K_2: self.p1_selection = 1
                    
                    if event.key == pygame.K_6: self.p2_selection = 0
                    elif event.key == pygame.K_7: self.p2_selection = 1

                    # Stage selection (Tab)
                    if event.key == pygame.K_TAB:
                        self.stage_selection = (self.stage_selection + 1) % len(self.available_stages)
                    
                    # Skin selection (S for P1, Down for P2)
                    if event.key == pygame.K_s:
                        self.p1_skin = (self.p1_skin + 1) % len(self.available_skins)
                    if event.key == pygame.K_DOWN:
                        self.p2_skin = (self.p2_skin + 1) % len(self.available_skins)
                        
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        self.start_game('VERSUS')
                    elif event.key == pygame.K_ESCAPE:
                        self.state = 'MENU'
                            
                    if event.key == pygame.K_7:
                        self.audio.toggle()

                elif self.state == 'VICTORY':
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        self.state = 'MENU'

                elif self.state == 'NET_JOIN':
                    if event.key == pygame.K_BACKSPACE:
                        self.net_ip_input = self.net_ip_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        self.network.connect(self.net_ip_input)
                        self.state = 'CHAR_SELECT'
                    elif event.key == pygame.K_ESCAPE:
                        self.state = 'MENU'
                    else:
                        if event.unicode in "0123456789.":
                            self.net_ip_input += event.unicode
                            
                elif event.key == pygame.K_ESCAPE:
                    self.state = 'MENU'

    def update(self, dt):
        if self.state in ['MENU', 'CHAR_SELECT', 'NET_JOIN', 'SETTINGS', 'VICTORY']:
            return
            
        # Update round timer
        if self.state == 'VERSUS':
            self.round_time_left -= dt
            if self.round_time_left <= 0:
                # Sudden death or time out logic
                if self.p1.damage < self.p2.damage:
                    self.reset_round(1)
                else:
                    self.reset_round(2)
                return
            
        keys = pygame.key.get_pressed()
        
        # Use dynamic controls
        controls_p1 = self.controls_p1
        controls_p2 = self.controls_p2
        
        self.p1.handle_input(keys, controls_p1, dt)
        
        # If networking, sync inputs
        if self.network.is_connected:
            # Send P1 inputs
            # Actually, we need to send the EXACT keys or logical actions.
            # Simplified: just send move/jump/attack flags.
            net_input = {
                'left': keys[controls_p1['left']], 'right': keys[controls_p1['right']],
                'jump': keys[controls_p1['jump']], 'down': keys[controls_p1['down']],
                'attack': keys[controls_p1['attack']], 'special': keys[controls_p1['special']]
            }
            self.network.send_input(net_input)
            
            # Receive P2 inputs
            remote_p2 = self.network.receive_input()
            if remote_p2:
                # Mock controls_p2 with boolean values from remote
                self.players[1].handle_input(remote_p2, remote_p2, dt) # Passing same dict as mock
            else:
                # If no data, P2 stays idle or uses previous? 
                pass
        else:
            if len(self.players) > 1:
                self.players[1].handle_input(keys, controls_p2, dt)
            
        if self.hit_freeze_timer > 0:
            self.hit_freeze_timer -= dt
            # Still update projectiles even during hit freeze for visual continuity? 
            # Or keep it fully frozen. Usually, Smash freezes everything.
            return 

        for p in self.players:
            p.update(dt, self.current_stage.platforms)
            
        self.current_stage.update(dt, self.players)
            
        self.effect_manager.update(dt)
        
        if self.state == 'VERSUS':
            # Check Round ending deaths
            if self.round_end_timer > 0:
                self.round_end_timer -= dt
                if self.round_end_timer <= 0:
                    self.reset_round()
            else:
                pass # Death check handled globally below
                # Check death
                for i, p in enumerate(self.players):
                    if p.rect.top > HEIGHT or p.rect.bottom < 0 or p.rect.left > WIDTH or p.rect.right < 0:
                        # In Versus, death means round end
                        if self.state == 'VERSUS':
                            winner = 2 if i == 0 else 1
                            self.audio.play('death')
                            # Safety check: ensure game hasn't already reset
                            if self.state == 'VERSUS':
                                self.reset_round(winner)
                                return
                        else:
                            p.die()
                    
            if self.round_end_timer == 0:
                self.item_manager.update(dt, self.current_stage.platforms, self.players, self.effect_manager)
            
            # Check for generic item laser triggers on players
            for p in self.players:
                if getattr(p, 'fire_laser', False):
                    p.fire_laser = False
                    for other in self.players:
                        if other != p:
                            dir_x = 1 if p.facing_right else -1
                            # Full screen beam check
                            if abs(other.rect.centery - p.rect.centery) < 120: 
                                if (dir_x == 1 and other.rect.x > p.rect.x) or (dir_x == -1 and other.rect.x < p.rect.x):
                                    other.take_damage(40, (dir_x * 1200, -800))
                                    self.hit_freeze_timer = 0.2
                                    self.screen_shake_timer = 0.4
                                    self.effect_manager.add_shockwave(other.rect.centerx, other.rect.centery, (0, 255, 255))
                                    self.effect_manager.add_blast_particles(other.rect.centerx, other.rect.centery, (0, 255, 255))
            
        # New Generic Hit Logic
        if self.state == 'VERSUS':
            for attacker in self.players:
                # In Challenge mode, there might only be 1 player. We need to skip hit logic or target enemies.
                if len(self.players) < 2:
                    continue 

                victim = self.p2 if attacker == self.p1 else self.p1
                
                # Check normal attacks (physical hitboxes)
                attack_rect = None
                dmg = 0
                kb = (0, 0)
                color = attacker.color
                
                if hasattr(attacker, 'sword_active') and attacker.sword_active and not attacker.has_hit:
                    attack_rect = attacker.sword_rect
                    dmg = 12 * getattr(attacker, 'temp_damage_mult', 1.0)
                    kb = (800 if attacker.facing_right else -800, -600)
                elif hasattr(attacker, 'tiger_active') and attacker.tiger_active and not attacker.has_hit:
                    attack_rect = attacker.tiger_rect
                    dmg = 14 * getattr(attacker, 'temp_damage_mult', 1.0)
                    kb = (700 if attacker.facing_right else -700, -500)
                elif hasattr(attacker, 'dagger_active') and attacker.dagger_active and not attacker.has_hit:
                    attack_rect = attacker.dagger_rect
                    dmg = 10 * getattr(attacker, 'temp_damage_mult', 1.0)
                    kb = (900 if attacker.facing_right else -900, -400)
                
                if attack_rect and attack_rect.colliderect(victim.rect):
                    victim.take_damage(dmg, (kb[0] * getattr(attacker, 'temp_damage_mult', 1.0), kb[1] * getattr(attacker, 'temp_damage_mult', 1.0)))
                    attacker.has_hit = True
                    self.hit_freeze_timer = 0.1
                    self.screen_shake_timer = 0.3
                    self.effect_manager.add_blast_particles(victim.rect.centerx, victim.rect.centery, color)
                    self.effect_manager.add_shockwave(victim.rect.centerx, victim.rect.centery, color)
                    self.effect_manager.add_flash(victim.rect, color, 0.2)
                    
                    if dmg > 15:
                        self.effect_manager.add_funny_impact(victim.rect.centerx, victim.rect.centery)
                        self.effect_manager.add_bg_flash(color)
                
                # Check projectiles
                if hasattr(attacker, 'projectiles'):
                    for proj in attacker.projectiles:
                        if proj['active']:
                            pr = pygame.Rect(proj['x'] - proj['radius'], proj['y'] - proj['radius'], proj['radius']*2, proj['radius']*2)
                            if pr.colliderect(victim.rect):
                                dirx = 1 if proj['vx'] > 0 else -1
                                dmg = 5 + (proj['radius'] / 3)
                                victim.take_damage(dmg, (dirx * 900, -400))
                                proj['active'] = False
                                self.hit_freeze_timer = 0.05
                                self.screen_shake_timer = 0.15
                                self.effect_manager.add_hit_sparks(victim.rect.centerx, victim.rect.centery, int(10 + dmg))
                                self.effect_manager.add_shockwave(victim.rect.centerx, victim.rect.centery, (0, 255, 255))
                                
                if hasattr(attacker, 'arrows'):
                    for arrow in attacker.arrows:
                        if arrow['active']:
                            if arrow['rect'].colliderect(victim.rect):
                                dirx = 1 if arrow['vx'] > 0 else -1
                                victim.take_damage(8, (dirx * 600, -300))
                                arrow['active'] = False
                                self.hit_freeze_timer = 0.05
                                self.screen_shake_timer = 0.1
                                self.effect_manager.add_hit_sparks(victim.rect.centerx, victim.rect.centery, 5)

                if hasattr(attacker, 'tornados'):
                    for t in attacker.tornados:
                        if t['active']:
                            if t['rect'].colliderect(victim.rect):
                                dirx = 1 if t['vx'] > 0 else -1
                                victim.take_damage(6, (dirx * 400, -800)) # Ninja tornado sends upwards!
                                # Tornado doesn't disappear on hit, it multi-hits!
                                # But we need a hit timer to prevent instant death.
                                # For now, let's just make it disappear to be safe.
                                t['active'] = False 
                                self.hit_freeze_timer = 0.05
                                self.effect_manager.add_shockwave(victim.rect.centerx, victim.rect.centery, (200, 200, 255))
                        
        # Camera Logic
        if len(self.players) > 1:
            target_x = (self.p1.rect.centerx + self.p2.rect.centerx) / 2
            target_y = (self.p1.rect.centery + self.p2.rect.centery) / 2
        else:
            target_x = self.p1.rect.centerx
            target_y = self.p1.rect.centery
        
        desired_cam_x = target_x - WIDTH / 2
        desired_cam_y = target_y - HEIGHT / 2
        
        # Smooth lerp
        self.cam_x += (desired_cam_x - self.cam_x) * 5 * dt
        self.cam_y += (desired_cam_y - self.cam_y) * 5 * dt
        
        if self.screen_shake_timer > 0:
            self.screen_shake_timer -= dt
            
    def draw(self):
        # Cool Gradient Background
        for y in range(HEIGHT):
            r = int(20 + 20 * (y / HEIGHT))
            g = int(20 + 30 * (y / HEIGHT))
            b = int(40 + 60 * (y / HEIGHT))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))
            
        render_offset_x = self.cam_x
        render_offset_y = self.cam_y
        
        if self.screen_shake_timer > 0:
            import random
            intensity = int(self.screen_shake_timer * 100)
            render_offset_x += random.randint(-intensity, intensity)
            render_offset_y += random.randint(-intensity, intensity)
        
        if self.state == 'MENU':
            if getattr(self, 'menu_bg', None):
                self.screen.blit(self.menu_bg, (0, 0))
            else:
                self.screen.fill((20, 20, 30))
                
            # Dark overlay
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            title = self.font.render("ARTHUR JEU - ULTIMATE", True, (255, 200, 0))
            press1 = self.font.render("[1] JOUER VERSUS (Selection)", True, WHITE)
            press2 = self.font.render("[2] DEFI SURVIE (Solo)", True, WHITE)
            press3 = self.font.render("[3] HOST ONLINE (Local IP)", True, (100, 255, 100))
            press4 = self.font.render("[4] JOIN ONLINE (Entrer IP)", True, (100, 200, 255))
            press5 = self.font.render("[5] PARAMETRES (Touches)", True, (200, 200, 200))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4))
            self.screen.blit(press1, (WIDTH//2 - press1.get_width()//2, HEIGHT//2 - 50))
            self.screen.blit(press2, (WIDTH//2 - press2.get_width()//2, HEIGHT//2))
            self.screen.blit(press3, (WIDTH//2 - press3.get_width()//2, HEIGHT//2 + 50))
            self.screen.blit(press4, (WIDTH//2 - press4.get_width()//2, HEIGHT//2 + 100))
            self.screen.blit(press5, (WIDTH//2 - press5.get_width()//2, HEIGHT//2 + 150))
            
            # Sound status
            s_state = "OUI" if self.audio.enabled else "NON"
            audio_hint = self.font.render(f"[M] SON : {s_state}", True, (255, 255, 0))
            self.screen.blit(audio_hint, (WIDTH//2 - audio_hint.get_width()//2, HEIGHT//2 + 220))
            
            pygame.display.flip()
            return

        if self.state == 'SETTINGS':
            self.screen.fill((20, 25, 40))
            title = self.large_font.render("PARAMETRES DES TOUCHES", True, WHITE)
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 40))
            
            def draw_keys_col(x, title, controls, color, keys_start):
                h_surf = self.font.render(title, True, color)
                self.screen.blit(h_surf, (x, 150))
                y = 200
                actions = ['left', 'right', 'jump', 'down', 'attack', 'special']
                for i, action in enumerate(actions):
                    key_name = pygame.key.name(controls[action]).upper()
                    if self.remapping and self.remapping_target == (1 if title=="JOUEUR 1" else 2, action):
                        key_name = "[ ? ]"
                    shortcut = keys_start[i]
                    txt = self.font.render(f"[{shortcut}] {action.capitalize()}: {key_name}", True, WHITE)
                    self.screen.blit(txt, (x, y))
                    y += 40

            draw_keys_col(WIDTH//2 - 350, "JOUEUR 1", self.controls_p1, (100, 100, 255), ["1", "2", "3", "4", "5", "6"])
            draw_keys_col(WIDTH//2 + 50, "JOUEUR 2", self.controls_p2, (255, 100, 100), ["F1", "F2", "F3", "F4", "F5", "F6"])
            
            s_state = "OUI" if self.audio.enabled else "NON"
            hint6 = self.font.render(f"[7] SON : {s_state}", True, (255, 255, 0))
            self.screen.blit(hint6, (WIDTH//2 - hint6.get_width()//2, 450))

            hint = self.font.render("Echap pour quitter", True, (150, 150, 150))
            self.screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT - 80))
            pygame.display.flip()
            return

        if self.state == 'VICTORY':
            self.screen.fill((10, 10, 20))
            v_surf = self.large_font.render(self.winner_text, True, (255, 200, 0))
            sub = self.font.render("Pressez ENTREE pour le menu", True, WHITE)
            self.screen.blit(v_surf, (WIDTH//2 - v_surf.get_width()//2, HEIGHT//2 - 50))
            self.screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 50))
            pygame.display.flip()
            return
            
        if self.state == 'NET_JOIN':
            self.screen.fill((20, 20, 30))
            title = self.font.render("ENTRER L'ADRESSE IP DU SERVEUR", True, WHITE)
            ip_surf = self.large_font.render(self.net_ip_input + "_", True, (0, 255, 255))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3))
            self.screen.blit(ip_surf, (WIDTH//2 - ip_surf.get_width()//2, HEIGHT//2))
            pygame.display.flip()
            return
            
        if self.state == 'CHAR_SELECT':
            self.screen.fill((30, 30, 45))
            title = self.font.render("SELECTION DES PERSONNAGES", True, (255, 255, 255))
            self.screen.blit(title, (WIDTH//2 - title.get_width()//2, 50))
            
            # Draw options
            for i, char in enumerate(self.available_chars):
                rect = pygame.Rect(WIDTH//2 - 200 + i*220, HEIGHT//2 - 100, 180, 250)
                bg_col = (50, 50, 70)
                if self.p1_selection == i: bg_col = (100, 100, 255)
                if self.p2_selection == i: bg_col = (255, 100, 100)
                if self.p1_selection == i and self.p2_selection == i: bg_col = (200, 100, 255)
                
                pygame.draw.rect(self.screen, bg_col, rect, border_radius=15)
                pygame.draw.rect(self.screen, WHITE, rect, 2, border_radius=15)
                
                # Highlight selection
                if i == self.p1_selection:
                    pygame.draw.rect(self.screen, (255, 255, 0), rect, 4)
                if i == self.p2_selection:
                    pygame.draw.rect(self.screen, (0, 255, 255), rect, 2)

                # Draw character sprite preview
                if char['preview']:
                    s_w, s_h = char['preview'].get_size()
                    scaled = pygame.transform.scale(char['preview'], (rect.width - 20, rect.height - 20))
                    self.screen.blit(scaled, (rect.x + 10, rect.y + 10))
                else:
                    # Generic icon if no sprite
                    inner = rect.inflate(-40, -40)
                    pygame.draw.circle(self.screen, char['color'], inner.center, 30)

                name_surf = self.font.render(f"[{i+1}] {char['name']}", True, WHITE)
                self.screen.blit(name_surf, (rect.centerx - name_surf.get_width()//2, rect.bottom + 10))

            # Stage display
            stage_name = self.available_stages[self.stage_selection]['name']
            stage_surf = self.font.render(f"CARTE : {stage_name}", True, (255, 200, 0))
            self.screen.blit(stage_surf, (WIDTH//2 - stage_surf.get_width()//2, HEIGHT - 180))

            help1 = self.font.render("P1: ZQSD/1-4  -- P2: Flèches/6-9  -- [TAB] Carte", True, (200, 200, 200))
            help2 = self.font.render("S/BAS pour changer de SKIN !", True, (200, 255, 200))
            help3 = self.font.render("Pressez [ESPACE] pour COMBATTRE !", True, (255, 200, 0))
            self.screen.blit(help1, (WIDTH//2 - help1.get_width()//2, HEIGHT - 130))
            self.screen.blit(help2, (WIDTH//2 - help2.get_width()//2, HEIGHT - 100))
            self.screen.blit(help3, (WIDTH//2 - help3.get_width()//2, HEIGHT - 70))
            
            pygame.display.flip()
            return

        # Draw level
        self.current_stage.draw(self.screen, render_offset_x, render_offset_y)
        
        if self.state == 'VERSUS':
            self.item_manager.draw(self.screen, render_offset_x, render_offset_y)
            
        for p in self.players:
            # We must pass the offset to player draw
            p.draw(self.screen, self.font, render_offset_x, render_offset_y)
            
        self.effect_manager.draw(self.screen, render_offset_x, render_offset_y)
        
        # HUD / Scores
        if self.state == 'VERSUS':
            # Draw timer and scores
            mins = int(self.round_time_left // 60)
            secs = int(self.round_time_left % 60)
            t_surf = self.large_font.render(f"{mins:02d}:{secs:02d}", True, WHITE)
            self.screen.blit(t_surf, (WIDTH//2 - t_surf.get_width()//2, 20))
            
            s_surf = self.font.render(f"P1: {self.p1_wins}  -  P2: {self.p2_wins}", True, (255, 200, 0))
            self.screen.blit(s_surf, (WIDTH//2 - s_surf.get_width()//2, 80))

        # Render panels
        if self.state == 'CHALLENGE_TARGETS':
            # Draw score and time
            time_elapsed = (pygame.time.get_ticks() - self.challenge_start_time) / 1000.0
            info = self.font.render(f"Cibles: {self.current_stage.targets_destroyed}/{self.current_stage.total_targets}  -- Temps: {time_elapsed:.2f}s", True, WHITE)
            self.screen.blit(info, (WIDTH//2 - info.get_width()//2, 50))
            if self.current_stage.targets_destroyed >= self.current_stage.total_targets:
                win_text = self.font.render(" DEFI REUSSI ! ", True, GREEN)
                self.screen.blit(win_text, (WIDTH//2 - win_text.get_width()//2, 100))
                
        # Draw UI on top without offset
        if self.state == 'VERSUS':
            # Player 1 UI (Bottom Left)
            draw_player_panel(self.screen, self.font, "JOUEUR 1 (Chevalier)", self.p1.damage, self.p1.color, getattr(self, 'p1_wins', 0), 20, HEIGHT - 130)
            
            # Player 2 UI (Bottom Right)
            draw_player_panel(self.screen, self.font, "JOUEUR 2 (Mage)", self.p2.damage, self.p2.color, getattr(self, 'p2_wins', 0), WIDTH - 320, HEIGHT - 130)
            
            # Draw Round Winner text
            if getattr(self, 'round_end_timer', 0) > 0:
                overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                self.screen.blit(overlay, (0, 0))
                
                large_font = pygame.font.SysFont('Arial', 50, bold=True)
                wt = large_font.render(self.winner_text, True, (255, 200, 0))
                self.screen.blit(wt, (WIDTH//2 - wt.get_width()//2, HEIGHT//2))
            
        speed_text = self.font.render(f"FPS: {int(self.clock.get_fps())}", True, WHITE)
        self.screen.blit(speed_text, (10, 10))
        
        pygame.display.flip()

    def run(self):
        while self.running:
            # dt is bounded to prevent simulation explosion on lag spike (max 0.1s dt)
            dt = min(self.clock.tick(FPS) / 1000.0, 0.1)
            # Apply game speed modifier
            dt *= GAME_SPEED
            
            self.events()
            self.update(dt)
            self.draw()
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
