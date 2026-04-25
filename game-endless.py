import pygame
import pygame.gfxdraw
import random
import sys
import math

# --- 1. 基础配置 ---
pygame.init()
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("CyberDuck: Tutorial & Grid Fixed")
clock = pygame.time.Clock()

C_VOID = (10, 10, 25); C_GOLD = (255, 220, 50); C_PINK = (255, 50, 150)
C_CYAN = (0, 255, 255); C_WHITE = (255, 255, 255); C_PURPLE = (160, 50, 255)
C_BTN = (30, 30, 70); C_BTN_H = (50, 50, 120)

GAME_DATA = {"coins": 1000, "current_color": C_GOLD, "owned_skins": ["Classic Gold"]}
SHOP_ITEMS = [
    {"name": "Classic Gold", "color": C_GOLD, "price": 0},
    {"name": "Neon Cyan", "color": C_CYAN, "price": 500},
    {"name": "Rose Pink", "color": C_PINK, "price": 1000},
    {"name": "Royal Purple", "color": C_PURPLE, "price": 2000}
]

current_page = "MAIN_MENU"
GROUND_Y = HEIGHT - 80

# --- 2. 核心动画与角色类 ---
def draw_neon_portal(surf, x, y, time):
    pulse = math.sin(time * 0.01) * 10
    for i in range(5):
        r = pygame.Rect(x - 30 + i*2, y - 90 + i*2 - pulse, 60 - i*4, 180 - i*4 + pulse*2)
        pygame.draw.ellipse(surf, C_CYAN, r, 2)

class Player:
    def __init__(self):
        self.pos = pygame.Vector2(150, GROUND_Y - 50); self.vel_y = 0
        self.jump_count, self.angle, self.squash = 0, 0, 1.0
        self.is_crouching = False; self.ghosts = [] 

    def jump(self):
        if self.jump_count < 2 and not self.is_crouching: 
            self.vel_y = -17; self.jump_count += 1; self.squash = 1.4

    def update(self, platforms):
        keys = pygame.key.get_pressed()
        self.is_crouching = keys[pygame.K_c]
        target_squash = 0.35 if self.is_crouching else 1.0
        self.squash += (target_squash - self.squash) * 0.25
        
        if not self.is_crouching:
            self.vel_y += 0.85; self.pos.y += self.vel_y
            self.angle = self.angle - 12 if self.jump_count > 0 else self.angle * 0.8
        else:
            self.vel_y = 0; self.angle *= 0.5
            if self.pos.y + 50 < GROUND_Y: self.pos.y += 12 

        self.ghosts.append((self.pos.x, self.pos.y, self.angle, self.squash, self.is_crouching))
        if len(self.ghosts) > 6: self.ghosts.pop(0)
        if self.pos.y + 50 >= GROUND_Y: self.pos.y, self.vel_y, self.jump_count = GROUND_Y-50, 0, 0
        
        if not self.is_crouching and self.vel_y >= 0:
            foot = pygame.Rect(self.pos.x, self.pos.y+40, 45, 10)
            for p in platforms:
                if foot.colliderect(p) and self.pos.y + 40 < p.centery:
                    self.pos.y, self.vel_y, self.jump_count = p.top-50, 0, 0

    def draw(self, surf, color=None):
        c = color if color else GAME_DATA["current_color"]
        for i, g in enumerate(self.ghosts): self._draw_duck(surf, g[0], g[1], g[2], g[3], 30 + i*30, c, g[4])
        self._draw_duck(surf, self.pos.x, self.pos.y, self.angle, self.squash, 255, c, self.is_crouching)

    def _draw_duck(self, surf, x, y, angle, squash, alpha, color, crouching):
        h = int(50 * squash); w = int(45 * (1.8 if crouching else 2.0 - squash))
        s = pygame.Surface((150, 150), pygame.SRCALPHA)
        pygame.gfxdraw.filled_ellipse(s, 75, 75, w//2, h//2, (*color, alpha))
        pygame.draw.rect(s, (*C_CYAN, alpha), (75+w//4, 75-h//4, 16, 4 if crouching else 8), border_radius=2)
        rot = pygame.transform.rotate(s, angle)
        surf.blit(rot, (x - rot.get_width()//2 + 22, y - rot.get_height()//2 + 25))

# --- 3. 游戏关卡 ---
def run_game(lvl):
    player = Player()
    speed = 10 + (lvl * 1.5)
    portal_x = 5500 + (lvl * 800)
    platforms, hazards = [], []

    curr_x = 1200
    while curr_x < portal_x - 1000:
        choice = random.random()
        # 教学关卡（Lvl 1）强制生成简单的障碍
        if lvl == 1:
            if curr_x < 3000: # 前半段地雷跳跃教学
                hazards.append({'rect': pygame.Rect(curr_x, GROUND_Y-45, 42, 45), 'type': 'mine'})
            else: # 后半段激光滑行教学
                hazards.append({'rect': pygame.Rect(curr_x, GROUND_Y-120, 240, 35), 'type': 'laser'})
        else:
            # 5-8关特供电网
            if 5 <= lvl <= 8 and choice < 0.3:
                hazards.append({'rect': pygame.Rect(curr_x, GROUND_Y-250, 50, 160), 'type': 'grid', 'base_y': GROUND_Y-220, 'offset': random.random()*10})
                curr_x += 350
            elif choice < 0.75: # 高密度地雷
                num = random.randint(1, 4)
                for n in range(num): hazards.append({'rect': pygame.Rect(curr_x + n*65, GROUND_Y-45, 42, 45), 'type': 'mine'})
                curr_x += num * 110
            else: # 激光
                hazards.append({'rect': pygame.Rect(curr_x, GROUND_Y-120, 240, 35), 'type': 'laser'})
                curr_x += 450
            
        if random.random() > 0.4: platforms.append(pygame.Rect(curr_x - 150, GROUND_Y-180, 250, 20))
        curr_x += random.randint(300, 550)

    state = "PLAY"; ticks = 0
    while True:
        screen.fill(C_VOID); ticks += 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if state == "PLAY": player.jump()
                else: return

        if state == "PLAY":
            player.update(platforms); portal_x -= speed
            p_h = 20 if player.is_crouching else 45
            p_y = player.pos.y + (30 if player.is_crouching else 5)
            hit_box = pygame.Rect(player.pos.x+10, p_y, 25, p_h)
            for h in hazards: 
                h['rect'].x -= speed
                if h.get('type') == 'grid': h['rect'].y = h['base_y'] + math.sin((ticks + h['offset']) * 0.05) * 120
                if hit_box.colliderect(h['rect']):
                    if not (h['type'] == 'laser' and player.is_crouching): state = "DEAD"
            for p in platforms: p.x -= speed
            if portal_x <= player.pos.x + 20: state = "WIN"; GAME_DATA["coins"] += lvl * 50

        # 绘制
        pygame.draw.rect(screen, (20,20,50), (0, GROUND_Y, WIDTH, HEIGHT))
        for p in platforms: pygame.draw.rect(screen, C_CYAN, p, border_radius=6)
        for h in hazards:
            if h.get('type') == 'grid':
                pygame.draw.rect(screen, C_PURPLE, h['rect'], border_radius=5)
                if ticks % 4 < 2: pygame.draw.line(screen, C_WHITE, (h['rect'].left, h['rect'].centery), (h['rect'].right, h['rect'].centery), 3)
            else:
                col = C_PINK if h['type'] == 'laser' else C_GOLD
                pygame.draw.rect(screen, col, h['rect'], border_radius=8)

        draw_neon_portal(screen, portal_x, GROUND_Y-80, pygame.time.get_ticks())
        player.draw(screen)

        # --- 第一关教学文本修复 ---
        if lvl == 1 and state == "PLAY":
            f = pygame.font.SysFont("Impact", 40)
            if portal_x > 3200:
                msg = f.render("SPACE TO JUMP OVER MINES", True, C_GOLD)
                screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 150))
            elif portal_x > 1500:
                msg = f.render("HOLD TO SLIDE UNDER LASERS", True, C_PINK)
                screen.blit(msg, (WIDTH//2 - msg.get_width()//2, 150))

        if state != "PLAY":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA); overlay.fill((0,0,0,180)); screen.blit(overlay, (0,0))
            f = pygame.font.SysFont("Impact", 90).render("CLEAR" if state == "WIN" else "WASTED", True, C_WHITE)
            screen.blit(f, (WIDTH//2-f.get_width()//2, 220))
        pygame.display.flip(); clock.tick(60)
def run_endless():
    player = Player()
    speed = 10
    platforms, hazards = [], []
    curr_x = 1200
    distance = 0
    ticks = 0
    state = "PLAY"

    # 初始生成一段地图（和普通关卡类似）
    while curr_x < 4000:
        choice = random.random()
        if choice < 0.7:
            hazards.append({'rect': pygame.Rect(curr_x, GROUND_Y-45, 42, 45), 'type': 'mine'})
            curr_x += random.randint(250, 400)
        else:
            hazards.append({'rect': pygame.Rect(curr_x, GROUND_Y-120, 240, 35), 'type': 'laser'})
            curr_x += 450

        if random.random() > 0.5:
            platforms.append(pygame.Rect(curr_x - 150, GROUND_Y-180, 250, 20))

    while True:
        screen.fill(C_VOID)
        ticks += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if state == "PLAY":
                    player.jump()
                else:
                    return

        if state == "PLAY":
            player.update(platforms)

            speed += 0.002
            distance += speed

            # 移动
            for h in hazards:
                h['rect'].x -= speed
                if h.get('type') == 'grid':
                    h['rect'].y = h['base_y'] + math.sin((ticks + h['offset']) * 0.05) * 120

            for p in platforms:
                p.x -= speed

            # ⭐ 动态生成（关键）
            if hazards and hazards[-1]['rect'].x < WIDTH:
                new_x = hazards[-1]['rect'].x + random.randint(300, 600)
                choice = random.random()

                if choice < 0.6:
                    hazards.append({'rect': pygame.Rect(new_x, GROUND_Y-45, 42, 45), 'type': 'mine'})
                elif choice < 0.85:
                    hazards.append({'rect': pygame.Rect(new_x, GROUND_Y-120, 240, 35), 'type': 'laser'})
                else:
                    hazards.append({
                        'rect': pygame.Rect(new_x, GROUND_Y-250, 50, 160),
                        'type': 'grid',
                        'base_y': GROUND_Y-220,
                        'offset': random.random()*10
                    })

                if random.random() > 0.5:
                    platforms.append(pygame.Rect(new_x - 120, GROUND_Y-180, 220, 20))

            # 碰撞
            p_h = 20 if player.is_crouching else 45
            p_y = player.pos.y + (30 if player.is_crouching else 5)
            hit_box = pygame.Rect(player.pos.x+10, p_y, 25, p_h)

            for h in hazards:
                if hit_box.colliderect(h['rect']):
                    if not (h['type'] == 'laser' and player.is_crouching):
                        state = "DEAD"

        # ===== 绘制（完全复用你原风格）=====
        pygame.draw.rect(screen, (20,20,50), (0, GROUND_Y, WIDTH, HEIGHT))

        for p in platforms:
            pygame.draw.rect(screen, C_CYAN, p, border_radius=6)

        for h in hazards:
            if h.get('type') == 'grid':
                pygame.draw.rect(screen, C_PURPLE, h['rect'], border_radius=5)
                if ticks % 4 < 2:
                    pygame.draw.line(screen, C_WHITE,
                        (h['rect'].left, h['rect'].centery),
                        (h['rect'].right, h['rect'].centery), 3)
            else:
                col = C_PINK if h['type'] == 'laser' else C_GOLD
                pygame.draw.rect(screen, col, h['rect'], border_radius=8)

        player.draw(screen)

        # ⭐ 距离显示（无尽核心）
        dist_txt = pygame.font.SysFont("Impact", 40).render(f"DIST: {int(distance)}", True, C_WHITE)
        screen.blit(dist_txt, (20, 20))

        if state != "PLAY":
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,180))
            screen.blit(overlay, (0,0))

            f = pygame.font.SysFont("Impact", 90).render("WASTED", True, C_WHITE)
            screen.blit(f, (WIDTH//2-f.get_width()//2, 220))

        pygame.display.flip()
        clock.tick(60)

# --- 4. 界面逻辑 ---
class AnimatedButton:
    def __init__(self, text, x, y, w, h, idle_col, hover_col):
        self.text, self.base_rect = text, pygame.Rect(x, y, w, h); self.scale = 1.0
    def update(self, disabled=False):
        m_pos, click = pygame.mouse.get_pos(), pygame.mouse.get_pressed()[0]
        hover = self.base_rect.collidepoint(m_pos) and not disabled
        self.scale += ((1.1 if hover else 1.0) - self.scale) * 0.2
        return hover and click
    def draw(self, surf, disabled=False):
        color = (60,60,60) if disabled else (C_BTN_H if self.base_rect.collidepoint(pygame.mouse.get_pos()) else C_BTN)
        rect = self.base_rect.inflate(self.base_rect.width*(self.scale-1), self.base_rect.height*(self.scale-1))
        pygame.draw.rect(surf, color, rect, border_radius=12)
        f = pygame.font.SysFont("Impact", int(28*self.scale)).render(self.text, True, C_WHITE)
        surf.blit(f, (rect.centerx-f.get_width()//2, rect.centery-f.get_height()//2))

start_y = 230
gap = 90

m_btns = [
    AnimatedButton("START GAME", 350, start_y + gap*0, 300, 70, C_BTN, C_BTN_H),
    AnimatedButton("NEON SHOP", 350, start_y + gap*1, 300, 70, C_BTN, C_BTN_H),
    AnimatedButton("ABOUT", 350, start_y + gap*2, 300, 70, C_BTN, C_BTN_H),
    AnimatedButton("ENDLESS", 350, start_y + gap*3, 300, 70, C_BTN, C_BTN_H)
]
l_btns = [AnimatedButton(str(i+1), 230+(i%5)*110, 220+(i//5)*100, 85, 85, C_BTN, C_BTN_H) for i in range(10)]
shop_btns = [AnimatedButton("GET", 720, 185+i*100, 110, 50, (40,80,40), (60,120,60)) for i in range(len(SHOP_ITEMS))]
back_btn = AnimatedButton("BACK", 50, 40, 110, 50, (100,30,30), (160,40,40))


while True:
    screen.fill(C_VOID); t = pygame.time.get_ticks()
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()

    if current_page == "MAIN_MENU":
        f = pygame.font.SysFont("Impact", 100).render("CYBER DUCK", True, C_GOLD)
        screen.blit(f, (WIDTH//2-f.get_width()//2, 100 + math.sin(t*0.005)*15))
        if m_btns[0].update(): pygame.time.delay(200); current_page = "LEVEL_SELECT"
        if m_btns[1].update(): pygame.time.delay(200); current_page = "SHOP"
        if m_btns[2].update(): pygame.time.delay(200); current_page = "ABOUT"
        if m_btns[3].update():
            pygame.time.delay(200)
            run_endless()
        for b in m_btns: b.draw(screen)

    elif current_page == "LEVEL_SELECT":
        if back_btn.update(): current_page = "MAIN_MENU"
        back_btn.draw(screen)
        for i, lb in enumerate(l_btns):
            if lb.update(): pygame.time.delay(200); run_game(i+1)
            lb.draw(screen)

    elif current_page == "SHOP":
        draw_s = pygame.font.SysFont("Impact", 45).render(f"COINS: {GAME_DATA['coins']}", True, C_GOLD)
        screen.blit(draw_s, (WIDTH//2-draw_s.get_width()//2, 40))
        for i, item in enumerate(SHOP_ITEMS):
            y = 170 + i*100
            pygame.draw.rect(screen, (30,30,80), (150, y, 700, 80), border_radius=15)
            p_v = Player(); p_v.pos = pygame.Vector2(190, y+15); p_v.is_crouching = (t//500 % 2 == 0); p_v.draw(screen, item["color"])
            owned = item["name"] in GAME_DATA["owned_skins"]; is_using = (GAME_DATA["current_color"] == item["color"])
            shop_btns[i].text = "USING" if is_using else ("EQUIP" if owned else f"${item['price']}")
            disabled = is_using or (not owned and GAME_DATA["coins"] < item["price"])
            if shop_btns[i].update(disabled):
                if not owned: GAME_DATA["coins"] -= item["price"]; GAME_DATA["owned_skins"].append(item["name"])
                else: GAME_DATA["current_color"] = item["color"]
            shop_btns[i].draw(screen, disabled)
            nt = pygame.font.SysFont("Impact", 30).render(item["name"], True, item["color"])
            screen.blit(nt, (300, y+22))
        if back_btn.update(): current_page = "MAIN_MENU"
        back_btn.draw(screen)

    elif current_page == "ABOUT":
        if back_btn.update(): current_page = "MAIN_MENU"
        back_btn.draw(screen)
        info = ["Producer: Zhang Shuhao", "Phone nuber: +86 17868782889","C: SLIDE | SPACE: JUMP", "V12.0 Fixed Tutorial"]
        for i, txt in enumerate(info):
            it = pygame.font.SysFont("Impact", 40).render(txt, True, C_WHITE)
            screen.blit(it, (WIDTH//2-it.get_width()//2, 280 + i*60))

    pygame.display.flip(); clock.tick(60)