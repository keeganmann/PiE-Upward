from serial import Serial
import pygame
from math import sqrt

"""
TODO:
 - Replication Stats
 - Labels
"""

"""BASIC SETTINGS"""
width = 800
height = 600
sample_period = 10
sensor_count = 4
step_size = 3
fullscreen = False
scale_factor = 0.7
deriv_scale = 20
lowpass = 0.5
port_name = "/dev/tty.usbserial-A900cehS"

"""END OF BASIC SETTINGS"""

pygame.init()

#Setup Serial Port
print("Initializing Serial Port: ", (port_name))
ser = Serial(port_name)

#initialize screen
print("Using", width, "x", height)
if fullscreen:
    flags = pygame.FULLSCREEN
else:
    flags = 0
screen = pygame.display.set_mode((width, height), flags)
print("Supported Display Modes:  ")
pygame.display.list_modes()

#divide screen
div_hor = int(sqrt(sensor_count)+0.5)
div_vert = int(sqrt(sensor_count))
port_width = width//div_hor
div_height = height//div_vert
port_height = height//div_vert
print("Screen divided : ", div_hor, "x", div_vert)


#Setup font
font = pygame.font.Font(pygame.font.get_default_font(), 15)

colors = [[255, 0, 0], [0, 255, 0], [70, 70, 255], [255, 255, 0], [0, 255, 255], [255, 0, 255]]

current_message = "PIONEERS"
recordstate = 0

def update_values(array):
    val = ser.readline()
    i = 0
    #print "----"
    for item in val.strip().split():
        if i >= sensor_count:
            break
        try:
            #print int(item)
            array[i] = int(item)/1024.0*scale_factor
        except BaseException as _:
            print("Could not parse string")
        i += 1

def differentiate(inarray1, inarray2, outarray, tmInt, pderivatives):
    for i in range(0, len(inarray1)):
        #differentiate
        outarray[i] = (inarray2[i] - inarray1[i]) * deriv_scale
        #smooth
        outarray[i] = outarray[i] * (1 - lowpass) + pderivatives[i] * (lowpass)

def message(mymessage):
    screen.fill([0, 0, 0], [width/2-50, height/2-10, 100, 20])
    pygame.draw.rect(screen, [100, 100, 100], [width/2-50, height/2-10, 100, 20], 2)
    text = font.render(mymessage, True, [100, 100, 100])
    screen.blit(text, [width/2-text.get_width()/2, height/2-text.get_height()/2+2])

def axes():
    #draw axes
    for i in range(0, div_hor):
        pygame.draw.line(screen,[127,127,127], [width//div_hor*i,0],[width//div_hor*i,height],5)
    for i in range(0, div_vert):
        pygame.draw.line(screen,[127,127,127], [0,height//div_vert*i],[width,height//div_vert*i],5)
        pygame.draw.line(screen,[100,100,100], [0,height//div_vert*(i+0.5)],[width,height//div_vert*(i+0.5)],1)
    message(current_message)

def drawbuffer(num):
    global current_message
    if not num in buffers.keys():
        return
    for i in range(1, len(buffers[num])):
        for sensornumber in range(0, sensor_count):
            x = sensornumber % div_hor
            y = sensornumber // div_hor
            pygame.draw.line(screen,[80,80,80], 
                             [(i-1)*step_size+port_width*x,clip(buffers[num][i-1])*port_height+div_height*y], 
                             [i*step_size+port_width*x,clip(buffers[num][i])*port_height+div_height*y], 
                             3)

def clearscreen():
    global recordstate
    global current_message
    global savebuffer
    global currentbuffer
    global buffers
    if recordstate == 1:
        if current_buffer == 0:
            recordstate = 0
            current_message = "Cannot save to buffer 0" #cannot save to buffer 0
            break
        recordstate = 2
        current_message = "Recording"
        savebuffer = []
    elif recordstate == 2:
        recordstate = 0
        if current_buffer == 0:
            current_message = "Cannot save to buffer 0" #cannot save to buffer 0
            break
        buffers[currentbuffer] = savebuffer
        current_message = "Stored as " + str(currentbuffer)
    screen.fill([0,0,0])
    if currentbuffer != 0:
        drawbuffer(currentbuffer)
    axes();

def clip(val, small=0.0, big=1.0):
    return max(small, min(big, val))


print("Started")

savebuffer = []
currentbuffer = 1
buffers = {}
done = False
count = 0
vals =   [0 for _ in range(0, sensor_count)]
pvals =  [0 for _ in range(0, sensor_count)]
pdvals = [0 for _ in range(0, sensor_count)]
dvals =  [0 for _ in range(0, sensor_count)]
clearscreen()
while not done:
    #check events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done=True
        if event.type == pygame.KEYDOWN:
            if( event.key == pygame.K_f ):
                pygame.display.toggle_fullscreen()
            if( event.key == pygame.K_r ):
                recordstate = 1
                current_message = "READY"
            if( event.key == pygame.K_x or event.key == pygame.K_ESCAPE ):
                done = True
            if( event.key == pygame.K_b):
                if recordstate == 2:
                    break #don't change buffers while recording
                currentbuffer = (currentbuffer + 1) % 4
                if currentbuffer == 0:
                    current_message = "No buffer"
                else:
                    current_message = "Buffer " + str(currentbuffer)
                
            
    #increment iteration counter
    count = count + 1
    
    #clear screen if necessary
    if count*step_size > port_width:
        count = 0
        clearscreen()
    
    #swap buffers
    pdvals, dvals = dvals, pdvals
    pvals, vals = vals, pvals
    #read values
    update_values(vals)
    differentiate(pvals, vals, dvals, sample_period, pdvals)

    #draw traces
    for i in range(0, sensor_count):
        x = i % div_hor
        y = i // div_hor


        pygame.draw.line(screen,list(map(lambda x: x/2, colors[i])), 
                         [max(count-1, 0)*step_size+port_width*x,clip(pdvals[i],-0.5,0.5)*port_height+div_height*(y+0.5)], 
                         [          count*step_size+port_width*x,clip( dvals[i],-0.5,0.5)*port_height+div_height*(y+0.5)], 
                         3)


        pygame.draw.line(screen,colors[i], 
                         [max(count-1, 0)*step_size+port_width*x,clip(pvals[i])*port_height+div_height*y], 
                         [          count*step_size+port_width*x,clip( vals[i])*port_height+div_height*y], 
                         3)

        
    if recordstate == 2:
        savebuffer.append(vals[0])

    axes()
    pygame.display.flip()
    
