from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse, Triangle, Quad, Line, Mesh
from kivy.properties import NumericProperty, BooleanProperty, StringProperty, ListProperty, ObjectProperty
from kivy.uix.widget import Widget
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDListItem, MDListItemHeadlineText
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
import sqlite3
import math
from datetime import datetime

CANDLES = {
    'test': {'name': 'Test Flame', 'seconds': 5, 'icon': 'flask-outline', 'color': [0.2, 0.6, 0.8, 1], 'price': 0},
    'pillar': {'name': 'Simple Pillar', 'seconds': 15 * 60, 'icon': 'cylinder', 'color': [0.9, 0.7, 0.3, 1], 'price': 0},
    'pyramid': {'name': 'Pine Pyramid', 'seconds': 30 * 60, 'icon': 'triangle-outline', 'color': [0.3, 0.6, 0.3, 1], 'price': 0},
    'orb': {'name': 'Magic Orb', 'seconds': 45 * 60, 'icon': 'circle-outline', 'color': [0.8, 0.4, 0.6, 1], 'price': 0},
    'block': {'name': 'Sturdy Block', 'seconds': 60 * 60, 'icon': 'square-outline', 'color': [0.6, 0.4, 0.2, 1], 'price': 0},
    'dragon': {'name': 'Dragon Scale', 'seconds': 90 * 60, 'icon': 'fire', 'color': [0.8, 0.2, 0.2, 1], 'price': 20},
    'crystal': {'name': 'Ice Crystal', 'seconds': 120 * 60, 'icon': 'snowflake', 'color': [0.4, 0.8, 0.9, 1], 'price': 30},
    'lotus': {'name': 'Serene Lotus', 'seconds': 45 * 60, 'icon': 'flower-outline', 'color': [0.9, 0.5, 0.8, 1], 'price': 15},
    'mystery': {'name': 'Mystery Box', 'seconds': 0, 'icon': 'help-box-outline', 'color': [0.5, 0.3, 0.7, 1], 'price': 10, 'is_mystery': True}
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
                     
        c.execute('''CREATE TABLE IF NOT EXISTS candle_inventory (
                     candle_id TEXT PRIMARY KEY)''')
                     
        # Seed default unlocks
        c.execute('SELECT COUNT(*) FROM candle_inventory')
        if c.fetchone()[0] == 0:
            for c_id, data in CANDLES.items():
                if data.get('price', 0) == 0:
                     c.execute('INSERT INTO candle_inventory (candle_id) VALUES (?)', (c_id,))
                     
        c.execute('''CREATE TABLE IF NOT EXISTS custom_candles (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     name TEXT,
                     points TEXT,
                     duration INTEGER,
                     color TEXT)''')
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

    def get_unlocked_candles(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT candle_id FROM candle_inventory')
        unlocked = [row[0] for row in c.fetchall()]
        conn.close()
        return unlocked
        
    def unlock_candle(self, candle_id, price):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT embers_balance FROM user WHERE id=1')
        bal = c.fetchone()[0]
        if bal >= price:
            c.execute('UPDATE user SET embers_balance = embers_balance - ? WHERE id=1', (price,))
            c.execute('INSERT OR IGNORE INTO candle_inventory (candle_id) VALUES (?)', (candle_id,))
            conn.commit()
            success = True
        else:
            success = False
        conn.close()
        return success
        
    def get_custom_candles(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT id, name, points, duration, color FROM custom_candles')
        res = c.fetchall()
        conn.close()
        return res
        
    def add_custom_candle(self, name, points_json, duration, _color='[0.8, 0.4, 0.2, 1]', price=5):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT embers_balance FROM user WHERE id=1')
        bal = c.fetchone()[0]
        if bal >= price:
            c.execute('UPDATE user SET embers_balance = embers_balance - ? WHERE id=1', (price,))
            c.execute('INSERT INTO custom_candles (name, points, duration, color) VALUES (?, ?, ?, ?)',
                      (name, points_json, duration, _color))
            conn.commit()
            success = True
        else:
            success = False
        conn.close()
        return success

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
    total_time = NumericProperty(0)
    custom_points = ListProperty([])
    custom_color = ListProperty([0.5, 0.5, 0.5, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time_elapsed = 0
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

            elif self.candle_type in ['dragon', 'crystal', 'lotus']:
                # Special premium regular shapes
                w_prem = 110
                Color(*dark_color)
                Ellipse(pos=(cx - w_prem/2, base_y - 12), size=(w_prem, 24))
                Color(*c_color)
                # Drawing a slightly curved body (using a quad that narrows slightly)
                w_top = w_prem * 0.8
                Quad(points=(cx - w_prem/2, base_y, 
                             cx + w_prem/2, base_y, 
                             cx + w_top/2, base_y + current_h, 
                             cx - w_top/2, base_y + current_h))
                Color(*light_color)
                Ellipse(pos=(cx - w_top/2, base_y + current_h - 8), size=(w_top, 16))
                flame_y = base_y + current_h + 5
                
            elif self.candle_type == 'mystery':
                total_m = max(10, min(120, float(self.total_time) / 60.0)) if self.total_time > 0 else 60.0
                scale = min(1.0, max(0.2, total_m / 120.0))
                w_myst = 60 + 80 * scale
                h_myst = 80 + 100 * scale
                current_myst_h = h_myst * self.melt_progress
                
                Color(*dark_color)
                Ellipse(pos=(cx - w_myst/2, base_y - 10), size=(w_myst, 20))
                Color(*c_color)
                Rectangle(pos=(cx - w_myst/2, base_y), size=(w_myst, current_myst_h))
                Color(*light_color)
                Ellipse(pos=(cx - w_myst/2, base_y + current_myst_h - 10), size=(w_myst, 20))
                flame_y = base_y + current_myst_h + 5
                
            elif self.candle_type == 'custom':
                current_h_ratio = self.melt_progress
                if self.custom_points:
                    scaled_pts = []
                    for px, py in self.custom_points:
                        # px and py are 0 to 1 relative
                        ox = cx + (px - 0.5) * 200
                        oy = base_y + py * 200 * current_h_ratio
                        scaled_pts.extend([ox, oy])
                    
                    if len(scaled_pts) >= 6:
                        Color(*self.custom_color)
                        Line(points=scaled_pts, width=3, close=True)
                        indices = list(range(len(scaled_pts)//2))
                        Mesh(vertices=[v for v in scaled_pts for _ in (0, 0)], indices=indices, mode='triangle_fan')
                        
                    flame_y = base_y + 200 * current_h_ratio + 5
                else:
                    flame_y = base_y + 10

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
    is_mystery = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.db = Database()
        self.timer_event = None
        self.remaining_time = 0
        self.alarm_sound = None
        super().__init__(**kwargs)

    def on_kv_post(self, base_widget):
        self.load_carousel()

    def on_pre_enter(self, *args):
        if 'candle_carousel' in self.ids:
            self.load_carousel()

    def load_carousel(self):
        carousel = self.ids.candle_carousel
        carousel.clear_widgets()
        unlocked = self.db.get_unlocked_candles()
        
        for c_id, data in CANDLES.items():
            if c_id not in unlocked:
                continue
                
            if data.get('is_mystery'):
                t_str = "???"
            elif data['seconds'] < 60:
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
            
        customs = self.db.get_custom_candles()
        for cid, name, pts, dur, color in customs:
            card = CandleCard(
                candle_id=f"custom_{cid}",
                icon_source="fountain-pen-tip",
                candle_name=name,
                candle_time=f"{dur // 60} min",
                icon_color=eval(color)
            )
            carousel.add_widget(card)

        if not self.selected_candle:
            self.update_selected_candle('test')

    def update_selected_candle(self, c_id):
        if self.timer_event: return
        
        if self.alarm_sound:
            self.alarm_sound.stop()
            self.alarm_sound = None
            
        self.selected_candle = c_id
        
        if c_id.startswith('custom_'):
            db_c = next((c for c in self.db.get_custom_candles() if str(c[0]) == c_id.split('_')[1]), None)
            if db_c:
                self.ids.selected_candle_label.text = db_c[1]
                mins, secs = divmod(db_c[3], 60)
                self.ids.timer_label.text = f"{mins:02d}:{secs:02d}"
                self.remaining_time = db_c[3]
                self.ids.candle_widget.candle_type = 'custom'
                self.ids.candle_widget.custom_points = eval(db_c[2])
                self.ids.candle_widget.custom_color = eval(db_c[4])
                self.is_mystery = False
        else:
            data = CANDLES[c_id]
            self.ids.selected_candle_label.text = f"{data['name']}"
            self.ids.candle_widget.candle_type = c_id
            
            if data.get('is_mystery'):
                self.ids.timer_label.text = "???"
                self.remaining_time = 0
                self.is_mystery = True
            else:
                mins, secs = divmod(int(data['seconds']), 60)
                self.ids.timer_label.text = f"{mins:02d}:{secs:02d}"
                self.remaining_time = int(data['seconds'])
                self.is_mystery = False
                
        self.ids.candle_widget.melt_progress = 1.0
        self.ids.candle_widget.flame_active = False
        self.ids.start_btn.disabled = False
        self.ids.pause_btn.disabled = True
        self.ids.pause_btn_text.text = "Pause"

    def start_timer(self):
        if not self.timer_event:
            import random
            
            if self.selected_candle.startswith('custom_'):
                db_c = next((c for c in self.db.get_custom_candles() if str(c[0]) == self.selected_candle.split('_')[1]), None)
                if not db_c: return
                total_t = db_c[3]
                if self.remaining_time <= 0:
                    self.remaining_time = total_t
            else:
                data = CANDLES[self.selected_candle]
                if self.is_mystery and self.remaining_time <= 0:
                    self.remaining_time = random.randint(10 * 60, 120 * 60)
                    self.ids.candle_widget.total_time = self.remaining_time
                    total_t = self.remaining_time
                else:
                    total_t = int(data['seconds']) if not self.is_mystery else self.ids.candle_widget.total_time
                    if self.remaining_time <= 0:
                        self.remaining_time = total_t
            
            self.ids.candle_widget.start_melt(total_t)
            self.ids.candle_widget.time_elapsed = total_t - self.remaining_time

            self.ids.start_btn.disabled = True
            self.ids.pause_btn.disabled = False
            self.timer_event = Clock.schedule_interval(self.update_timer, 1)

    def pause_timer(self):
        if self.ids.pause_btn_text.text == "Stop & Reset":
            if self.alarm_sound:
                self.alarm_sound.stop()
                self.alarm_sound = None
            self.update_selected_candle(self.selected_candle)
            return

        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
            self.ids.start_btn.disabled = False
            self.ids.pause_btn.disabled = True
            self.ids.candle_widget.flame_active = False

    def update_timer(self, dt):
        self.remaining_time -= 1
        
        if not self.is_mystery:
            mins, secs = divmod(self.remaining_time, 60)
            self.ids.timer_label.text = f"{mins:02d}:{secs:02d}"
        else:
            self.ids.timer_label.text = "???"
            
        if self.remaining_time <= 0:
            self.stop_timer(completed=True)

    def stop_timer(self, completed=False):
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None
        
        self.ids.candle_widget.flame_active = False
        
        if completed:
            self.ids.timer_label.text = "Burnt Out!"
            if self.selected_candle.startswith('custom_'):
                db_c = next((c for c in self.db.get_custom_candles() if str(c[0]) == self.selected_candle.split('_')[1]), None)
                if db_c: self.db.add_session(db_c[3], db_c[1])
            else:
                data = CANDLES[self.selected_candle]
                if self.is_mystery:
                    self.db.add_session(self.ids.candle_widget.total_time, data['name'])
                else:
                    self.db.add_session(int(data['seconds']), data['name'])
            
            self.alarm_sound = SoundLoader.load('assets/candle_out.mp3')
            if self.alarm_sound: 
                self.alarm_sound.loop = True
                self.alarm_sound.play()
                
            self.remaining_time = 0
            self.ids.start_btn.disabled = True
            self.ids.pause_btn.disabled = False
            self.ids.pause_btn_text.text = "Stop & Reset"
            
        else:
            self.ids.start_btn.disabled = False
            self.ids.pause_btn.disabled = True

class ShopCard(MDCard):
    candle_id = StringProperty()
    icon_source = StringProperty()
    candle_name = StringProperty()
    candle_price = NumericProperty(0)
    icon_color = ListProperty([1, 1, 1, 1])
    shop_screen = ObjectProperty(None)

class WaxShopScreen(Screen):
    def on_enter(self):
        self.load_shop()

    def load_shop(self):
        db = Database()
        self.ids.balance_label.text = f"Embers: {db.get_balance()}"
        
        grid = self.ids.shop_grid
        grid.clear_widgets()
        
        unlocked = db.get_unlocked_candles()
        
        for c_id, data in CANDLES.items():
            if c_id in unlocked: continue # Only show locked ones
            if data.get('price', 0) <= 0: continue
            
            card = ShopCard(
                candle_id=c_id,
                icon_source=data['icon'],
                candle_name=data['name'],
                candle_price=data['price'],
                icon_color=data['color'],
                shop_screen=self
            )
            grid.add_widget(card)

    def buy_candle(self, c_id, price):
        db = Database()
        success = db.unlock_candle(c_id, price)
        if success:
            self.load_shop() # Reload to remove purchased item and update balance

class DrawCanvas(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.draw_points = []
        self._line = None

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            with self.canvas:
                Color(1, 1, 1, 1)
                self._line = Line(points=[touch.x, touch.y], width=2)
            self.draw_points.append((touch.x, touch.y))
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._line and self.collide_point(*touch.pos):
            self._line.points += [touch.x, touch.y]
            self.draw_points.append((touch.x, touch.y))
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._line:
            self._line = None
            return True
        return super().on_touch_up(touch)
        
    def clear_canvas(self):
        self.canvas.clear()
        self.draw_points = []
        # Re-draw background since clear removes it all
        with self.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            Rectangle(pos=self.pos, size=self.size)

    def get_normalized_points(self):
        if not self.draw_points: return []
        xs = [p[0] for p in self.draw_points]
        ys = [p[1] for p in self.draw_points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        w = max(1, max_x - min_x)
        h = max(1, max_y - min_y)
        
        norm = []
        for x, y in self.draw_points:
            norm.append( ((x - min_x) / w, (y - min_y) / h) )
        return norm

class ForgeScreen(Screen):
    def on_enter(self):
        db = Database()
        self.ids.forge_bal.text = f"Balance: {db.get_balance()} Embers"

    def forge_candle(self):
        pts = self.ids.draw_area.get_normalized_points()
        if not pts: return
        
        db = Database()
        import random
        dur = random.randint(30*60, 90*60)
        
        colors = ['[0.8, 0.3, 0.3, 1]', '[0.3, 0.8, 0.3, 1]', '[0.3, 0.3, 0.8, 1]', '[0.8, 0.8, 0.3, 1]', '[0.8, 0.3, 0.8, 1]']
        c = random.choice(colors)
        
        success = db.add_custom_candle("My Custom Flame", str(pts), dur, c, price=5)
        if success:
            self.ids.draw_area.clear_canvas()
            self.manager.current = 'hearth'
            
        self.ids.forge_bal.text = f"Balance: {db.get_balance()} Embers"

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
        self.sm.add_widget(ForgeScreen(name='forge'))
        self.sm.add_widget(GraveyardScreen(name='graveyard'))
        return self.sm

    def select_candle(self, c_id):
        hearth = self.sm.get_screen('hearth')
        hearth.update_selected_candle(c_id)

if __name__ == '__main__':
    LitUpFocusApp().run()