import json
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import contextily as ctx


def remove_outliers(gdf):
    # Calculate Q1, Q3, and IQR for both X and Y coordinates
    Q1_x = gdf.geometry.x.quantile(0.25)
    Q3_x = gdf.geometry.x.quantile(0.75)
    IQR_x = Q3_x - Q1_x

    Q1_y = gdf.geometry.y.quantile(0.25)
    Q3_y = gdf.geometry.y.quantile(0.75)
    IQR_y = Q3_y - Q1_y

    # Define bounds for outliers
    lower_bound_x = Q1_x - 1.5 * IQR_x
    upper_bound_x = Q3_x + 1.5 * IQR_x

    lower_bound_y = Q1_y - 1.5 * IQR_y
    upper_bound_y = Q3_y + 1.5 * IQR_y

    # Filter out outliers based on X and Y coordinates
    gdf_filtered = gdf[(gdf.geometry.x >= lower_bound_x) & (gdf.geometry.x <= upper_bound_x) &
                       (gdf.geometry.y >= lower_bound_y) & (gdf.geometry.y <= upper_bound_y)]

    return gdf_filtered



def plot_coordinates_with_satellite_base_map(image_info):
    points = []
    for location, infos in image_info.items():
        for info in infos:
            if info['latitude'] is not None and info['longitude'] is not None:
                points.append(Point(info['longitude'], info['latitude']))

    # Create a GeoDataFrame
    gdf = gpd.GeoDataFrame(geometry=points, crs="EPSG:4326")  # WGS 84

    # Convert to Web Mercator for contextily
    gdf = gdf.to_crs(epsg=3857)

    # Remove outliers
    gdf = remove_outliers(gdf)

    # Plot the points with a satellite base map
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(ax=ax, color='magenta', markersize=10, alpha=0.5)  # Adjust markersize and alpha as needed
    
    # Add basemap
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery)  # Using Esri's World Imagery service
    
    # Adjust the visible area by setting the limits
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    padding_x = (xlim[1] - xlim[0]) * 0.5  # Increased padding for x
    padding_y = (ylim[1] - ylim[0]) * 0.5  # Increased padding for y
    ax.set_xlim([xlim[0] - padding_x, xlim[1] + padding_x])
    ax.set_ylim([ylim[0] - padding_y, ylim[1] + padding_y])
    
    ax.set_axis_off()
    plt.show()


def load_json_data(json_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    return data

json_file_path_A = r"C:\Users\aleja\Documents\image_info.json"
json_file_path_R = r"C:\Users\aleja\Documents\image_info_r.json"



image_info_A= load_json_data(json_file_path_A)
image_info_R = load_json_data(json_file_path_R)

plot_coordinates_with_satellite_base_map({**image_info_A,**image_info_R})

