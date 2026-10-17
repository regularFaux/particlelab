"""Particle Lab 0.2: a playful, simplified accelerator construction game."""
import math
import random
import sys
from dataclasses import dataclass
import pygame

pygame.init()
W,H=1180,780
screen=pygame.display.set_mode((W,H))
pygame.display.set_caption('Particle Lab 0.2 | Accelerator Workshop')
clock=pygame.time.Clock()
FONT=pygame.font.SysFont('dejavusans',18)
SMALL=pygame.font.SysFont('dejavusans',14)
TINY=pygame.font.SysFont('dejavusans',12)
BIG=pygame.font.SysFont('dejavusans',27,bold=True)
BG=(12,19,31); PANEL=(24,35,52); TILE=(31,45,62); WHITE=(230,238,248)
MUTED=(153,175,198); CYAN=(82,211,237); GREEN=(107,222,162); GOLD=(255,207,105)
RED=(244,113,124); PURPLE=(178,151,245); BORDER=(70,94,117)
E=1.602176634e-19; C=299792458.; ME=510998.95; MP=938272088.16
GRID=40; OX=40; OY=140; COLS=20; ROWS=12
BOARD=pygame.Rect(OX,OY,COLS*GRID,ROWS*GRID)
SIDEX=870
ITEMS={'gun':(0,'Electron gun'),'vacuum':(1200,'Vacuum pipe'),'accelerator':(2500,'HV gap'),
       'magnet':(3500,'Dipole magnet'),'detector':(2200,'Detector'),'erase':(0,'Remove')}
NOTES=[
('Energy from a voltage','K = |q| Delta V   (for a particle accelerated from rest)'),
('Relativistic energy','E_total = K + mc^2 = gamma mc^2'),
('Momentum','(pc)^2 = K^2 + 2 K mc^2'),
('Magnetic curvature','r = p / (|q| B)   (for motion perpendicular to B)'),
('Lorentz force','dp/dt = q (E + v x B)'),
('Cyclotron frequency','f = |q| B / (2 pi gamma m)  [relativistic]'),
('Cyclotron radius','r = gamma m v / (|q| B) = p / (|q| B)'),
('Beam transmission','N_detected / N_launched; a toy detector has finite aperture'),
]

@dataclass
class Particle:
    x:float; y:float; ux:float; uy:float; k:float; age:float=0.

class Game:
    def __init__(self):
        self.cash=15000; self.mode='linear'; self.tool='gun'; self.rotation=0
        self.components={}; self.particles=[]; self.trails=[]; self.running=False
        self.voltage=25.; self.field=.0002; self.hits=0; self.shots=0; self.cycle_hits=0
        self.cycle_shots=0; self.cycle_k=0.; self.cycle_phi=0.; self.cycle_radius=0.
        self.cycle_revolutions=0.; self.cycle_accumulator=0.; self.timer=0.
        self.notes=False; self.mission=0; self.buttons=[]; self.dragging=None
        self.message='Choose a component, then click the grid to place it. Build left to right.'
        self.place('gun',2,6,0,free=True)
    def place(self,kind,cx,cy,rot=None,free=False):
        if not (0<=cx<COLS and 0<=cy<ROWS): return
        if rot is None:rot=self.rotation
        old=self.components.get((cx,cy))
        if kind=='erase':
            if old:
                self.cash+=ITEMS[old[0]][0]//2; del self.components[(cx,cy)]
                self.message='Component removed; 50% salvage recovered.'
            return
        if old and old[0]==kind and old[1]==rot:return
        price=ITEMS[kind][0]
        if self.cash<price:
            self.message='Not enough research funding.';return
        if old:self.cash+=ITEMS[old[0]][0]//2
        self.cash-=price;self.components[(cx,cy)]=(kind,rot)
        self.message=f'{ITEMS[kind][1]} placed. Press R to rotate the next component.'
    def button(self,label,rect,callback,active=True,selected=False):
        rect=pygame.Rect(rect);pygame.draw.rect(screen,(42,83,105) if selected else (41,57,75) if active else (38,45,55),rect,border_radius=6)
        pygame.draw.rect(screen,CYAN if selected else BORDER,rect,2 if selected else 1,border_radius=6)
        t=SMALL.render(label,True,WHITE if active else MUTED);screen.blit(t,t.get_rect(center=rect.center))
        self.buttons.append((rect,callback,active))
    def text(self,s,x,y,color=WHITE,font=FONT):screen.blit(font.render(str(s),True,color),(x,y))
    def toggle(self):
        if self.mode=='linear':
            if not any(k=='gun' for k,r in self.components.values()) or not any(k=='detector' for k,r in self.components.values()):
                self.message='Place an electron gun and detector first.';return
        else:
            if self.cash<0:return
        self.running=not self.running
        self.message='Experiment running.' if self.running else 'Experiment paused.'
    def switch(self,mode):
        self.running=False;self.particles.clear();self.mode=mode
        self.field=.0002 if mode=='linear' else .2
        self.message=('Build a beamline: gun -> HV gaps -> magnet -> detector.' if mode=='linear' else
                      'Cyclotron: tune B and gap voltage; particles spiral outward as energy rises.')
    def adjust_field(self,direction):
        step=.00005 if self.mode=='linear' else .05
        minimum=0. if self.mode=='linear' else .05
        maximum=.002 if self.mode=='linear' else 2.
        self.field=max(minimum,min(maximum,round(self.field+direction*step,7)))
    def grant(self):
        if self.mission==0 and self.hits>=10:
            self.mission=1;self.cash+=6000;self.running=False
            self.message='GRANT AWARDED: 10 detected electrons! +$6,000.'
        if self.mission==1 and self.hits>=100:
            self.mission=2;self.cash+=12000;self.running=False
            self.message='GRANT AWARDED: 100 detected electrons! +$12,000. Try the cyclotron.'
        if self.mission==2 and self.cycle_hits>=10:
            self.mission=3;self.cash+=18000;self.running=False
            self.message='GRANT AWARDED: 10 cyclotron extractions! +$18,000.'
    def physics(self,dt):
        if not self.running:return
        if self.mode=='linear':self.linear_step(dt)
        else:self.cyclotron_step(dt)
        self.grant()
    def linear_step(self,dt):
        self.timer+=dt
        while self.timer>=.085:
            self.timer-=.085
            for (cx,cy),(kind,rot) in self.components.items():
                if kind=='gun':
                    a=rot*math.pi/2+random.gauss(0,.008)
                    self.particles.append(Particle(OX+(cx+.5)*GRID,OY+(cy+.5)*GRID,math.cos(a),math.sin(a),1000.))
                    self.shots+=1
        out=[]
        for p in self.particles:
            p.age+=dt
            # A fixed visual speed is used; curvature and energy use relativistic momentum.
            dist=dt*255; steps=max(1,math.ceil(dist/4));step=dist/steps
            alive=True
            for _ in range(steps):
                cx=int((p.x-OX)//GRID);cy=int((p.y-OY)//GRID)
                if not (0<=cx<COLS and 0<=cy<ROWS):alive=False;break
                comp=self.components.get((cx,cy))
                if comp:
                    kind,rot=comp
                    if kind=='accelerator':
                        # Energy gain applied once per traversal, not on every numerical substep.
                        key=(cx,cy)
                        if getattr(p,'last_gap',None)!=key:
                            p.k+=self.voltage*1000; p.last_gap=key
                    elif kind=='magnet':
                        pc=math.sqrt(p.k*p.k+2*p.k*ME)
                        radius=pc/(C*self.field)/.002 if self.field>0 else 1e20
                        # Electron bends clockwise in screen coordinates for B out of screen.
                        angle=step/radius
                        co,si=math.cos(angle),math.sin(angle)
                        p.ux,p.uy=p.ux*co-p.uy*si,p.ux*si+p.uy*co
                    elif kind=='detector':
                        self.hits+=1;alive=False;break
                if not comp or comp[0]!='accelerator':p.last_gap=None
                p.x+=p.ux*step;p.y+=p.uy*step
            if alive and p.age<9:out.append(p)
        self.particles=out[-300:]
    def cyclotron_step(self,dt):
        # Toy orbit: proton receives |q|V per gap crossing; relativistic f and radius.
        # A physical orbit takes microseconds; playback is slowed for visibility.
        if self.cycle_k==0:self.cycle_k=1000.;self.cycle_phi=0.;self.cycle_revolutions=0.;self.cycle_shots+=1
        k=self.cycle_k;gamma=1+k/MP
        pc=math.sqrt(k*k+2*k*MP) # eV
        r=pc*E/C/(E*max(self.field,.001)) # meters
        self.cycle_radius=r
        angular=2*math.pi*1.1/(gamma) # display radians/s, not physical frequency
        previous=self.cycle_phi;self.cycle_phi+=angular*dt
        old_cross=math.floor(previous/math.pi);new_cross=math.floor(self.cycle_phi/math.pi)
        crossings=max(0,new_cross-old_cross)
        if crossings:
            self.cycle_k+=crossings*self.voltage*1000.
            self.cycle_revolutions=self.cycle_phi/(2*math.pi)
        # Extraction at 0.5 m orbit radius. Smaller B and higher V help reach it.
        if self.cycle_radius>=.5:
            self.cycle_hits+=1;self.cycle_k=0.;self.cycle_phi=0.
    def icon(self,kind,x,y,rot=0,scale=1):
        s=GRID*scale;center=(int(x),int(y))
        if kind=='gun':
            pygame.draw.rect(screen,(78,113,135),(x-s*.36,y-s*.22,s*.56,s*.44),border_radius=4)
            pygame.draw.polygon(screen,CYAN,[(x+s*.04,y-s*.18),(x+s*.39,y),(x+s*.04,y+s*.18)])
            pygame.draw.circle(screen,GOLD,(int(x-s*.22),int(y)),4)
        elif kind=='vacuum':
            pygame.draw.rect(screen,(82,122,141),(x-s*.45,y-s*.2,s*.9,s*.4),border_radius=7)
            pygame.draw.rect(screen,(15,32,45),(x-s*.37,y-s*.1,s*.74,s*.2),border_radius=4)
        elif kind=='accelerator':
            for dx in (-.24,.24):pygame.draw.rect(screen,GOLD,(x+s*dx-3,y-s*.35,6,s*.7),border_radius=2)
            pygame.draw.line(screen,CYAN,(x-s*.12,y),(x+s*.12,y),3)
        elif kind=='magnet':
            pygame.draw.arc(screen,RED,(x-s*.37,y-s*.39,s*.74,s*.78),.15,3.0,7)
            pygame.draw.circle(screen,CYAN,center,5,1)
            pygame.draw.circle(screen,CYAN,center,2)
        elif kind=='detector':
            pygame.draw.rect(screen,GREEN,(x-s*.12,y-s*.4,s*.24,s*.8),border_radius=3)
            for j in range(3):pygame.draw.line(screen,(26,78,66),(x-s*.1,y+s*(-.2+j*.2)),(x+s*.1,y+s*(-.2+j*.2)),2)
        if kind in ('gun','vacuum','accelerator','detector') and rot:
            # Small direction indicator makes rotated components identifiable.
            a=rot*math.pi/2
            pygame.draw.line(screen,GOLD,center,(x+math.cos(a)*s*.46,y+math.sin(a)*s*.46),2)
    def draw_board(self):
        pygame.draw.rect(screen,PANEL,BOARD,border_radius=7)
        for i in range(COLS+1):pygame.draw.line(screen,(38,54,72),(OX+i*GRID,OY),(OX+i*GRID,OY+ROWS*GRID))
        for j in range(ROWS+1):pygame.draw.line(screen,(38,54,72),(OX,OY+j*GRID),(OX+COLS*GRID,OY+j*GRID))
        for (cx,cy),(kind,rot) in self.components.items():
            x=OX+(cx+.5)*GRID;y=OY+(cy+.5)*GRID
            pygame.draw.rect(screen,TILE,(OX+cx*GRID+2,OY+cy*GRID+2,GRID-4,GRID-4),border_radius=4)
            self.icon(kind,x,y,rot)
        for p in self.particles:pygame.draw.circle(screen,GOLD,(int(p.x),int(p.y)),3)
        mx,my=pygame.mouse.get_pos()
        if BOARD.collidepoint((mx,my)) and self.mode=='linear' and not self.notes:
            cx=int((mx-OX)//GRID);cy=int((my-OY)//GRID)
            pygame.draw.rect(screen,CYAN,(OX+cx*GRID,OY+cy*GRID,GRID,GRID),2)
        self.text('CONSTRUCTION GRID  |  Click to place  |  R rotate  |  Right-click remove',OX,113,MUTED,SMALL)
    def draw_cyclotron(self):
        cx=OX+COLS*GRID//2;cy=OY+ROWS*GRID//2
        pygame.draw.rect(screen,PANEL,BOARD,border_radius=8)
        for radius in (70,135,205):pygame.draw.circle(screen,(55,75,95),(cx,cy),radius,1)
        pygame.draw.circle(screen,(44,67,91),(cx,cy),213,4)
        pygame.draw.circle(screen,(31,52,75),(cx,cy),202)
        pygame.draw.rect(screen,(13,19,31),(cx-5,cy-205,10,410))
        pygame.draw.line(screen,GOLD,(cx-200,cy),(cx+200,cy),2)
        self.text('DEE A',cx-145,cy-18,CYAN,SMALL);self.text('DEE B',cx+85,cy-18,CYAN,SMALL)
        pygame.draw.circle(screen,GREEN,(cx+205,cy),9,2)
        self.text('EXTRACTION',cx+220,cy-11,GREEN,SMALL)
        if self.cycle_k:
            r=min(200,self.cycle_radius/.5*200)
            x=cx+math.cos(self.cycle_phi)*r;y=cy+math.sin(self.cycle_phi)*r
            pygame.draw.circle(screen,GOLD,(int(x),int(y)),6)
        self.text('Protons gain energy crossing the RF gap; B bends their orbits.',OX+14,OY+12,MUTED,SMALL)
        self.text('Simplified cyclotron: ideal gap synchronization, no beam losses.',OX+14,OY+34,MUTED,SMALL)
    def draw_notes(self):
        pygame.draw.rect(screen,(17,28,44),(115,115,950,550),border_radius=12)
        pygame.draw.rect(screen,CYAN,(115,115,950,550),2,border_radius=12)
        self.text('LAB NOTEBOOK  |  Physics equations',145,139,CYAN,BIG)
        self.text('Idealized models; SI units unless indicated. K and mc^2 use eV.',145,179,MUTED,SMALL)
        for i,(name,eq) in enumerate(NOTES):
            y=215+i*49
            self.text(name,146,y,GOLD,SMALL);self.text(eq,146,y+19,WHITE,SMALL)
        self.button('CLOSE NOTES',(877,610,153,36),lambda:setattr(self,'notes',False))
    def draw(self):
        screen.fill(BG);self.buttons=[]
        self.text('PARTICLE LAB',40,20,CYAN,BIG)
        self.text('Accelerator Workshop / v0.2',40,57,MUTED,SMALL)
        self.text(f'RESEARCH FUNDING  ${self.cash:,}',830,24,GREEN)
        self.button('LINEAR',(40,78,108,31),lambda:self.switch('linear'),selected=self.mode=='linear')
        self.button('CYCLOTRON',(158,78,120,31),lambda:self.switch('cyclotron'),selected=self.mode=='cyclotron')
        self.button('NOTEBOOK  [N]',(687,78,152,31),lambda:setattr(self,'notes',not self.notes))
        if self.mode=='linear':self.draw_board()
        else:self.draw_cyclotron()
        self.text('WORKSHOP',SIDEX,112,CYAN,SMALL)
        if self.mode=='linear':
            for i,(kind,(cost,label)) in enumerate(ITEMS.items()):
                y=143+i*49
                self.button(f'{label}  ${cost:,}' if cost else label,(SIDEX,y,270,39),lambda k=kind:setattr(self,'tool',k),selected=self.tool==kind)
            self.text(f'Selected: {self.tool}  |  Facing: {self.rotation*90} deg',SIDEX,447,MUTED,SMALL)
        else:
            self.text('RF acceleration + uniform B',SIDEX,156,MUTED,SMALL)
            self.text('Cyclotron extraction at r = 0.50 m',SIDEX,187,MUTED,SMALL)
            self.text(f'Kinetic energy: {self.cycle_k/1000:.1f} keV',SIDEX,225,GOLD,SMALL)
            self.text(f'Orbit radius: {self.cycle_radius:.3f} m',SIDEX,253,WHITE,SMALL)
            self.text(f'Extracted protons: {self.cycle_hits}',SIDEX,283,GREEN,SMALL)
        self.text('EXPERIMENT CONTROLS',40,644,CYAN,SMALL)
        self.button('Voltage -5 kV',(40,673,140,37),lambda:setattr(self,'voltage',max(5,self.voltage-5)))
        self.button('Voltage +5 kV',(190,673,140,37),lambda:setattr(self,'voltage',min(200,self.voltage+5)))
        self.button('B -' + ('0.05 mT' if self.mode=='linear' else '0.05 T'),(344,673,120,37),lambda:self.adjust_field(-1))
        self.button('B +' + ('0.05 mT' if self.mode=='linear' else '0.05 T'),(473,673,120,37),lambda:self.adjust_field(1))
        self.button('STOP' if self.running else 'RUN EXPERIMENT',(609,673,198,37),self.toggle)
        self.button('CLEAR PARTICLES',(820,673,160,37),lambda:self.particles.clear())
        self.text(f'Voltage: {self.voltage:.0f} kV / gap     Field: {self.field*1000:.2f} mT' if self.mode=='linear' else f'Voltage: {self.voltage:.0f} kV / gap     Field: {self.field:.2f} T',40,724,WHITE,SMALL)
        self.text(f'Linear detections: {self.hits} / {self.shots} launched',420,724,GREEN,SMALL)
        self.text('Milestones: 10 e- / 100 e- / 10 cyclotron protons',40,749,MUTED,TINY)
        self.text(self.message[:80],40,613,GOLD,SMALL)
        if self.notes:self.draw_notes()
    def click(self,pos,button):
        if self.notes:
            if button==1:
                for rect,action,enabled in reversed(self.buttons):
                    if rect.collidepoint(pos) and enabled and rect.y>=600:action();return
            return
        if button==3 and self.mode=='linear' and BOARD.collidepoint(pos):
            self.place('erase',int((pos[0]-OX)//GRID),int((pos[1]-OY)//GRID));return
        if button!=1:return
        for rect,action,enabled in reversed(self.buttons):
            if rect.collidepoint(pos) and enabled:action();return
        if self.mode=='linear' and BOARD.collidepoint(pos):
            self.place(self.tool,int((pos[0]-OX)//GRID),int((pos[1]-OY)//GRID))

def main():
    g=Game()
    while True:
        dt=min(clock.tick(60)/1000,.05)
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT:pygame.quit();sys.exit()
            if ev.type==pygame.MOUSEBUTTONDOWN:g.click(ev.pos,ev.button)
            if ev.type==pygame.KEYDOWN:
                if ev.key==pygame.K_n:g.notes=not g.notes
                elif ev.key==pygame.K_ESCAPE:g.notes=False
                elif ev.key==pygame.K_r and not g.notes:g.rotation=(g.rotation+1)%4
                elif ev.key==pygame.K_SPACE and not g.notes:g.toggle()
        g.physics(dt);g.draw();pygame.display.flip()
if __name__=='__main__':main()
