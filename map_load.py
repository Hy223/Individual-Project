import math
import os
import queue
import random
import sys

import carla

IM_WIDTH = 640
IM_HEIGHT= 480


def main():
    try:
        client = carla.Client('localhost', 2000)
        client.load_world('Town03_opt')
        world = client.get_world()
        traffic_manager = client.get_trafficmanager()
        vehicle_spawn_points = world.get_map().get_spawn_points()
        ego_spawn_point = random.choice(vehicle_spawn_points)
        ego_bp = world.get_blueprint_library().find('vehicle.mini.cooper_s_2021')
        ego_bp.set_attribute('role_name', 'hero')
        ego_vehicle = world.spawn_actor(ego_bp, ego_spawn_point)
        ego_vehicle.set_autopilot()
        camera_bp = world.get_blueprint_library().find('sensor.camera.rgb')
        camera_bp.set_attribute("image_size_x", "{}".format(IM_WIDTH))
        camera_bp.set_attribute("image_size_y", "{}".format(IM_HEIGHT))
        camera_transform = carla.Transform(carla.Location(x=1.5, y=0, z=1.5), carla.Rotation(pitch=-120, yaw=0, roll=180))
        camera = world.spawn_actor(camera_bp, camera_transform, attach_to=ego_vehicle, attachment_type=carla.libcarla.AttachmentType.SpringArmGhost)
        setting = world.get_settings()
        traffic_manager.ignore_lights_percentage(ego_vehicle, 100)
        setting.synchronous_mode = True
        setting.fixed_delta_seconds = 0.1
        world.apply_settings(setting)
        traffic_manager.synchronous_mode = True
        image_queue = queue.Queue()
        camera.listen(image_queue.put)
        while True:
            world.tick()
            world.get_spectator().set_transform(camera.get_transform())
            if traffic_manager.synchronous_mode:
                image = image_queue.get()
                image.save_to_disk('_out/%06d' % image.frame)

            else:
                world.wait_for_tick()
    finally:
        for controller in world.get_actors().filter('*controller*'):
            controller.stop()
        for vehicle in world.get_actors().filter('*vehicle*'):
            vehicle.destroy()
        settings = world.get_settings()
        settings.synchronous_mode = False
        settings.fixed_delta_seconds = None
        world.apply_settings(settings)


if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        print('\ndone.')
