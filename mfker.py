import carla
import random
import pygame
import numpy as np
import queue
import os
from ultralytics import YOLO

client = carla.Client('localhost', 2000)
client.load_world('Town01_opt')
world = client.get_world()

settings = world.get_settings()
settings.synchronous_mode = True # Enables synchronous mode
settings.fixed_delta_seconds = 0.01
world.apply_settings(settings)

traffic_manager = client.get_trafficmanager()
traffic_manager.set_synchronous_mode(True)


spectator = world.get_spectator()

spawn_points = world.get_map().get_spawn_points()

IM_WIDTH = 640
IM_HEIGHT= 480



# Render object to keep and pass the PyGame surface
class RenderObject(object):
    def __init__(self, width, height):
        init_image = np.random.randint(0,255,(height,width,3),dtype='uint8')
        self.surface = pygame.surfarray.make_surface(init_image.swapaxes(0,1))

# Camera sensor callback, reshapes raw data from camera into 2D RGB and applies to PyGame surface
def pygame_callback(data, obj):
    img = np.reshape(np.copy(data.raw_data), (data.height, data.width, 4))
    img = img[:,:,:3]
    img = img[:, :, ::-1]
    obj.surface = pygame.surfarray.make_surface(img.swapaxes(0,1))
    # Process the current control state
    keys = pygame.key.get_pressed()
    if keys[pygame.K_SPACE]:
        image_queue = queue.Queue()
        image_queue.put(data)
        image = image_queue.get()
        image.save_to_disk('_out/carla_scene.jpg')


def yolo_detect():
    if os.path.exists('_out/carla_scene.jpg'):
        model = YOLO("best.pt")  # load a custom model
        results = model.predict("_out/carla_scene.jpg")  # predict on an image
        for result in results:
            names = [result.names[cls.item()] for cls in result.boxes.cls.int()]
        if names != []:
            return str(names[0])
        else:
            return 'no_detection'



class ControlObject(object):
    def __init__(self, veh):

        # Conrol parameters to store the control state
        self._vehicle = veh
        self._steer = 0
        self._throttle = False
        self._brake = False
        self._steer = None
        self._steer_cache = 0
        # A carla.VehicleControl object is needed to alter the
        # vehicle's control state
        self._control = carla.VehicleControl()

    # Check for key press events in the PyGame window
    # and define the control state
    def parse_control(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._vehicle.set_autopilot(False)
            if event.key == pygame.K_UP:
                self._throttle = True
            if event.key == pygame.K_DOWN:
                self._brake = True
            if event.key == pygame.K_RIGHT:
                self._steer = 1
            if event.key == pygame.K_LEFT:
                self._steer = -1
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_UP:
                self._throttle = False
            if event.key == pygame.K_DOWN:
                self._brake = False
                self._control.reverse = False
            if event.key == pygame.K_RIGHT:
                self._steer = None
            if event.key == pygame.K_LEFT:
                self._steer = None

    # Process the current control state, change the control parameter
    # if the key remains pressed
    def process_control(self):

        if self._throttle:
            self._control.throttle = min(self._control.throttle + 0.01, 1)
            self._control.gear = 1
            self._control.brake = False
        elif not self._brake:
            self._control.throttle = 0.0

        if self._brake:
            # If the down arrow is held down when the car is stationary, switch to reverse
            if self._vehicle.get_velocity().length() < 0.01 and not self._control.reverse:
                self._control.brake = 0.0
                self._control.gear = 1
                self._control.reverse = True
                self._control.throttle = min(self._control.throttle + 0.1, 1)
            elif self._control.reverse:
                self._control.throttle = min(self._control.throttle + 0.1, 1)
            else:
                self._control.throttle = 0.0
                self._control.brake = min(self._control.brake + 0.3, 1)
        else:
            self._control.brake = 0.0

        if self._steer is not None:
            if self._steer == 1:
                self._steer_cache += 0.03
            if self._steer == -1:
                self._steer_cache -= 0.03
            min(0.7, max(-0.7, self._steer_cache))
            self._control.steer = round(self._steer_cache,1)
        else:
            if self._steer_cache > 0.0:
                self._steer_cache *= 0.2
            if self._steer_cache < 0.0:
                self._steer_cache *= 0.2
            if 0.01 > self._steer_cache > -0.01:
                self._steer_cache = 0.0
            self._control.steer = round(self._steer_cache,1)

        # Ápply the control parameters to the ego vehicle
        self._vehicle.apply_control(self._control)


# Select a vehicle to follow with the camera
ego_spawn_point = random.choice(spawn_points)
ego_bp = world.get_blueprint_library().find('vehicle.mini.cooper_s_2021')
ego_bp.set_attribute('role_name', 'hero')
ego_vehicle = world.spawn_actor(ego_bp, ego_spawn_point)

# Initialise the camera floating behind the vehicle
camera_init_trans = carla.Transform(carla.Location(x=1.5, y=0, z=1.5), carla.Rotation(pitch=-20))
camera_bp = world.get_blueprint_library().find('sensor.camera.rgb')
camera_bp.set_attribute("image_size_x", "{}".format(IM_WIDTH))
camera_bp.set_attribute("image_size_y", "{}".format(IM_HEIGHT))
camera = world.spawn_actor(camera_bp, camera_init_trans, attach_to=ego_vehicle)

# Start camera with PyGame callback
camera.listen(lambda image: pygame_callback(image, renderObject))

# Get camera dimensions
image_w = camera_bp.get_attribute("image_size_x").as_int()
image_h = camera_bp.get_attribute("image_size_y").as_int()

# Instantiate objects for rendering and vehicle control
renderObject = RenderObject(image_w, image_h)
controlObject = ControlObject(ego_vehicle)


pygame.init()
gameDisplay = pygame.display.set_mode((image_w,image_h), pygame.HWSURFACE | pygame.DOUBLEBUF)
# Draw black to the display
gameDisplay.fill((0,0,0))
gameDisplay.blit(renderObject.surface, (0,0))
pygame.display.flip()



# Game loop
crashed = False

while not crashed:
    # Advance the simulation time
    world.tick()
    # Update the display
    gameDisplay.blit(renderObject.surface, (0,0))
    font = pygame.font.SysFont("Arial", 50)
    red = (255, 0, 0)
    detection ='no_detection'
    keys = pygame.key.get_pressed()
    if keys[pygame.K_r]:
        detection = str(yolo_detect())
        pygame.display.flip()
    txtsurf = font.render(detection, True, red)
    gameDisplay.blit(txtsurf, (0, 0))
    pygame.display.flip()
    # Process the current control state
    controlObject.process_control()
    # Collect key press events
    for event in pygame.event.get():
        # If the window is closed, break the while loop
        if event.type == pygame.QUIT:
            crashed = True

        # Parse effect of key press event on control state
        controlObject.parse_control(event)
        if event.type == pygame.KEYUP:
            # TAB key switches pilot
            if event.key == pygame.K_TAB:
                ego_vehicle.set_autopilot(True)
                traffic_manager.ignore_lights_percentage(ego_vehicle, 100)



# Stop camera and quit PyGame after exiting game loop
camera.stop()
pygame.quit()
if crashed:
    for controller in world.get_actors().filter('*controller*'):
        controller.stop()
    for vehicle in world.get_actors().filter('*vehicle*'):
        vehicle.destroy()
    settings = world.get_settings()
    settings.synchronous_mode = False
    settings.fixed_delta_seconds = 0.01
    world.apply_settings(settings)