import pygame, json
from pygame.transform import flip, rotate
from pygame_helper.helper_sprites import AnimatedSprite
from pygame_helper.helper_graphics import load_image, scale_image, draw_image
from settings import BLOCK_SIZE, GRAPHICS_PATH, GRAVITY_CONSTANT, HEIGHT, ITEM_SIZE, SCROLL_LINE_X, SCROLL_LINE_Y, WIDTH, SAFE_BLOCKS_NUM,WALK_COOLDOWN
from inventory import Inventory
from hotbar import Hotbar
from pygame_helper.pygame_helper import debug
from item import ItemInstance
from stats import Statistics

class Player(AnimatedSprite):
    def __init__(self,start_pos,scrollx,scrolly, assets, add_drop,trigger_death, id):
        AnimatedSprite.__init__(self)

        self.height = BLOCK_SIZE*2 * 0.9
        self.width = BLOCK_SIZE/2
        self.scroll_x = scrollx
        self.scroll_y = scrolly
        self.is_dead = False

        #self.right_image = load_image(GRAPHICS_PATH+"player/stand/stand_right.png",True)
        #self.right_image = scale_image(self.right_image,None,self.width,self.height)
        #self.left_image = flip(self.right_image,True,False)
        #self.image = self.right_image
        #self.rect = self.image.get_rect(midbottom=start_pos)
        scale = 0.8
        self.head_img_l = scale_image(load_image(f"{GRAPHICS_PATH}player/male/head.png"),scale) 
        self.head_img_r = flip(self.head_img_l,True,False)
        self.head_img = self.head_img_r
        self.body_img = scale_image(load_image(f"{GRAPHICS_PATH}player/male/body.png"),scale)
        self.original_arm_img = scale_image(load_image(f"{GRAPHICS_PATH}player/male/arm.png",True),scale)
        self.original_leg_img = scale_image(load_image(f"{GRAPHICS_PATH}player/male/leg.png",True),scale)
        self.left_arm_img = self.original_arm_img
        self.right_arm_img = self.original_arm_img
        self.left_leg_img = self.original_leg_img
        self.right_leg_img = self.original_leg_img

        self.rect = self.body_img.get_rect(center=start_pos)
        self.head_rect = self.head_img_l.get_rect(midbottom=self.rect.midtop)
        self.left_arm_rect = self.left_arm_img.get_rect(midtop=self.rect.midtop)
        self.right_arm_rect = self.right_arm_img.get_rect(midtop=self.rect.midtop)
        self.left_leg_rect = self.left_leg_img.get_rect(midbottom=self.rect.midbottom)
        self.right_leg_rect = self.right_leg_img.get_rect(midbottom=self.rect.midbottom)

        self.right_angle = 0
        self.left_angle = 0
        self.go_right = 1
        self.go_left = -1

        self.inf_height = self.original_leg_img.get_height()

        self.arm_direction = pygame.Vector2((0,0))
        self.leg_direction = pygame.Vector2((0,0))

        self.sel_item_rect = pygame.Rect(0,0,ITEM_SIZE,ITEM_SIZE)

        self.gravity = 0
        self.jump_speed = 10

        self.x_speed = 8
        self.direction = 1

        self.can_jump = False
        self.is_standing = False
        self.is_moving = False
        self.can_move_d = True
        self.can_move_a = True
        self.can_press = True

        self.selected_item = None

        self.assets = assets
        self.add_drop = add_drop

        self.inventory_open = False
        self.inventory = Inventory(self.add_drop,self.return_data)
        self.give_starter_items()
        self.can_open_inventory = True
        self.hotbar = Hotbar(self.inventory.columns,self.inventory.get_first_line,self.change_selected_item)
        self.statistics = Statistics(self.hotbar.offset[1],self.hotbar.offset[0],self.hotbar.lenght,trigger_death)

        self.first_time_land = False
        self.pixel_fell = 0

        self.v = 3
        self.started_moving = False

    def save_data(self,id):
        try:
            with open("data/worlds_data/"+id+"/player_data.json","w") as p_file:
                data = {"pos":self.rect.center,"gravity":self.gravity,"pixel_fell":self.pixel_fell,"health":self.statistics.player_health,"hunger":self.statistics.player_hunger,"dir":self.direction,"index":self.hotbar.selection_index}
                json.dump(data,p_file)
            self.inventory.save_data(id)
            self.selected_item = None
        except:
            pass

    def load_data(self,id):
        #try:
            p_file = open("data/worlds_data/"+id+"/player_data.json","r")
            data = json.load(p_file)
            self.rect.center = data["pos"]
            self.gravity = data["gravity"]
            self.pixel_fell = data["pixel_fell"]
            self.statistics.player_health = data["health"]
            self.statistics.player_hunger = data["hunger"]
            self.direction = data["dir"]
            self.flip_image()
            self.inventory.load_data(id)
            self.hotbar.selection_index = data["index"]
            if self.hotbar.get_selected().empty == False:
                self.selected_item = self.hotbar.get_selected().item.__copy__()
            self.flip_image(False)
            if self.selected_item:
                if self.direction == -1:
                    self.selected_item.image = pygame.transform.flip(self.selected_item.image,True,False)
            p_file.close()

    def reset(self):
        self.can_move_a = True
        self.can_move_d = True
        self.can_jump = False
        self.can_open_inventory = True
        self.gravity = 0
        self.is_standing = False
        self.pixel_fell = 0
        self.first_time_land = True
        self.change_selected_item(None)
        self.inventory_open = False
        self.is_dead = False

    def get_rect(self):
        return self.rect.inflate(0,self.inf_height*2)

    def return_data(self):
        return [self.rect.midtop,self.direction]

    def change_selected_item(self,item):
        self.selected_item = item
        if self.selected_item:
            if self.direction == -1:
                self.selected_item.image = pygame.transform.flip(self.selected_item.image,True,False)

    def give_starter_items(self):
        self.inventory.add_item(self.inventory.get_empty_slot_pos(),ItemInstance(0,"tools",False),1)
        self.inventory.add_item(self.inventory.get_empty_slot_pos(),ItemInstance(1,"tools",False),1)
        self.inventory.add_item(self.inventory.get_empty_slot_pos(),ItemInstance(2,"tools",False),1)
        self.inventory.add_item(self.inventory.get_empty_slot_pos(),ItemInstance(3,"tools",False),1)
    
    def walk_animation(self):
        if self.is_moving:
            
            if self.right_angle > 0:
                self.arm_direction.x = 1
                self.leg_direction.x = 1
            else:
                self.arm_direction.x = -1
                self.leg_direction.x = -1
            self.arm_direction.y = self.arm_direction.x *-1
            self.leg_direction.y = self.leg_direction.x *-1

            if self.go_right == 1:
                if self.right_angle > 45:
                    self.go_right = -1
            elif self.go_right == -1:
                if self.right_angle < -45:
                    self.go_right = 1

            self.go_left = self.go_right *-1
            
            self.left_arm_img = rotate(self.original_arm_img,self.left_angle)
            self.right_arm_img = rotate(self.original_arm_img,self.right_angle)
            self.left_leg_img = rotate(self.original_leg_img,self.left_angle)
            self.right_leg_img = rotate(self.original_leg_img,self.right_angle)

            self.right_angle += self.v*self.go_right
            self.left_angle += self.v*self.go_left

    def custom_draw(self):
        self.walk_animation()

        self.head_rect.midbottom = self.rect.midtop
        match self.arm_direction.x:
            case 1:
                self.right_arm_rect = self.right_arm_img.get_rect(topleft=self.rect.midtop)
            case -1:
                self.right_arm_rect = self.right_arm_img.get_rect(topright=self.rect.midtop)
            case 0:
                self.right_arm_rect = self.right_arm_img.get_rect(midtop=self.rect.midtop)
        match self.arm_direction.y:
            case 1:
                self.left_arm_rect = self.left_arm_img.get_rect(topleft=self.rect.midtop)
            case -1:
                self.left_arm_rect = self.left_arm_img.get_rect(topright=self.rect.midtop)
            case 0:
                self.left_arm_rect = self.left_arm_img.get_rect(midtop=self.rect.midtop)

        match self.leg_direction.x:
            case 1:
                self.right_leg_rect = self.right_leg_img.get_rect(topleft=self.rect.midbottom)
            case -1:
                self.right_leg_rect = self.right_leg_img.get_rect(topright=self.rect.midbottom)
            case 0:
                self.right_leg_rect = self.right_leg_img.get_rect(midtop=self.rect.midbottom)
        match self.leg_direction.y:
            case 1:
                self.left_leg_rect = self.left_leg_img.get_rect(topleft=self.rect.midbottom)
            case -1:
                self.left_leg_rect = self.left_leg_img.get_rect(topright=self.rect.midbottom)
            case 0:
                self.left_leg_rect = self.left_leg_img.get_rect(midtop=self.rect.midbottom)

        if self.direction == 1:
            draw_image(self.left_arm_img,self.left_arm_rect)
            draw_image(self.left_leg_img,self.left_leg_rect)
        else:
            draw_image(self.right_arm_img,self.right_arm_rect)
            draw_image(self.right_leg_img,self.right_leg_rect)
            self.draw_selected_item()
        draw_image(self.head_img,self.head_rect)
        draw_image(self.body_img,self.rect)
        if self.direction ==1:
            draw_image(self.right_arm_img,self.right_arm_rect)
            draw_image(self.right_leg_img,self.right_leg_rect)
            self.draw_selected_item()
        else:
            draw_image(self.left_arm_img,self.left_arm_rect)
            draw_image(self.left_leg_img,self.left_leg_rect)

    def flip_image(self,do=True):
        if self.direction == 1:
            self.head_img = self.head_img_r
        else:
            self.head_img = self.head_img_l
        if do:
            if self.selected_item:
                self.selected_item.image = pygame.transform.flip(self.selected_item.image,True,False)

    def fall(self,dt):
        if not self.is_standing:
            self.gravity += GRAVITY_CONSTANT
            if self.gravity < 0:
                if self.rect.top < SCROLL_LINE_Y:
                    self.scroll_y(dt)
                    self.rect.top = SCROLL_LINE_Y
            if self.rect.bottom <= HEIGHT-SCROLL_LINE_Y or self.gravity < 0:
                self.rect.y += self.gravity*dt
                if self.gravity > 0:
                    self.pixel_fell += self.gravity*dt
            else:
                if self.gravity > 0:
                    self.scroll_y(dt)
                    self.pixel_fell += self.gravity*dt
            self.can_jump = False

    def drop_item(self):
        if self.hotbar.get_selected().empty == False:
            pos = (self.rect.midtop[0]+BLOCK_SIZE*self.direction,self.rect.midtop[1])
            self.add_drop(pos,self.hotbar.get_selected().item,self.hotbar.get_selected().quantity)
            self.hotbar.slots[self.hotbar.get_s_pos()].empty = True
            self.hotbar.slots[self.hotbar.get_s_pos()].item = None
            self.hotbar.slots[self.hotbar.get_s_pos()].quantity = 1
            self.selected_item = None

    def input(self,dt):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_d]:
            if self.can_move_d:
                self.can_move_a = True
                if self.direction != 1:
                    self.direction = 1
                    self.flip_image()
                if not self.started_moving:
                    self.arm_direction = pygame.Vector2((1,-1))
                    self.leg_direction = pygame.Vector2((1,-1))
                    self.go_right = 1
                    self.go_left = -1
                    self.started_moving = True
                if self.rect.right < WIDTH-SCROLL_LINE_X:
                    self.move(dt)
                else:
                    self.scroll_x(dt)
                    self.rect.right = WIDTH-SCROLL_LINE_X
                    self.is_moving = True
            else:
                if self.is_moving:
                    self.is_moving = False
                    self.stop_player()

        if keys[pygame.K_a]:
            if self.can_move_a:
                self.can_move_d = True
                if self.direction != -1:
                    self.direction = -1
                    self.flip_image()
                if not self.started_moving:
                    self.arm_direction = pygame.Vector2((-1,1))
                    self.leg_direction = pygame.Vector2((-1,1))
                    self.go_right = -1
                    self.go_left = 1
                    self.started_moving = True
                if self.rect.left > SCROLL_LINE_X:
                    self.move(dt)
                else:
                    self.scroll_x(dt)
                    self.rect.left = SCROLL_LINE_X
                    self.is_moving = True
            else:
                if self.is_moving:
                    self.is_moving = False
                    self.stop_player()

        if keys[pygame.K_q] and self.can_press:
            self.can_press = False
            self.drop_item()

        if not keys[pygame.K_q]:
            self.can_press = True

        if (not keys[pygame.K_a]) and (not keys[pygame.K_d]):
            if self.is_moving:
                self.is_moving = False
                self.stop_player()

        if keys[pygame.K_SPACE] and self.can_jump:
            self.jump()

        if keys[pygame.K_e] and self.can_open_inventory:
            self.inventory_open = not self.inventory_open
            self.can_open_inventory = False
        if not keys[pygame.K_e]:
            self.can_open_inventory = True

    def stop_player(self):
        self.arm_direction = pygame.Vector2((0,0))
        self.leg_direction = pygame.Vector2((0,0))
        self.left_arm_img = self.original_arm_img
        self.right_arm_img = self.original_arm_img
        self.left_leg_img = self.original_leg_img
        self.right_leg_img = self.original_leg_img
        self.left_angle = 0
        self.right_angle = 0
        self.started_moving = False

    def drop_collision(self,drop):
        if self.rect.inflate(0,self.inf_height).colliderect(drop.rect):
            if self.inventory.get_free_pos_by_id(drop.item.id,drop.item.type):
                self.inventory.add_item(self.inventory.get_free_pos_by_id(drop.item.id,drop.item.type),drop.item,drop.quantity)
                return True
        return False

    def obstacles_collisions(self,obstacles):
        not_collided = 0
        near_blocks = 0
        not_call_r = 0
        not_call_l = 0
        
        if self.gravity != 0:
            if self.is_standing != False:
                self.is_standing = False
                self.can_jump = False
        if obstacles:
            for obstacle in obstacles:
                obs = obstacle[0]
                r = self.rect.inflate(0,self.inf_height*2)
                inf_y = r.inflate(-self.width+10,2)
                inf_x = r.inflate(2,-self.height/3)
                if abs(obs.x-self.rect.x) <= BLOCK_SIZE*4 and abs(obs.y-self.rect.y) <= BLOCK_SIZE*4:
                    near_blocks += 1
                    if r.colliderect(obs):
                        if self.gravity >= 0:
                            if r.bottom > obs.top:
                                if (r.bottom < obs.centery) or (self.rect.left > obs.left and self.rect.right < obs.right):
                                    if self.rect.left < obs.right -5 or self.rect.right > obs.left + 5:
                                        self.rect.bottom = obs.top-self.inf_height
                                        self.is_standing = True
                                        self.gravity = 0
                                        self.can_jump = True
                                        if self.first_time_land:
                                            self.first_time_land = False
                                            blocks_fell = ((self.pixel_fell)/BLOCK_SIZE)-SAFE_BLOCKS_NUM
                                            if int(blocks_fell) > 0:
                                                self.statistics.damage_player(int(blocks_fell))
                                            self.pixel_fell = 0
                        elif self.gravity < 0:
                            if r.top < obs.bottom and r.top > obs.centery+15:
                                self.rect.top = obs.bottom+self.inf_height
                                self.is_standing = False
                                self.gravity = 0
                        #if self.is_moving:
                        if self.direction == 1:
                            if 0 < (obs.left+15)-(self.rect.right-15) < BLOCK_SIZE//2:
                                if self.rect.right > obs.left:
                                    self.can_move_d = False
                                    self.rect.right = obs.left
                                    if self.gravity < 0 and r.bottom < obs.centery:
                                        self.rect.bottom = obs.top-self.inf_height
                        elif self.direction == -1:
                            if 0 < (self.rect.left+15)-(obs.right-15)< BLOCK_SIZE//2 :
                                if self.rect.left < obs.right:
                                    self.can_move_a = False
                                    self.rect.left = obs.right
                                    if self.gravity < 0 and r.bottom < obs.centery:
                                        self.rect.bottom = obs.top-self.inf_height
                    else: 
                        if not inf_y.colliderect(obs):
                            not_collided += 1
                        if not inf_x.colliderect(obs):
                            if self.direction == 1:
                                not_call_r += 1
                            elif self.direction == -1:
                                not_call_l += 1

        if not_collided == near_blocks:
            self.is_standing = False
            self.first_time_land = True
        if not_call_l == near_blocks:
            self.can_move_a = True
        if not_call_r == near_blocks:
            self.can_move_d = True
                    
    def move(self,dt):
        self.rect.x += self.x_speed*self.direction*dt
        self.is_moving = True

    def jump(self):
        self.gravity-=self.jump_speed
        self.can_jump = False

    def draw_selected_item(self):
        if self.selected_item:
            if self.direction == 1:
                if self.arm_direction.x == 1:
                    self.sel_item_rect.bottomleft = (self.right_arm_rect.right-5,self.right_arm_rect.bottom-5)
                else:
                    self.sel_item_rect.bottomleft = (self.right_arm_rect.left+5,self.right_arm_rect.bottom-5)
            else:
                if self.arm_direction.x == -1:
                    self.sel_item_rect.bottomright = (self.right_arm_rect.left+5,self.right_arm_rect.bottom-5)
                else:
                    self.sel_item_rect.bottomright = (self.right_arm_rect.right-5,self.right_arm_rect.bottom-5)
            draw_image(self.selected_item.image,self.sel_item_rect)

    def update(self,obstacles,dt,mouse):
        
        if not self.is_dead:
            self.fall(dt)
            self.input(dt)
            self.statistics.update()
        self.obstacles_collisions(obstacles)
        self.hotbar.render_slots()
        self.statistics.draw()
        

        if self.inventory_open and not self.is_dead:
            self.inventory.render_slots()
            self.inventory.update(mouse)
        else:
            if not self.is_dead:
                self.hotbar.update(mouse)