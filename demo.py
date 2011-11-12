from serial import Serial
import serial.tools.list_ports
import pygame
from math import sqrt

"""*** BASIC SETTINGS ***"""
#display dimensions
width = 800
height = 600

#Not used
sample_period = 10

#number of times the screen should be divided
sensor_count = 4

#how fast the graph moves across the screen
step_size = 1

#display fullscreen?
fullscreen = False

#scales the distance
scale_factor = 12

#scales the velocity
deriv_scale = 20

#Filtering constant for velocity graph (between 0 and 1)
lowpass = 0.7

#name of the serial port associated with the Arduino
port_name = "/dev/tty.usbserial-A900cehS"
#I think it was COM4 or something for Sahar

#the number of buffers
max_buffers = 4

"""*** END OF BASIC SETTINGS ***"""

pygame.init()

#Setup Serial Port
print("Available Serial Ports:")
serial.tools.list_ports.main()
print("")
print("Initializing Serial Port: " + str(port_name))
try:
    ser = Serial(port_name)
except BaseException as e:
    print(e)
    print("====================================================")
    print("Failed to Initialize Serial Port")
    print("Make sure the Arduino is connected")
    print("If you have not already, edit the port_name = ... line in this python file")
    print("On windows it should be set to something like COM#")
    print("On UNIX/Linux/Mac, it should be set to something like /dev/tty...")
    print("See the list of serial ports printed above under 'Available Serial Ports'.")
    exit()

#initialize screen
print("")
print("Using resolution: " + str(width) + "x" + str(height) )
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
print("Screen divided: " + str(div_hor) + "x" + str(div_vert) )


#Setup font
font = pygame.font.Font(pygame.font.get_default_font(), 15)

colors = [[255, 0, 0], [0, 255, 0], [70, 70, 255], [255, 255, 0], [0, 255, 255], [255, 0, 255]]

#message to display in center
current_message = "PIONEERS"
#state of the recording 0=normal, 1=ready to record, 2=recording
recordstate = 0

pong = False

ballv = 0

b1p = [100,100]
b1v = [1,0]
b2p = [100,100]
b2v = [1,0]

def update_values(array):
    """Fetches values from the arduino and puts them in the passed array"""
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
            print("Warning: Could not parse string")
        i += 1

def differentiate(inarray1, inarray2, outarray, tmInt, pderivatives):
    """Takes the derivative and smooths the result"""
    for i in range(0, len(inarray1)):
        #differentiate
        outarray[i] = (inarray2[i] - inarray1[i]) * deriv_scale
        #smooth
        outarray[i] = outarray[i] * (1 - lowpass) + pderivatives[i] * (lowpass)

def message(mymessage):
    """Displays the message passed in the center of the screen"""
    screen.fill([0, 0, 0], [width/2-50, height/2-10, 100, 20])
    pygame.draw.rect(screen, [100, 100, 100], [width/2-50, height/2-10, 100, 20], 2)
    text = font.render(mymessage, True, [100, 100, 100])
    screen.blit(text, [width/2-text.get_width()/2, height/2-text.get_height()/2+2])

def axes():
    """draw borders and divisions on the screen"""
    for i in range(0, div_hor):
        pygame.draw.line(screen,[127,127,127], [width//div_hor*i,0],[width//div_hor*i,height],5)
    for i in range(0, div_vert):
        pygame.draw.line(screen,[127,127,127], [0,height//div_vert*i],[width,height//div_vert*i],5)
        pygame.draw.line(screen,[100,100,100], [0,height//div_vert*(i+0.5)],[width,height//div_vert*(i+0.5)],1)
    message(current_message)

def drawbuffer(num):
    """Draws the current reference buffer"""
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
    """
    Clears the screen.  Calls many necessary helper funcitons to draw the 
    necessary elements
    """
    global recordstate
    global current_message
    global savebuffer
    global currentbuffer
    global buffers
    if recordstate == 1:
        if currentbuffer == 0:
            recordstate = 0
            current_message = "Specify Bufr!" #cannot save to buffer 0
        else:
            recordstate = 2
            current_message = "Recording"
            savebuffer = []
    elif recordstate == 2:
        recordstate = 0
        if currentbuffer == 0:
            current_message = "Specify Bufr!" #cannot save to buffer 0
        else:
            buffers[currentbuffer] = savebuffer
            current_message = "Stored as " + str(currentbuffer)
    screen.fill([0,0,0])
    if currentbuffer != 0:
        drawbuffer(currentbuffer)
    axes();

def clip(val, small=0.0, big=1.0):
    """Clips a value, val to between small and big"""
    return max(small, min(big, val))

#Temporary buffer for data to save
savebuffer = []
#The current buffer to display/save data to
currentbuffer = 1
#Reference buffers data is saved to
buffers = {}
#set to true causes exit
done = False
#position across the screen
count = 0
#buffers used to store the necessary sensor data for one frame
vals =   [0 for _ in range(0, sensor_count)]
pvals =  [0 for _ in range(0, sensor_count)]
pdvals = [0 for _ in range(0, sensor_count)]
dvals =  [0 for _ in range(0, sensor_count)]
#clear the screen before we begin
clearscreen()
print("")
print("Started Successfully!")
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
                currentbuffer = (currentbuffer + 1) % max_buffers
                if currentbuffer == 0:
                    current_message = "No buffer"
                else:
                    current_message = "Buffer " + str(currentbuffer)
            if( event.key == pygame.K_p ):
                pong = not pong
    
            
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


        pygame.draw.line(screen,list(map(lambda x: x/10, colors[i])), 
                         [max(count-1, 0)*step_size+port_width*x,clip(pdvals[i],-0.5,0.5)*port_height+div_height*(y+0.5)], 
                         [          count*step_size+port_width*x,clip( dvals[i],-0.5,0.5)*port_height+div_height*(y+0.5)], 
                         3)

        
        pygame.draw.line(screen,colors[i], 
                         [max(count-1, 0)*step_size+port_width*x,clip(pvals[i])*port_height+div_height*y], 
                         [          count*step_size+port_width*x,clip( vals[i])*port_height+div_height*y], 
                         3)

    #if recording, save to the savebuffer
    if recordstate == 2:
        savebuffer.append(vals[0])

    #draw axes on top every time
    axes()

    
    if pong:
        #screen.fill([0,0,0], [0,0,10,height])
        #screen.fill([0,0,0], [width-10,0,width,height])
        screen.fill([0,0,0], [0,0,width,height])

        ul_top = clip(vals[0])*div_height - 20
        ul_btm = clip(vals[0])*div_height  + 20
        ur_top = clip(vals[1])*div_height  - 20
        ur_btm = clip(vals[1])*div_height  + 20
        bl_top = clip(vals[2])*div_height  - 20
        bl_btm = clip(vals[2])*div_height + 20
        br_top = clip(vals[3])*div_height - 20
        br_btm = clip(vals[3])*div_height + 20
        screen.fill([255, 255, 255], [0,ul_top,10,40])
        screen.fill([255, 255, 255], [width-10,ur_top,10,40])
        screen.fill([255, 255, 255], [0,bl_top+div_height,10,40])
        screen.fill([255, 255, 255], [width-10,br_top+div_height,10,40])
        
        screen.fill([255,255,255], b1p + [10,10])
        #screen.fill([255,255,255], b2p + [10,10])
        if 1:
            b1p[0] += b1v[0]
            b1p[1] += b1v[1]
            b2p[0] += b2v[0]
            b2p[1] += b2v[1]
            if b1p[0] < 0 or b1p[0] > width:
                reset_ball()
            if b1p[1] < 0:
                p1p[1] = 0
                b1v *= -1
            if b1p[1] > height:
                p1p[1] = height
                b1v *= -1
        
        
    #refresh the screen
    pygame.display.flip()

    
