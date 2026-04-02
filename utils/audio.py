import pygame
import array
import math

class SoundManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls)
            cls._instance.enabled = True
            cls._instance.sounds = {}
            cls._instance.init_sounds()
        return cls._instance
    
    def init_sounds(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=1)
            self.sounds['jump'] = self._generate_tone(440, 880, 0.1, pulse=True)
            self.sounds['hit'] = self._generate_noise(0.15, volume=0.5)
            self.sounds['attack'] = self._generate_tone(600, 300, 0.05, pulse=False)
            self.sounds['death'] = self._generate_tone(400, 100, 0.5, pulse=True)
            self.sounds['victory'] = self._generate_tone(523, 1046, 0.8, pulse=True) # C5 to C6
        except Exception as e:
            print(f"Erreur Audio: {e}")
            self.enabled = False

    def _generate_tone(self, start_freq, end_freq, duration, pulse=False):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        
        for i in range(n_samples):
            t = i / sample_rate
            # Frequency sweep
            freq = start_freq + (end_freq - start_freq) * (i / n_samples)
            val = math.sin(2 * math.pi * freq * t)
            
            if pulse:
                # Square-ish wave
                val = 1.0 if val > 0 else -1.0
                
            # Envelope (fade out)
            volume = 1.0 - (i / n_samples)
            buf[i] = int(val * volume * 32767 * 0.3)
            
        return pygame.mixer.Sound(buffer=buf)

    def _generate_noise(self, duration, volume=0.5):
        import random
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = array.array('h', [0] * n_samples)
        
        for i in range(n_samples):
            val = random.uniform(-1, 1)
            # Envelope
            v = (1.0 - (i / n_samples)) * volume
            buf[i] = int(val * v * 32767 * 0.3)
            
        return pygame.mixer.Sound(buffer=buf)

    def play(self, name):
        try:
            if self.enabled and name in self.sounds:
                self.sounds[name].play()
        except:
            pass

    def toggle(self):
        self.enabled = not self.enabled
        return self.enabled
