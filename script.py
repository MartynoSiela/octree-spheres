import open3d as o3d
import numpy as np
import pylas


def las_to_open3d_point_cloud(las_path):
    las_data = pylas.read(las_path)
    xyz = np.vstack((las_data.x, las_data.y, las_data.z)).T
    point_cloud = o3d.geometry.PointCloud()
    point_cloud.points = o3d.utility.Vector3dVector(xyz)

    if 'red' in las_data.point_format.dimension_names:
        colors = np.vstack((las_data.red, las_data.green, las_data.blue)).T / 255
        point_cloud.colors = o3d.utility.Vector3dVector(colors)

    return point_cloud


def points_inside_sphere(points, sphere_center, radius):
    distances = np.linalg.norm(points - sphere_center, axis=1)
    return distances <= radius


def collect_points_in_spheres(pcd, max_depth, current_depth=1):
    collected_points = []

    def recursive_traversal(node, node_info):
        nonlocal collected_points

        center = np.array(node_info.origin) + node_info.size / 2
        radius = node_info.size / 2

        if isinstance(node, o3d.geometry.OctreePointColorLeafNode):
            node_points = np.asarray(pcd.points)[node.indices]
            points_in_sphere_mask = points_inside_sphere(node_points, center, radius)
            points_in_sphere = node_points[points_in_sphere_mask]

            if len(points_in_sphere) > 0:
                if current_depth < max_depth:
                    sub_pcd = o3d.geometry.PointCloud()
                    sub_pcd.points = o3d.utility.Vector3dVector(points_in_sphere)
                    deeper_points = collect_points_in_spheres(sub_pcd, max_depth, current_depth + 1)
                    if not deeper_points:
                        collected_points.extend(points_in_sphere)
                    else:
                        collected_points.extend(deeper_points)
                else:
                    collected_points.extend(points_in_sphere)

        return False

    octree = o3d.geometry.Octree(max_depth=1)
    octree.convert_from_point_cloud(pcd, size_expand=0.0001)
    octree.traverse(recursive_traversal)

    return collected_points


def main():
    las_path = "sample.las"
    pcd = las_to_open3d_point_cloud(las_path)

    collected_points = collect_points_in_spheres(pcd, max_depth=12)

    final_pcd = o3d.geometry.PointCloud()
    final_pcd.points = o3d.utility.Vector3dVector(np.array(collected_points))
    o3d.visualization.draw_geometries([pcd])
    o3d.visualization.draw_geometries([final_pcd])


if __name__ == "__main__":
    main()
