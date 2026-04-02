import pygame

# Display settings
WIDTH = 1280
HEIGHT = 720
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Physics Constants
GRAVITY = 3000           # pixels per second^2
FRICTION_GROUND = 10     # lerp factor for ground sliding
FRICTION_AIR = 2         # lerp factor for air drifting
MAX_FALL_SPEED = 1200
TERMINAL_KNOCKBACK = 3000

# Base Player Attributes
BASE_SPEED = 400
BASE_JUMP_FORCE = -1000
BASE_DASH_MULTIPLIER = 1.8

# Blast zones (padding around screen before dying)
BLAST_ZONE_PADDING = 300

# Game Speed factor
GAME_SPEED = 1.0
