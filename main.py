import pygame, random, math, json, os
pygame.init()
WIDTH, HEIGHT = 2610, 1320
GW, GH = 640, 360
FPS = 60
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("RETRO HERO - 16 BIT ADVENTURE")
game = pygame.Surface((GW, GH))
clock = pygame.time.Clock()

BLACK=(8,8,15); WHITE=(255,255,255); RED=(220,50,55)
DARK_RED=(110,25,35); GREEN=(60,180,80); DARK_GREEN=(30,90,45)
BLUE=(70,130,210); DARK_BLUE=(30,50,100); CYAN=(50,210,220)
YELLOW=(255,220,60); GOLD=(255,180,40); ORANGE=(240,120,40)
PURPLE=(145,70,200); GRAY=(110,115,130); DARK_GRAY=(45,45,55)
BROWN=(125,70,40); PINK=(230,80,150)

FONT_S=pygame.font.Font(None,18)
FONT=pygame.font.Font(None,25)
FONT_B=pygame.font.Font(None,42)
FONT_H=pygame.font.Font(None,62)

SAVE_FILE="retro_hero_save.json"
DEFAULT_SAVE={"coins":0,"owned":["classic"],"skin":"classic"}

def load_save():
    if not os.path.exists(SAVE_FILE): return DEFAULT_SAVE.copy()
    try:
        with open(SAVE_FILE,"r") as f: d=json.load(f)
        if not isinstance(d,dict): return DEFAULT_SAVE.copy()
        d["coins"]=max(0,int(d.get("coins",0)))
        d["owned"]=d.get("owned",["classic"])
        if not isinstance(d["owned"],list): d["owned"]=["classic"]
        d["owned"]=[x for x in d["owned"] if x in SKINS]
        if "classic" not in d["owned"]: d["owned"].insert(0,"classic")
        d["skin"]=d.get("skin","classic")
        if d["skin"] not in d["owned"]: d["skin"]="classic"
        return d
    except Exception: return DEFAULT_SAVE.copy()

SKINS={
"classic":{"name":"CLASSIC","price":0,"body":(220,50,60),"dark":(110,25,35),"helmet":(240,240,240)},
"ninja":{"name":"NINJA","price":75,"body":(45,45,60),"dark":(15,15,25),"helmet":(120,80,170)},
"knight":{"name":"KNIGHT","price":150,"body":(100,120,145),"dark":(45,55,75),"helmet":(220,225,235)},
"cyber":{"name":"CYBER","price":250,"body":(40,200,210),"dark":(10,80,95),"helmet":(210,250,255)},
"shadow":{"name":"SHADOW","price":400,"body":(70,40,100),"dark":(25,12,40),"helmet":(170,80,220)},
"gold":{"name":"GOLD","price":600,"body":(220,165,35),"dark":(115,70,10),"helmet":(255,235,120)},
"fire":{"name":"FIRE","price":850,"body":(240,70,25),"dark":(120,25,10),"helmet":(255,200,50)},
"legend":{"name":"LEGEND","price":1200,"body":(185,50,180),"dark":(70,15,75),"helmet":(70,220,255)}
}
save_data=load_save()

MENU,SHOP,PLAYING,PAUSED,GAME_OVER,LEVEL_CLEAR,VICTORY=range(7)
state=MENU
level=1
WORLD_WIDTH=16000
platforms=[]; coins=[]; enemies=[]; projectiles=[]; particles=[]; texts=[]
camera_x=0
joystick_center=[75,300]; joystick_pos=[75,300]; joystick_active=False
jump_pressed=False; attack_pressed=False
jump_lock=False
shop_index=0

def save_game():
    try:
        with open(SAVE_FILE,"w") as f: json.dump(save_data,f,indent=2)
    except Exception: pass

def rect_screen(r):
    return pygame.Rect(int(r.x-camera_x),int(r.y),r.width,r.height)

def text_center(surface,text,font,color,y):
    img=font.render(text,True,color)
    surface.blit(img,(surface.get_width()//2-img.get_width()//2,y))

def spawn_particles(x,y,color,amount=8):
    for _ in range(amount):
        a=random.random()*math.tau; s=random.uniform(.5,2.8)
        particles.append({"x":x,"y":y,"vx":math.cos(a)*s,"vy":math.sin(a)*s,
                          "life":random.randint(15,35),"color":color,"size":random.randint(1,3)})

def add_text(value,x,y,color=WHITE):
    texts.append({"text":value,"x":x,"y":y,"life":45,"color":color})

class Player:
    def __init__(self):
        self.rect=pygame.Rect(80,250,18,27)
        self.vx=0; self.vy=0; self.speed=3.8; self.jump=8.8
        self.gravity=.42; self.ground=False; self.facing=1
        self.lives=3; self.coins=save_data["coins"]; self.checkpoint=80
        self.invincible=0; self.attack_timer=0; self.attack_cooldown=0; self.anim=0
    def reset(self):
        self.rect.x=int(self.checkpoint); self.rect.y=220
        self.vx=0; self.vy=0; self.invincible=90
    def hurt(self):
        if self.invincible: return
        self.lives-=1
        spawn_particles(self.rect.centerx,self.rect.centery,RED,18)
        if self.lives<=0: set_state(GAME_OVER)
        else: self.reset()
    def do_jump(self):
        if self.ground:
            self.vy=-self.jump; self.ground=False
            spawn_particles(self.rect.centerx,self.rect.bottom,WHITE,5)
    def attack(self):
        if not self.attack_cooldown:
            self.attack_timer=9; self.attack_cooldown=17
    def attack_rect(self):
        if self.facing>0: return pygame.Rect(self.rect.right,self.rect.y+5,15,15)
        return pygame.Rect(self.rect.left-15,self.rect.y+5,15,15)
    def update(self):
        global jump_pressed, attack_pressed
        if self.invincible: self.invincible-=1
        if self.attack_timer: self.attack_timer-=1
        if self.attack_cooldown: self.attack_cooldown-=1
        self.anim+=1
        keys=pygame.key.get_pressed()
        move=0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: move-=1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: move+=1
        if joystick_active:
            dx=joystick_pos[0]-joystick_center[0]
            if abs(dx)>5: move=max(-1,min(1,dx/30))
        self.vx=move*self.speed
        if move: self.facing=1 if move>0 else -1
        if jump_pressed: self.do_jump()
        if attack_pressed: self.attack()
        self.rect.x+=int(self.vx)
        for p in platforms:
            if self.rect.colliderect(p):
                if self.vx>0: self.rect.right=p.left
                elif self.vx<0: self.rect.left=p.right
        self.vy=min(self.vy+self.gravity,8)
        old_bottom=self.rect.bottom; old_top=self.rect.top
        self.rect.y+=int(self.vy); self.ground=False
        for p in platforms:
            if not self.rect.colliderect(p): continue
            if self.vy>0 and old_bottom<=p.top:
                self.rect.bottom=p.top; self.vy=0; self.ground=True
            elif self.vy<0 and old_top>=p.bottom:
                self.rect.top=p.bottom; self.vy=0
    def draw(self):
        if self.invincible and self.invincible//5%2==0: return
        skin=SKINS[save_data["skin"]]; r=rect_screen(self.rect)
        if save_data["skin"] in ("shadow","fire","legend"):
            pygame.draw.rect(game,skin["dark"],(r.x-5*self.facing,r.y+8,6,15))
        pygame.draw.rect(game,skin["dark"],(r.x+3,r.y+21,5,6))
        pygame.draw.rect(game,skin["dark"],(r.x+11,r.y+21,5,6))
        pygame.draw.rect(game,skin["body"],(r.x+3,r.y+8,12,15))
        pygame.draw.rect(game,skin["helmet"],(r.x+2,r.y,14,11))
        pygame.draw.rect(game,(255,205,170),(r.x+4,r.y+4,10,7))
        eye_x=r.x+11 if self.facing>0 else r.x+5
        pygame.draw.rect(game,BLACK,(eye_x,r.y+5,2,2))
        if self.attack_timer: pygame.draw.rect(game,WHITE,rect_screen(self.attack_rect()))

class Enemy:
    def __init__(self,x,y,kind):
        self.kind=kind; self.rect=pygame.Rect(x,y,20,20); self.vy=0
        self.direction=random.choice([-1,1]); self.timer=random.randint(0,100)
        self.left=x-80; self.right=x+80; self.health=1
        sizes={"tank":(25,25,3),"bat":(20,14,1),"runner":(18,22,1),
               "shooter":(20,22,2),"ghost":(18,22,2),"boss":(64,64,20)}
        if kind in sizes:
            w,h,hp=sizes[kind]; self.rect.size=(w,h); self.health=hp
            self.left=x-(200 if kind=="boss" else 80)
            self.right=x+(200 if kind=="boss" else 80)
    def damage(self):
        self.health-=1
        spawn_particles(self.rect.centerx,self.rect.centery,YELLOW,7)
        if self.health<=0:
            spawn_particles(self.rect.centerx,self.rect.centery,RED,20)
            reward=50 if self.kind=="boss" else 10
            player.coins+=reward; add_text("+"+str(reward),self.rect.x,self.rect.y,GOLD)
            return True
        return False
    def update(self):
        self.timer+=1
        if self.kind=="slime":
            self.vy=min(self.vy+.4,7); self.rect.y+=int(self.vy)
            for p in platforms:
                if self.rect.colliderect(p) and self.vy>0:
                    self.rect.bottom=p.top; self.vy=-5
            self.rect.x+=self.direction
        elif self.kind=="bat":
            self.rect.x+=self.direction
            self.rect.y+=math.sin(self.timer*.08)*.5
            if self.rect.left<self.left or self.rect.right>self.right: self.direction*=-1
        elif self.kind=="runner":
            dx=player.rect.centerx-self.rect.centerx
            if abs(dx)<220: self.direction=1 if dx>0 else -1; self.rect.x+=self.direction*2.5
            else: self.rect.x+=self.direction
        elif self.kind=="tank":
            self.rect.x+=self.direction*.7
            if self.rect.left<self.left or self.rect.right>self.right: self.direction*=-1
        elif self.kind=="shooter":
            self.rect.x+=self.direction*.5
            if self.rect.left<self.left or self.rect.right>self.right: self.direction*=-1
            if self.timer%100==0: shoot_at_player(self.rect.centerx,self.rect.centery,2.5)
        elif self.kind=="ghost":
            dx=player.rect.centerx-self.rect.centerx; dy=player.rect.centery-self.rect.centery
            d=math.hypot(dx,dy)
            if 20<d<280: self.rect.x+=int(dx/d); self.rect.y+=int(dy/d)
        elif self.kind=="boss":
            dx=player.rect.centerx-self.rect.centerx
            if abs(dx)>80: self.rect.x+=1.1 if dx>0 else -1.1
            if self.timer%75==0: shoot_at_player(self.rect.centerx,self.rect.centery,2.4)
            if self.timer%180==0:
                for angle in range(0,360,45):
                    rad=math.radians(angle)
                    projectiles.append(Projectile(self.rect.centerx,self.rect.centery,
                                                  self.rect.centerx+math.cos(rad)*100,
                                                  self.rect.centery+math.sin(rad)*100,1.7))
    def draw(self):
        r=rect_screen(self.rect)
        if self.kind=="slime":
            pygame.draw.rect(game,GREEN,r); pygame.draw.rect(game,BLACK,(r.x+4,r.y+4,3,3)); pygame.draw.rect(game,BLACK,(r.x+13,r.y+4,3,3))
        elif self.kind=="bat":
            pygame.draw.polygon(game,PURPLE,[(r.centerx,r.y),(r.right,r.bottom),(r.centerx,r.bottom-3),(r.left,r.bottom)])
        elif self.kind=="runner":
            pygame.draw.rect(game,RED,r); pygame.draw.rect(game,WHITE,(r.x+3,r.y+4,4,4))
        elif self.kind=="tank":
            pygame.draw.rect(game,DARK_GRAY,r); pygame.draw.rect(game,GRAY,(r.x+4,r.y+3,17,7))
        elif self.kind=="shooter":
            pygame.draw.rect(game,ORANGE,r); pygame.draw.rect(game,BLACK,(r.x+4,r.y+5,12,6))
        elif self.kind=="ghost":
            pygame.draw.rect(game,(190,190,255),(r.x+3,r.y,12,17))
            pygame.draw.polygon(game,(190,190,255),[(r.x+3,r.y+14),(r.x+9,r.bottom),(r.x+15,r.y+14)])
            pygame.draw.rect(game,BLACK,(r.x+5,r.y+5,3,3))
        elif self.kind=="boss":
            pygame.draw.rect(game,DARK_RED,r); pygame.draw.rect(game,RED,(r.x+7,r.y+7,r.width-14,r.height-14))
            pygame.draw.rect(game,BLACK,(r.x+15,r.y+18,10,8)); pygame.draw.rect(game,BLACK,(r.x+39,r.y+18,10,8))
            pygame.draw.rect(game,BLACK,(r.x,r.y-9,r.width,5))
            pygame.draw.rect(game,RED,(r.x,r.y-9,int(r.width*self.health/20),5))

class Projectile:
    def __init__(self,x,y,tx,ty,speed=2.5):
        self.x=x; self.y=y; self.life=180
        dx=tx-x; dy=ty-y; d=math.hypot(dx,dy) or 1
        self.vx=dx/d*speed; self.vy=dy/d*speed
        self.rect=pygame.Rect(x,y,5,5)
    def update(self):
        self.x+=self.vx; self.y+=self.vy; self.rect.center=(int(self.x),int(self.y)); self.life-=1
    def draw(self): pygame.draw.rect(game,RED,rect_screen(self.rect))

def shoot_at_player(x,y,speed=2.5):
    projectiles.append(Projectile(x,y,player.rect.centerx,player.rect.centery,speed))

class Coin:
    def __init__(self,x,y):
        self.x=x; self.y=y; self.timer=random.randint(0,100); self.rect=pygame.Rect(x-5,y-5,10,10)
    def update(self): self.timer+=1
    def draw(self):
        bounce=math.sin(self.timer*.12)*2; x=int(self.x-camera_x); y=int(self.y+bounce)
        pygame.draw.circle(game,GOLD,(x,y),5); pygame.draw.rect(game,YELLOW,(x-1,y-3,2,6))

def generate_level(number):
    global platforms,enemies,coins,projectiles,WORLD_WIDTH
    platforms=[]; enemies=[]; coins=[]; projectiles=[]
    random.seed(number*1000); ground=320 if number==1 else 325
    WORLD_WIDTH=16000 if number==1 else 20000
    step=280 if number==1 else 250
    gap=.07 if number==1 else .11
    for x in range(0,WORLD_WIDTH,step):
        if random.random()<gap: continue
        platforms.append(pygame.Rect(x,ground,step if number==1 else step,40 if number==1 else 35))
    for x in range(180,WORLD_WIDTH-200,170 if number==1 else 140):
        if number==1 and random.random()>=.72: continue
        platforms.append(pygame.Rect(x,random.randint(150,275),random.randint(60,130),12))
    types=["slime","bat","runner","tank","shooter"] if number==1 else ["slime","bat","runner","tank","shooter","ghost"]
    for x in range(500,WORLD_WIDTH-(500 if number==1 else 700),300 if number==1 else 250):
        enemies.append(Enemy(x,ground-25,random.choice(types)))
    if number==2: enemies.append(Enemy(WORLD_WIDTH-600,ground-64,"boss"))
    for x in range(250,WORLD_WIDTH-(300 if number==1 else 500),150 if number==1 else 130):
        if random.random()<.8: coins.append(Coin(x,random.randint(110,270)))

def start_level(number):
    global level,camera_x,flag
    level=number; generate_level(number)
    player.rect.x=80; player.rect.y=220; player.checkpoint=80; player.invincible=60
    camera_x=0; flag=pygame.Rect(WORLD_WIDTH-200,190,15,130)

def set_state(new_state):
    global state
    state=new_state

def draw_background():
    if level==1:
        game.fill((90,150,215))
        pygame.draw.circle(game,(255,230,130),(535-int(camera_x*.04),55),28)
        for x in range(-300,1000,160):
            px=x-int(camera_x*.15)
            pygame.draw.polygon(game,(65,100,155),[(px,320),(px+80,150),(px+160,320)])
        for x in range(-100,1000,280):
            px=x-int(camera_x*.07)
            pygame.draw.rect(game,WHITE,(px,65,60,13)); pygame.draw.circle(game,WHITE,(px+20,65),17)
    else:
        game.fill((22,27,68)); pygame.draw.circle(game,(245,240,190),(520-int(camera_x*.03),50),27)
        random.seed(50)
        for _ in range(75):
            pygame.draw.rect(game,WHITE,(random.randint(0,GW),random.randint(20,170),1,1))
        for x in range(-200,1000,160):
            px=x-int(camera_x*.12)
            pygame.draw.polygon(game,(40,35,85),[(px,320),(px+80,150),(px+160,320)])

def draw_level():
    for p in platforms:
        r=rect_screen(p)
        if r.right<0 or r.left>GW: continue
        main=GREEN if level==1 and p.height<20 else DARK_GREEN if level==1 else GRAY if p.height<20 else DARK_GRAY
        top=(110,220,110) if level==1 else (160,160,175)
        pygame.draw.rect(game,main,r); pygame.draw.rect(game,top,(r.x,r.y,r.width,3))

def draw_flag():
    r=rect_screen(flag); pygame.draw.rect(game,WHITE,r)
    pygame.draw.polygon(game,RED,[(r.x+4,r.y),(r.x+35,r.y+12),(r.x+4,r.y+24)])
    
    def draw_ui():
         pygame.draw.rect(game,(15,15,25),(0,0,GW,30))
    pygame.draw.circle(game,GOLD,(15,15),5)
    game.blit(FONT_S.render(str(player.coins),True,WHITE),(25,8))
    game.blit(FONT_S.render("♥ "+str(player.lives),True,WHITE),(70,8))
    game.blit(FONT_S.render("LEVEL "+str(level),True,WHITE),(275,8))
    progress=max(0,min(1,player.rect.x/WORLD_WIDTH))
    pygame.draw.rect(game,DARK_GRAY,(380,10,150,7)); pygame.draw.rect(game,CYAN,(380,10,int(progress*150),7))

def draw_controls():
    pygame.draw.circle(game,(35,35,45),joystick_center,38); pygame.draw.circle(game,(100,100,110),joystick_center,38,3)
    pygame.draw.circle(game,(215,215,220),joystick_pos,17)
    pygame.draw.circle(game,(70,60,90),(480,330),29); text_center_at("ATK",FONT_S,WHITE,480,324)
    pygame.draw.circle(game,GREEN,(575,305),35); text_center_at("JUMP",FONT_S,WHITE,575,299)

def text_center_at(txt,font,color,x,y):
    img=font.render(txt,True,color); game.blit(img,(x-img.get_width()//2,y))

def update_effects():
    for p in particles[:]:
        p["x"]+=p["vx"]; p["y"]+=p["vy"]; p["vy"]+=.08; p["life"]-=1
        if p["life"]<=0: particles.remove(p)
    for t in texts[:]:
        t["y"]-=.5; t["life"]-=1
        if t["life"]<=0: texts.remove(t)

def draw_effects():
    for p in particles:
        pygame.draw.rect(game,p["color"],(int(p["x"]-camera_x),int(p["y"]),p["size"],p["size"]))
    for t in texts:
        game.blit(FONT_S.render(t["text"],True,t["color"]),(int(t["x"]-camera_x),int(t["y"])))

def draw_menu():
    game.fill((14,18,42))
    for x in range(-100,800,120):
        pygame.draw.polygon(game,(28,45,85),[(x,320),(x+60,160),(x+120,320)])
    text_center(game,"RETRO",FONT_H,CYAN,45); text_center(game,"HERO",FONT_H,GOLD,100)
    skin=SKINS[save_data["skin"]]
    pygame.draw.rect(game,skin["body"],(310,180,20,35)); pygame.draw.rect(game,skin["helmet"],(308,165,24,20))
    for label,y in [("ENTER  -  START",235),("S      -  SKIN SHOP",270)]:
        r=pygame.Rect(220,y,200,27); pygame.draw.rect(game,(50,60,100),r); pygame.draw.rect(game,CYAN,r,2)
        text_center(game,label,FONT,WHITE,y+4)
    text_center(game,"WASD / ARROWS MOVE",FONT_S,WHITE,315)
    text_center(game,"SPACE / W / UP = JUMP     Z / X = ATTACK",FONT_S,WHITE,335)

def shop_action():
    key=list(SKINS)[max(0,min(shop_index,len(SKINS)-1))]
    skin=SKINS[key]
    if key in save_data["owned"]:
        save_data["skin"]=key; save_game()
    elif player.coins>=skin["price"]:
        player.coins-=skin["price"]; save_data["coins"]=player.coins
        save_data["owned"].append(key); save_data["skin"]=key; save_game()

def draw_shop():
    game.fill((17,17,30)); text_center(game,"SKIN SHOP",FONT_H,GOLD,25)
    text_center(game,"COINS: "+str(player.coins),FONT,WHITE,72)
    for i,key in enumerate(SKINS):
        x=10+i*79; skin=SKINS[key]; selected=key==save_data["skin"]; owned=key in save_data["owned"]
        box=pygame.Rect(x,115,68,105); pygame.draw.rect(game,(180,150,45) if selected else (55,60,80),box); pygame.draw.rect(game,WHITE,box,1)
        pygame.draw.rect(game,skin["body"],(x+25,145,18,35)); pygame.draw.rect(game,skin["helmet"],(x+23,134,22,18))
        text_center_at(skin["name"],FONT_S,WHITE,x+34,188); text_center_at("OWNED" if owned else str(skin["price"]),FONT_S,YELLOW,x+34,207)
    text_center(game,"1-8 SELECT   ENTER BUY/EQUIP",FONT_S,WHITE,260)
    text_center(game,"LEFT/RIGHT BROWSE   ESC BACK",FONT_S,CYAN,282)

def draw_game_over():
    game.fill((25,8,20)); text_center(game,"GAME OVER",FONT_H,RED,90)
    text_center(game,"COINS: "+str(player.coins),FONT_B,GOLD,160)
    text_center(game,"ENTER - RETRY",FONT,WHITE,220); text_center(game,"ESC - MAIN MENU",FONT_S,GRAY,260)

def draw_level_clear():
    game.fill((15,45,30)); text_center(game,"LEVEL CLEAR!",FONT_H,GOLD,80)
    text_center(game,"LEVEL "+str(level),FONT_B,WHITE,150)
    if level==1: text_center(game,"ENTER - CONTINUE TO LEVEL 2",FONT,CYAN,220)
    else:
        text_center(game,"YOU DEFEATED THE BOSS!",FONT,CYAN,220)
        text_center(game,"ENTER - FINISH",FONT,WHITE,255)

def draw_victory():
    game.fill((30,20,65)); text_center(game,"LEGENDARY!",FONT_H,GOLD,70)
    text_center(game,"THE KINGDOM IS SAVED",FONT_B,WHITE,145)
    text_center(game,"TOTAL COINS: "+str(player.coins),FONT,YELLOW,205)
    text_center(game,"ENTER - MAIN MENU",FONT,CYAN,260)

def draw_pause():
    overlay=pygame.Surface((GW,GH),pygame.SRCALPHA); overlay.fill((0,0,0,150)); game.blit(overlay,(0,0))
    text_center(game,"PAUSED",FONT_H,WHITE,100); text_center(game,"P - CONTINUE",FONT,CYAN,175)

player=Player()
generate_level(1)
flag=pygame.Rect(WORLD_WIDTH-200,190,15,130)

running=True
while running:
    jump_pressed=False; attack_pressed=False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if state == MENU:
                if event.key == pygame.K_RETURN:
                    player.lives = 3
                    start_level(1)
                    set_state(PLAYING)
                elif event.key == pygame.K_s:
                    set_state(SHOP)
            elif state == PLAYING:
                if event.key in (pygame.K_SPACE, pygame.K_w, pygame.K_UP):
                    jump_pressed = True
                if event.key in (pygame.K_z, pygame.K_x):
                    attack_pressed = True
                if event.key in (pygame.K_p, pygame.K_ESCAPE):
                    set_state(PAUSED)
            elif state == PAUSED:
                if event.key in (pygame.K_p, pygame.K_ESCAPE):
                    set_state(PLAYING)
                elif event.key == pygame.K_q:
                    set_state(MENU)
            elif state == SHOP:
                if pygame.K_1 <= event.key <= pygame.K_8:
                    shop_index = event.key - pygame.K_1
                elif event.key == pygame.K_LEFT:
                    shop_index = (shop_index - 1) % 8
                elif event.key == pygame.K_RIGHT:
                    shop_index = (shop_index + 1) % 8
                elif event.key == pygame.K_RETURN:
                    # buy item
                    pass
                elif event.key == pygame.K_ESCAPE:
                    set_state(MENU)
            elif state == GAME_OVER:
                if event.key == pygame.K_RETURN:
                    set_state(MENU)
                elif event.key == pygame.K_r:
                    player.lives = 3
                    start_level(1)
                    set_state(PLAYING)
                elif event.key == pygame.K_ESCAPE:
                 set_state(MENU)  
            elif state==GAME_OVER:
                if event.key==pygame.K_RETURN: player.lives=3; start_level(level); set_state(PLAYING)
                elif event.key==pygame.K_ESCAPE: set_state(MENU)
            elif state==LEVEL_CLEAR:
                if event.key==pygame.K_RETURN:
                    if level==1: start_level(2); set_state(PLAYING)
                    else: set_state(VICTORY)
            elif state==VICTORY:
                if event.key==pygame.K_RETURN: set_state(MENU)
        if event.type==pygame.MOUSEBUTTONDOWN:
            mx=int(event.pos[0]*GW/WIDTH); my=int(event.pos[1]*GH/HEIGHT)
            if state==PLAYING:
                if math.hypot(mx-joystick_center[0],my-joystick_center[1])<60: joystick_active=True
                if pygame.Rect(540,270,70,70).collidepoint(mx,my): jump_pressed=True
                if pygame.Rect(450,300,60,60).collidepoint(mx,my): attack_pressed=True
        if event.type==pygame.MOUSEBUTTONUP:
            joystick_active=False; joystick_pos[:]=joystick_center
    if state==PLAYING:
        mouse=pygame.mouse.get_pressed()
        if mouse[0] and joystick_active:
            mx=int(pygame.mouse.get_pos()[0]*GW/WIDTH); my=int(pygame.mouse.get_pos()[1]*GH/HEIGHT)
            dx=mx-joystick_center[0]; dy=my-joystick_center[1]; d=math.hypot(dx,dy)
            if d>38: dx*=38/d; dy*=38/d
            joystick_pos[0]=joystick_center[0]+dx; joystick_pos[1]=joystick_center[1]+dy
            if pygame.Rect(540,270,70,70).collidepoint(mx,my): jump_pressed=True
            if pygame.Rect(450,300,60,60).collidepoint(mx,my): attack_pressed=True
        elif not mouse[0]:
            joystick_active=False; joystick_pos[:]=joystick_center
    if state==PLAYING:
        player.update()
        for enemy in enemies[:]:
            enemy.update()
            if player.attack_timer and player.attack_rect().colliderect(enemy.rect):
                if enemy.damage() and enemy in enemies: enemies.remove(enemy)
        for enemy in enemies[:]:
            if player.rect.colliderect(enemy.rect):
                if player.vy>0 and player.rect.bottom<enemy.rect.top+12 and enemy.kind!="boss":
                    if enemy.damage() and enemy in enemies: enemies.remove(enemy)
                    player.vy=-6
                else: player.hurt()
        for p in projectiles[:]:
            p.update()
            if p.life<=0:
                projectiles.remove(p); continue
            if p.rect.colliderect(player.rect):
                player.hurt()
                if p in projectiles: projectiles.remove(p)
        for c in coins[:]:
            c.update()
            if player.rect.colliderect(c.rect):
                coins.remove(c); player.coins+=1; add_text("+1",c.x,c.y,GOLD); spawn_particles(c.x,c.y,GOLD,6)
        if player.rect.x>WORLD_WIDTH*.5: player.checkpoint=WORLD_WIDTH*.5
        if player.rect.top>450: player.hurt()
        if player.rect.colliderect(flag):
            if level==1: set_state(LEVEL_CLEAR)
            elif not any(e.kind=="boss" for e in enemies): set_state(LEVEL_CLEAR)
        target=player.rect.centerx-GW//2; camera_x+=(target-camera_x)*.12
        camera_x=max(0,min(WORLD_WIDTH-GW,camera_x))
    update_effects()
    if state==MENU: draw_menu()
    elif state==SHOP: draw_shop()
    elif state in (PLAYING,PAUSED):
        draw_background(); draw_level(); draw_flag()
        for c in coins: c.draw()
        for e in enemies: e.draw()
        for p in projectiles: p.draw()
        draw_effects(); player.draw(); draw_effects(); draw_controls()
        if state==PAUSED: draw_pause()
    elif state==GAME_OVER: draw_game_over()
    elif state==LEVEL_CLEAR: draw_level_clear()
    elif state==VICTORY: draw_victory()
    screen.blit(pygame.transform.scale(game,(WIDTH,HEIGHT)),(0,0))
    pygame.display.flip()
    clock.tick(FPS)
save_data["coins"]=player.coins
save_game()
pygame.quit()
