#!/usr/bin/env python3
import rclpy
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
import numpy as np
from shapely.geometry import Polygon, LineString, Point

def generate_boustrophedon_path(polygon_pts, stripe_spacing=0.20, point_step=None, frame_id='map'):
    """
    Generates back-and-forth boustrophedon waypoints inside a polygon area.
    """
    poly = Polygon(polygon_pts)
    min_x, min_y, max_x, max_y = poly.bounds

    # Generate vertical or horizontal sweep lines
    y_coords = np.arange(min_y + (stripe_spacing / 2.0), max_y, stripe_spacing)
    
    waypoints = []
    reverse_direction = False

    for y in y_coords:
        sweep_line = LineString([(min_x - 1.0, y), (max_x + 1.0, y)])
        intersection = poly.intersection(sweep_line)

        if intersection.is_empty:
            continue

        # Extract line segments inside the polygon
        segments = []
        if intersection.geom_type == 'LineString':
            segments.append(list(intersection.coords))
        elif intersection.geom_type == 'MultiLineString':
            for line in intersection.geoms:
                segments.append(list(line.coords))

        for seg in segments:
            # Interpolate waypoints along the lane based on point_step
            p1, p2 = np.array(seg[0]), np.array(seg[1])
            dist = np.linalg.norm(p2 - p1)

            if point_step is not None and point_step > 0.0:
                num_points = max(2, int(np.ceil(dist / point_step)) + 1)
                pts = [p1 + (p2 - p1) * (i / (num_points - 1)) for i in range(num_points)]
            else:
                pts = [p1, p2]

            if reverse_direction:
                pts = pts[::-1]

            for pt in pts:
                pose = PoseStamped()
                pose.header.frame_id = frame_id
                pose.pose.position.x = float(pt[0])
                pose.pose.position.y = float(pt[1])
                pose.pose.position.z = 0.0
                pose.pose.orientation.w = 1.0  # Orientation handled dynamically by MPPI
                waypoints.append(pose)

            reverse_direction = not reverse_direction

    return waypoints

def main():
    rclpy.init()
    navigator = BasicNavigator()

    # Wait for Nav2 to become fully active
    navigator.waitUntilNav2Active()

    # Define the room boundary coordinates (X, Y) on your map
    # Update these 4 corners to fit your room's inner floor space:
    room_polygon = [
        (-4.2, -0.16),
        (0.22, -0.16),
        (0.22, 2.3),
        (-4.2, 2.3)
    ]

    # Generate coverage path with a 20 cm lane width
    stripe_width = 0.25
    point_density = 0.20  # Distance (in meters) between waypoints along the same lane (set to None for lane endpoints only)
    path_poses = generate_boustrophedon_path(room_polygon, stripe_spacing=stripe_width, point_step=point_density)

    print(f"Generated {len(path_poses)} coverage waypoints. Executing coverage path...")

    # Send all waypoints to Nav2
    navigator.goThroughPoses(path_poses)

    # Monitor navigation task
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback:
            print(f"Remaining waypoints: {feedback.number_of_poses_remaining}", end='\r')

    # Handle completion result
    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        print("\nCoverage mission completed successfully!")
    elif result == TaskResult.CANCELED:
        print("\nCoverage mission was canceled.")
    elif result == TaskResult.FAILED:
        print("\nCoverage mission failed.")

    rclpy.shutdown()

if __name__ == '__main__':
    main()