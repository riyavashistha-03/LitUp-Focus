from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse, Triangle, Quad
from kivy.properties import NumericProperty, BooleanProperty, StringProperty, ListProperty
from kivy.uix.widget import Widget
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDListItem, MDListItemHeadlineText
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
import sqlite3
import math
from datetime import datetime

CANDLES = {
    'test': {'name': 'Test Flame', 'seconds': 5, 'icon': 'flask-outline', 'color': [0.2, 0.6, 0.8, 1]},
    'pillar': {'name': 'Simple Pillar', 'seconds': 15 * 60, 'icon': 'cylinder', 'color': [0.9, 0.7, 0.3, 1]},
    'pyramid': {'name': 'Pine Pyramid', 'seconds': 30 * 60, 'icon': 'triangle-outline', 'color': [0.3, 0.6, 0.3, 1]},
    'orb': {'name': 'Magic Orb', 'seconds': 45 * 60, 'icon': 'circle-outline', 'color': [0.8, 0.4, 0.6, 1]},
    'block': {'name': 'Sturdy Block', 'seconds': 60 * 60, 'icon': 'square-outline', 'color': [0.6, 0.4, 0.2, 1]}
}

class Database:
    def __init__(self, db_path='litup_focus.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS user (
                     id INTEGER PRIMARY KEY,
                     embers_balance INTEGER DEFAULT 0,
                     total_study_time INTEGER DEFAULT 0)''')
        c.execute('INSERT OR IGNORE INTO user (id) VALUES (1)')
        c.execute('''CREATE TABLE IF NOT EXISTS sessions (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     timestamp TEXT,
                     duration_minutes INTEGER,
                     candle_type TEXT,
                     embers_earned INTEGER)''')
        conn.commit()
        conn.close()

    def get_balance(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT embers_balance FROM user WHERE id=1')
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0

    def add_session(self, duration_seconds, candle_type):
        minutes = duration_seconds // 60
        embers = max(1, minutes // 10) # Give at least 1 ember for testing
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        timestamp = datetime.now().isoformat()
        c.execute('INSERT INTO sessions (timestamp, duration_minutes, candle_type, embers_earned) VALUES (?, ?, ?, ?)',
                  (timestamp, minutes, candle_type, embers))
        c.execute('UPDATE user SET embers_balance = embers_balance + ?, total_study_time = total_study_time + ? WHERE id=1', 
                  (embers, minutes))
        conn.commit()
        conn.close()

    def get_sessions(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT timestamp, duration_minutes, candle_type, embers_earned FROM sessions ORDER BY id DESC LIMIT 20')
        result = c.fetchall()
        conn.close()
        return result

class CandleCard(MDCard):
    candle_id = StringProperty()
    icon_source = StringProperty()
    candle_name = StringProperty()
    candle_time = StringProperty()
    icon_color = ListProperty([0, 0, 0, 1])

class Candle(Widget):
    melt_progress = NumericProperty(1.0)
    flame_active = BooleanProperty(False)
    candle_type = StringProperty('test')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time_elapsed = 0
        self.total_time = 0
        Clock.schedule_interval(self.update_melt, 1/60.)

    def start_melt(self, total_time):
        self.total_time = total_time
        self.time_elapsed = 0
        self.melt_progress = 1.0
        self.flame_active = True

    def update_melt(self, dt):
        if self.flame_active:
            self.time_elapsed += dt
            if self.total_time > 0:
                self.melt_progress = max(0, 1 - (self.time_elapsed / self.total_time))
        
        self.canvas.clear()
        
        cx = self.center_x
        base_y = self.y + 40
        w = 100
        max_h = 160
        current_h = max_h * self.melt_progress
        
        data = CANDLES.get(self.candle_type, CANDLES['test'])
        c_color = data['color']
        
        # Calculate specialized colors
        r, g, b, a = float(c_color[0]), float(c_color[1]), float(c_color[2]), float(c_color[3])
        dark_color = [max(0.0, r-0.2), max(0.0, g-0.2), max(0.0, b-0.2), 1.0]
        light_color = [min(1.0, r+0.2), min(1.0, g+0.2), min(1.0, b+0.2), 1.0]

        with self.canvas:
            # Base plate/Shadow
            Color(0.05, 0.05, 0.05, 0.8)
            Ellipse(pos=(cx - w*0.8, base_y - 20), size=(w*1.6, 40))
            
            # Bronze/Wooden Holder
            Color(0.3, 0.2, 0.1, 1)
            Rectangle(pos=(cx - w*0.6, base_y - 15), size=(w*1.2, 10))
            Ellipse(pos=(cx - w*0.6, base_y - 20), size=(w*1.2, 10))

            if self.candle_type in ['test', 'pillar']:
                # Pillar Candle
                # Bottom curve
                Color(*dark_color)
                Ellipse(pos=(cx - w/2, base_y - 10), size=(w, 20))
                
                # Main body
                Color(*c_color)
                Rectangle(pos=(cx - w/2, base_y), size=(w, current_h))
                
                # Top pool
                Color(*light_color)
                Ellipse(pos=(cx - w/2, base_y + current_h - 10), size=(w, 20))
                
                # Wax drip
                if self.melt_progress < 0.95 and self.melt_progress > 0:
                    Color(*c_color)
                    Ellipse(pos=(cx - w*0.45, base_y + current_h - 30), size=(10, 30))
                    Ellipse(pos=(cx - w*0.45, base_y + current_h - 40), size=(10, 10))

                    Ellipse(pos=(cx + w*0.35, base_y + current_h - 20), size=(8, 20))
                    Ellipse(pos=(cx + w*0.35, base_y + current_h - 26), size=(8, 8))

                flame_y = base_y + current_h + 5

            elif self.candle_type == 'pyramid':
                w_base = 120
                w_top = w_base * (1 - self.melt_progress) + 10 # Never perfectly sharp
                
                Color(*dark_color)
                Ellipse(pos=(cx - w_base/2, base_y - 10), size=(w_base, 20))
                
                Color(*c_color)
                Quad(points=(cx - w_base/2, base_y, 
                             cx + w_base/2, base_y, 
                             cx + w_top/2, base_y + current_h, 
                             cx - w_top/2, base_y + current_h))
                
                Color(*light_color)
                Ellipse(pos=(cx - w_top/2, base_y + current_h - 5), size=(w_top, 10))
                flame_y = base_y + current_h + 5

            elif self.candle_type == 'orb':
                w_orb = 120
                h_orb = 120 * self.melt_progress
                w_current = w_orb * self.melt_progress
                
                Color(*dark_color)
                Ellipse(pos=(cx - w_current/2, base_y - 5), size=(w_current, 10))
                
                Color(*c_color)
                Ellipse(pos=(cx - w_current/2, base_y), size=(w_current, h_orb))
                
                Color(*light_color)
                Ellipse(pos=(cx - w_current/2, base_y + h_orb - 8), size=(w_current, 16))
                flame_y = base_y + h_orb + 5

            elif self.candle_type == 'block':
                w_block = 140
                Color(*dark_color)
                Rectangle(pos=(cx - w_block/2, base_y), size=(w_block, max_h * 0.7 * self.melt_progress))
                Color(*c_color)
                Rectangle(pos=(cx - w_block/2 + 5, base_y + 5), size=(w_block - 10, max_h * 0.7 * self.melt_progress - 5))
                Color(*light_color)
                Quad(points=(cx - w_block/2, base_y + max_h * 0.7 * self.melt_progress,
                             cx + w_block/2, base_y + max_h * 0.7 * self.melt_progress,
                             cx + w_block/2 - 10, base_y + max_h * 0.7 * self.melt_progress + 15,
                             cx - w_block/2 + 10, base_y + max_h * 0.7 * self.melt_progress + 15))
                flame_y = base_y + (max_h * 0.7 * self.melt_progress) + 10

            # Draw Wick
            if self.melt_progress > 0:
                Color(0.1, 0.1, 0.1, 1)
                Rectangle(pos=(cx - 2, flame_y - 12), size=(4, 15))
                if not self.flame_active:
                    Color(0.5, 0.1, 0.1, 1) # Red glowing wick bit
                    Ellipse(pos=(cx - 2.5, flame_y - 2), size=(5, 5))
                
            # Draw multi-layered complex Flame
            if self.flame_active and self.melt_progress > 0:
                t = self.time_elapsed
                # Complex noise to simulate real flicker
                flicker = 0.8 + 0.1 * math.sin(t * 15) + 0.05 * math.sin(t * 27) + 0.05 * math.sin(t * 7)
                wind_x = 3 * math.sin(t * 10) + 1 * math.sin(t * 31)
                
                # Outer Halo Glow
                Color(1, 0.6, 0.1, 0.15 * flicker) 
                glow_r = 140 * flicker
                Ellipse(pos=(cx + wind_x - glow_r/2, flame_y - glow_r*0.2), size=(glow_r, glow_r))
                
                # Middle Orange Flame
                Color(1, 0.4, 0.0, 0.8)
                flame_w, flame_h = 28 * flicker, 45 * flicker
                Ellipse(pos=(cx + wind_x*0.6 - flame_w/2, flame_y - 5), size=(flame_w, flame_h))
                
                # Inner Yellow Flame
                Color(1, 0.9, 0.2, 0.9)
                in_w, in_h = flame_w * 0.6, flame_h * 0.6
                Ellipse(pos=(cx + wind_x*0.3 - in_w/2, flame_y + flame_h*0.1), size=(in_w, in_h))
                
                # Core White Flame
                Color(1, 1, 1, 1)
                core_w, core_h = in_w * 0.4, in_h * 0.4
                Ellipse(pos=(cx - core_w/2, flame_y + flame_h*0.15), size=(core_w, core_h))

class HearthScreen(Screen):
    selected_candle = StringProperty('test')

    def __init__(self, **kwargs):
        self.db = Database()
        self.timer_event = None
        self.remaining_time = 0
        self.alarm_sound = None  # Store the audio object
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        carousel = self.ids.candle_carousel
        for c_id, data in CANDLES.items():
            if data['seconds'] < 60:
                t_str = f"{data['seconds']} sec"
            else:
                t_str = f"{data['seconds'] // 60} min"
                
            card = CandleCard(
                candle_id=c_id,
                icon_source=data['icon'],
                candle_name=data['name'],
                candle_time=t_str,
                icon_color=data['color']
            )
            carousel.add_widget(card)
        self.update_selected_candle('test')

    def update_selected_candle(self, c_id):
        if self.timer_event: return
        
        # Ensure alarm stops if user clicks a new candle while it's ringing
        if self.alarm_sound:
            self.alarm_sound.stop()
            self.alarm_sound = None
            
        self.selected_candle = c_id
        data = CANDLES[c_id]
        
        mins, secs = divmod(data['seconds'], 60)
        
        self.ids.selected_candle_label.text = f"{data['name']}"
        self.ids.timer_label.text = f"{mins:02d}:{secs:02d}"
        self.remaining_time = data['seconds']
        
        self.ids.candle_widget.candle_type = c_id
        self.ids.candle_widget.melt_progress = 1.0
        self.ids.candle_widget.flame_active = False
        
        # Reset Buttons
        self.ids.start_btn.disabled = False
        self.ids.pause_btn.disabled = True
        self.ids.pause_btn_text.text = "Pause"

    def start_timer(self):
        if not self.timer_event:
            data = CANDLES[self.selected_candle]
            if self.remaining_time <= 0:
                self.remaining_time = data['seconds']
            
            self.ids.candle_widget.start_melt(data['seconds'])
            self.ids.candle_widget.time_elapsed = data['seconds'] - self.remaining_time

            self.ids.start_btn.disabled = True
            self.ids.pause_btn.disabled = False
            self.timer_event = Clock.schedule_interval(self.update_timer, 1)

    def pause_timer(self):
        # 1. Check if the button is currently acting as a "Stop Alarm" button
        if self.ids.pause_btn_text.text == "Stop & Reset":
            if self.alarm_sound:
                self.alarm_sound.stop()
                self.alarm_sound = None
            self.update_selected_candle(self.selected_candle) # Resets UI back to starting state
            return

        # 2. Otherwise, act as a normal Pause button
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
            self.ids.start_btn.disabled = False
            self.ids.pause_btn.disabled = True
            self.ids.candle_widget.flame_active = False

    def update_timer(self, dt):
        self.remaining_time -= 1
        mins, secs = divmod(self.remaining_time, 60)
        self.ids.timer_label.text = f"{mins:02d}:{secs:02d}"
        
        if self.remaining_time <= 0:
            self.stop_timer(completed=True)

    def stop_timer(self, completed=False):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        
        self.ids.candle_widget.flame_active = False
        
        if completed:
            self.ids.timer_label.text = "Burnt Out!"
            data = CANDLES[self.selected_candle]
            self.db.add_session(data['seconds'], data['name'])
            
            # Play alarm and set it to loop
            self.alarm_sound = SoundLoader.load('assets/candle_out.mp3')
            if self.alarm_sound: 
                self.alarm_sound.loop = True
                self.alarm_sound.play()
                
            self.remaining_time = 0
            
            # Switch the pause button into a Stop/Reset Button
            self.ids.start_btn.disabled = True
            self.ids.pause_btn.disabled = False
            self.ids.pause_btn_text.text = "Stop & Reset"
            
        else:
            self.ids.start_btn.disabled = False
            self.ids.pause_btn.disabled = True

class WaxShopScreen(Screen):
    def on_enter(self):
        db = Database()
        self.ids.balance_label.text = f"Embers: {db.get_balance()}"

class GraveyardScreen(Screen):
    def on_enter(self):
        db = Database()
        self.ids.sessions_list.clear_widgets()
        for sess in db.get_sessions():
            ts, mins, candle, emb = sess
            date = ts.split('T')[0]
            item = MDListItem(
                MDListItemHeadlineText(text=f"{date} | {mins}m | {candle} | +{emb} Embers")
            )
            self.ids.sessions_list.add_widget(item)

class LitUpFocusApp(MDApp):
    def build(self):
        Builder.load_file('litup_focus.kv')
        self.theme_cls.theme_style = "Dark" 
        self.theme_cls.primary_palette = "Orange" 
        
        self.sm = ScreenManager()
        self.sm.add_widget(HearthScreen(name='hearth'))
        self.sm.add_widget(WaxShopScreen(name='shop'))
        self.sm.add_widget(GraveyardScreen(name='graveyard'))
        return self.sm

    def select_candle(self, c_id):
        hearth = self.sm.get_screen('hearth')
        hearth.update_selected_candle(c_id)

if __name__ == '__main__':
    LitUpFocusApp().run()