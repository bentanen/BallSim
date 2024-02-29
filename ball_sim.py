
# Python imports
import random
from typing import List

# Library imports
import pygame
from pygame import mixer
import math
import colorsys

# pymunk imports
import pymunk
import pymunk.pygame_util
from pymunk.pygame_util import DrawOptions


#TODO: create ball subclass to store individual ball info

class BouncyBalls(object):
    #Ball subclass
    class Balls:
        from queue import Queue

        radius = 0
        color = (0,0,0)
        collision_Type = 0
        mass = 0
        shape = pymunk.Circle
        inertia = 0
        elasticity = 0
        friction = 0
        body = pymunk.Body

        maxSize=600
        prevLocations = Queue(maxSize)
        prevColors = Queue(maxSize)
        #queue.prevLocations(10)
        
        def getCenter(self):
            p = self.body.position
            p = pymunk.Vec2d(p.x,p.y)
            return (round(p.x), round(p.y))


        def __init__(self, myMass,  myRadius, myColor, myElasticity, myFriction,myCollisionType):
                self.mass = myMass
                self.radius = myRadius
                offset =  [0,0]
                self.inertia = pymunk.moment_for_circle(myMass,0,myRadius,offset)
                self.body = pymunk.Body(myMass, self.inertia)
                self.collision_type = self.body.collision_type =myCollisionType

                self.shape = pymunk.Circle(self.body, self.radius, (0, 0))
                self.shape.elasticity = myElasticity
                self.shape.friction = myFriction

                self.color = pygame.Color(myColor)

                self.shape.collision_type = self.collision_Type
                self.shape.color = self.color

        
            #rectangles that exist in the world
    _rectangles: List[pymunk.Poly] = []

    collision_types = {
    "ball": 1,
    "wall":2,
    "death-ball":3,
    }
    
    x_pixel=720
    y_pixel = 1280

    num_balls=0
    max_balls = 8
    boundary_info = {
        "x_offset": x_pixel/2,
        "y_offset": y_pixel/2,
        "radius": x_pixel/2.5,
        "line_weight": 3,
    }

    ball_color_R = 255
    ball_color_G = 250
    ball_color_B = 228
    radius = 0

    """
    This class implements a simple scene in which there is a static platform (made up of a couple of lines)
    that don't move. Balls appear occasionally and drop onto the platform. They bounce around.
    """
    color = [255,255,255]

    FPS = 120


    def get_FPS(self):
        return self.FPS
    
    def set_color(self, val):
        self.color = val
        
    def get_background(self):
        return self.color
    
    newBalls =[]
    deathBalls = []
    def __init__(self) -> None:
        # Space
        self._space = pymunk.Space()
        self._space.gravity = (0.0, 900.0)


        # Physics
        # Time step -> 10x slower than the frame rate
        self._dt = 1.0 / self.get_FPS()/2000
        # Number of physics steps per screen frame
        self._physics_steps_per_frame = 1000

        # pygame
        pygame.init()
        mixer.init(buffer=512)
        #set number of channels above default(8) so more than 8 sounds can be played at once
        max_num_sound_channels = 100
        pygame.mixer.set_num_channels(max_num_sound_channels)
        

        self._screen = pygame.display.set_mode((self.x_pixel, self.y_pixel))
        self._surface = pygame.Surface((self.x_pixel, self.y_pixel),pygame.SRCALPHA)


        self.color=[0,0,0]

        self._clock = pygame.time.Clock()

        self._draw_options = pymunk.pygame_util.DrawOptions(self._screen)

        # Static barrier walls (lines) that the balls bounce off of
        self._add_static_scenery()

        # Balls that exist in the world
       # self._balls = []
        #rectangles that exist in the world
        #self._rectangles: List[pymunk.Poly] = []

        # Execution control and time until the next ball spawns
        self._running = True

        #generate balls to start
        numBalls = 3
        for i in range(numBalls):
            self.newBalls.append(self._create_ball())
        #self._balls = [self.Balls() for i in range(numBalls)]
            
        #create death ball
        self._create_death()


    def run(self) -> None:
        """
        The main loop of the game.
        :return: None
        """
        # Main loop
        while self._running:
            # Progress time forward
            for x in range(self._physics_steps_per_frame):
                self._space.step(self._dt)

            self._process_events()
            self._update_balls()
            self.ball_boundary_collision()
            self._clear_screen()
            self._draw_objects()
            pygame.display.flip()


            #function which decides ball-ball collision outcomes
            def ball_collision(arbiter, space, data):
                self._create_ball()
                mysound1=pygame.mixer.Sound("F:/ball-clack.wav")
                mysound1.set_volume(arbiter.total_impulse.__abs__()/200000)
                pygame.mixer.find_channel().play(mysound1)
            
            #function which decides ball-wall collision outcomes. Fires after collision
            def wall_collision(arbiter, space, data):
                mysound=pygame.mixer.Sound("F:/steel-drum-4.wav")
                mysound.set_volume(1)
                pygame.mixer.find_channel().play(mysound)
            
            #function which decides death ball-ball collision outcomes. Fires after collision
            def death_collision(arbiter, space, data):
                self.delete_ball(arbiter[0])
                self.delete_ball(arbiter[1])


            h = self._space.add_collision_handler(self.collision_types["ball"],self.collision_types["ball"])
            h.post_solve = ball_collision

            b = self._space.add_collision_handler(self.collision_types["ball"],self.collision_types["wall"])
            b.post_solve = wall_collision

            c = self._space.add_collision_handler(self.collision_types["death-ball"],self.collision_types["ball"])
            c.post_solve = death_collision

            # Delay fixed time between frames
            self._clock.tick(self.get_FPS())
            pygame.display.set_caption("fps: " + str(self._clock.get_fps()))

    #Creates boundary of static line objects in the shape of a discretized circle
    def create_circle (self,radius, num_lines, centerX, centerY, line_weight = 0, bounce = 1, friction = 0):
        static_body = self._space.static_body
        static_lines = []
        theta_step = 2*math.pi/num_lines
        for i in range(num_lines):
            x1 = radius * math.cos(i*theta_step)
            y1 = radius * math.sin(i*theta_step)
            x2 = radius * math.cos((i+1)*theta_step)
            y2 = radius * math.sin((i+1)*theta_step)

            static_lines.append(pymunk.Segment(static_body, (x1+centerX, y1+centerY), (x2+centerX, y2+centerY), line_weight))
            for line in static_lines:
                line.elasticity = bounce
                line.friction = friction
        self._space.add(*static_lines)

#Creates boundary of wall objects in the shape of a discretized circle
    def _create_circle_obj(self,cx1,cy1,radius,numLines):
        for i in range(numLines):
            theta_step = 2*math.pi/numLines

            x1 = radius * math.cos(i*(theta_step))
            y1 = radius * math.sin(i*(theta_step))
            x2 = radius * math.cos((i+1)*(theta_step))
            y2 = radius * math.sin((i+1)*(theta_step))

            self._create_wall_helper(x1+cx1,y1+cy1,x2+cx1,y2+cy1,3)



    def _add_static_scenery(self) -> None:
        """
        Create the static bodies.
        :return: None
        """
        #self._create_circle_obj(self.x_pixel/2,self.y_pixel/2,self.x_pixel/3,10)
        self.create_circle(self.boundary_info["radius"],100,self.x_pixel/2,self.y_pixel/2,0)

    
    def _process_events(self) -> None:
        """
        Handle game and events like keyboard input. Call once per frame only.
        :return: None
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                pygame.image.save(self._screen, "bouncing_balls.png")

    def _flip_y(self,y):
        return -y + self.y_pixel


    def _update_balls(self) -> None:
        """
        Create/remove balls as necessary. Call once per frame only.
        :return: None

        """
        #update the previous location for balls
        for ball in self.newBalls:
            val = ball.getCenter()
            while(ball.prevLocations.qsize()>=ball.maxSize):
                ball.prevLocations.get()
                ball.prevColors.get()
            ball.prevLocations.put(val)
            ball.prevColors.put(ball.color)

        
        #remove balls if there are too many
        for i in range(self.num_balls-self.max_balls):
            self.delete_ball(self.newBalls[i])
        
    #Wrapper for _create_wall which makes arguments consistent with generating static lines 
    def _create_wall_helper(self,x1, y1, x2, y2, line_weight) -> None:
        angle = math.atan2((y2-y1),(x2-x1))
        pos_x = (x2+x1)/2
        pos_y = (y2+y1)/2


        len=abs(abs(x2-x1)*math.cos(angle))+abs(abs(y2-y1)*math.sin(angle))

        self._create_wall(pos_x, pos_y, len, line_weight, angle)

    #Creates wall objects
    def _create_wall(self, position_x, position_y, width, height, angle) -> None:
        # Spawn walls
        wall_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
        wall_body.position = position_x, position_y
        
        rotation = pymunk.Transform(math.cos(angle),math.sin(angle),-math.sin(angle),math.cos(angle),0,0)
        
        wall_shape = pymunk.Poly(wall_body, [(-width/2,-height/2),(width/2,-height/2),(width/2,height/2),(-width/2,height/2)],rotation,radius=0)
        wall_shape.elasticity = 1.0
        wall_shape.color = pygame.Color("grey")
        wall_shape.group = 1
        wall_shape.collision_type = self.collision_types["wall"]
        self._space.add(wall_body, wall_shape)
        self._rectangles.append(wall_shape)

    #create death ball object
    def _create_death(self):
        myDeath = self.Balls(50,50,(0,0,0),1,0,self.collision_types["death-ball"])
        self._space.add(myDeath.body,myDeath.shape)
        myDeath.body.position = self.x_pixel/2, self.y_pixel/2
        self.deathBalls.append(myDeath)

    #Create ball objects
    def _create_ball(self):        
        myBall = self.Balls(10,10,(255,250,228),1,0,self.collision_types["ball"])
        self._space.add(myBall.body,myBall.shape)
       # self._balls.append(myBall)

        #sets spawn point of balls by selecting a random point in polar coordinates within the bounding circle
        #values are hard coded, should be changed to automatically match generate_circle params [Incircle of a Polygon]
        angle = random.randint(0,360)
        max_length = (self.boundary_info["radius"] -myBall.radius)
        length = (random.uniform(0,max_length))

        x = length*math.cos(angle*math.pi/180)
        y = length*math.sin(angle*math.pi/180)        
        myBall.body.position = x+self.x_pixel/2, y+self.y_pixel/2

       # self._balls.append(myBall)
        self.num_balls+=1
        return myBall

    vals=0

    #deletes a ball from the given Ball object -> doesnt check for deathball
    def delete_ball(self,myBall):
        self._space.remove(myBall.shape,myBall.body)
        self.newBalls.pop(self.newBalls.index(myBall))
        self.num_balls-=1

    def ball_boundary_collision(self):
        #TODO: :Limit to one execution per boundary collision
        #Check for change in velocity position
        if(True):
            for ball in self.newBalls:
                p = ball.body.position
                x = p.x -self.x_pixel/2
                y = p.y - self.y_pixel/2
                dist = math.sqrt((x**2)+(y**2))

                #prevLocation

                #TODO: Add change in velocity direction check
                if(dist>(self.boundary_info["radius"]-ball.radius-13) and True):
                    ball.color=self.wall_color
                    #mysound=pygame.mixer.Sound("F:/steel-drum-4.wav")
                    #pygame.mixer.find_channel().play(mysound)
                

    def testball_collision(space, arbiter, dummy):
        shapes = arbiter.shapes
        shapes[0].color = (0, 255, 0, 255)
        shapes[1].color = (0, 255, 0, 255)
        

    def _clear_screen(self) -> None:
        """
        Clears the screen.
        :return: None
        """
        self._screen.fill(pygame.Color(self.get_background()))
       # self._surface.fill(pygame.Color(self.get_background()))

    def _draw_trail(self,ball,surface):
        #surface = self._screen
        size = ball.prevLocations.qsize()
        for i in range(size):
            if(True):#(i%step==0):
                location = ball.prevLocations.queue[size-1-i]
                color = ball.prevColors.queue[size-1-i]
                #darken the color the further it is away from the ball
                r=list(color)[0]
                g=list(color)[1]
                b=list(color)[2]
                color=(r*0.97**i,g*0.97**i,b*0.97**i)
                #reduce the trail radius the further it is away from the ball
                radius = ball.radius*0.97**i
                pygame.draw.circle(surface,color,location,radius)
                       

    def _draw_circles(self) -> None:
        for death in self.deathBalls:
            surface = self._screen
            pygame.draw.circle(surface,death.color,death.getCenter(),death.radius)
            #generate outside color ranging smoothly from red->orange and back
            color2 = self.gen_color((3*math.sin(pygame.time.get_ticks()/1000)+3))
            pygame.draw.circle(surface,color2,death.getCenter(),death.radius,2)

        for ball in self.newBalls:
            surface = self._screen
            self._draw_trail(ball,surface)
            pygame.draw.circle(surface,ball.color,ball.getCenter(),ball.radius)
            
            
            


    def gen_color(self,phase_shift):
# Define the time variable (you can use loop counter or real-time)
        time = phase_shift
    
    # Define the duration of transition between hues (in loops or time units)
        transition_duration = 60
    
    # Calculate hue value, smoothly transitioning from 0 to 1 over the duration
        hue = (time % transition_duration) / transition_duration
    
    # Convert HSL color to RGB
        r, g, b = colorsys.hls_to_rgb(hue, 0.5, 1.0)
    
    # Scale RGB values to the range [0, 255]
        r = int(round(r * 255))
        g = int(round(g * 255))
        b = int(round(b * 255))
    
        return (r, g, b)


    wall_color = pygame.Color("grey")

    change = 1

    def _draw_circle_border(self) -> None:
        

        self.wall_color=self.gen_color(pygame.time.get_ticks()/100%255)

        center = (self.x_pixel/2, self.y_pixel/2)
        surface = self._screen
        thickness = 8
        pygame.draw.circle(surface,self.wall_color,center,self.boundary_info["radius"]+thickness,thickness)


    def _draw_rectangles(self) ->None:
        for rectangle in self._rectangles:
            color = rectangle.color
            p = rectangle.body.position
            p = pymunk.Vec2d(p.x,p.y)
            center = (round(p.x), round(p.y))
            surface = self._screen
           # pygame.draw.rect(surface,color,pygame.Rect(0,1,2,3))

    def _draw_objects(self) -> None:
        """
        Draw the objects.
        :return: None
        """

        #self._space.debug_draw(self._draw_options)
        self._draw_circles()
        self._draw_rectangles()
        self._draw_circle_border()

        #sets the color of the outline to the set colour, defaults blue
       # self._draw_options.shape_outline_color = self._draw_options.shape_dynamic_color
       # self._space.debug_draw(self._draw_options)


def main():
    BouncyBalls().run()



if __name__ == "__main__":
    main()