import json
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx

from shapely.geometry import Point
from create_images_folders import get_comments_info
from scipy.stats import gaussian_kde
import matplotlib
import numpy as np 
matplotlib.use('QtAgg')

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
    padding_x = (xlim[1] - xlim[0]) * 0.8 # Increased padding for x
    padding_y = (ylim[1] - ylim[0]) * 0.8  # Increased padding for y
    ax.set_xlim([xlim[0] - padding_x, xlim[1] + padding_x])
    ax.set_ylim([ylim[0] - padding_y, ylim[1] + padding_y])
    
    ax.set_axis_off()
    plt.show()



def load_json_data(json_file_path):
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    return data




def load_and_process_json_data(json_files):
    data = {}
    for json_file in json_files:
        with open(json_file, 'r') as file:
            file_data = json.load(file)
        for key, value in file_data.items():
            image_paths = [value['images'][img] for img in value['images']]
            for path in image_paths:
                image_info = get_comments_info(path)
                if image_info['latitude'] and image_info['longitude']:
                    if key not in data:
                        data[key] = []
                    data[key].append(image_info)
                else:
                    print(f"Skipping image {path} due to missing GPS information.")
    return data

def plot_coordinates_with_legends_and_customizations(json_list, json_map, colors, sizes, padding, save_path):
    all_data = {}
    for json_file in json_list:
        all_data.update(load_and_process_json_data([json_file]))

    points = []
    legend_labels = []

    # Create GeoDataFrame from collected points
    for json_file, legend_label in json_map.items():
        if json_file in json_list:
            file_data = load_and_process_json_data([json_file])
            for key in file_data:
                for image_info in file_data[key]:
                    if image_info['latitude'] is not None and image_info['longitude'] is not None:
                        points.append(Point(image_info['longitude'], image_info['latitude']))
                        legend_labels.append(legend_label)

    gdf = gpd.GeoDataFrame(geometry=points, crs="EPSG:4326")
    gdf['legend'] = legend_labels
    gdf = gdf.to_crs(epsg=3857)
    gdf = remove_outliers(gdf)

    # Plot the GeoDataFrame
    fig, ax = plt.subplots(figsize=(10, 10))
    for label, df in gdf.groupby('legend'):
        color = colors[json_list.index(list(json_map.keys())[list(json_map.values()).index(label)]) % len(colors)]
        size = sizes[json_list.index(list(json_map.keys())[list(json_map.values()).index(label)]) % len(sizes)]
        df.plot(ax=ax, color=color, markersize=size, label=label, alpha=0.7, edgecolor='white', linewidth=0.5)

    # Add the basemap without attribution
    ctx.add_basemap(ax, source=ctx.providers.Esri.WorldImagery, attribution="")

    # Set the limits of the map to the limits of the actual data plus padding
    minx, miny, maxx, maxy = gdf.total_bounds
    ax.set_xlim(minx - padding, maxx + padding)
    ax.set_ylim(miny - padding, maxy + padding)

    # Hide the original axes
    ax.set_axis_off()

    # Draw grid lines on top of the base map
    # Create the grid lines manually
    ax.set_xticks([])
    ax.set_yticks([])
    grid_x = np.linspace(start=min(gdf.geometry.x), stop=max(gdf.geometry.x), num=10)
    grid_y = np.linspace(start=min(gdf.geometry.y), stop=max(gdf.geometry.y), num=10)
    for x in grid_x:
        ax.axvline(x, color='k', dashes=[10, 2], linewidth=1, alpha=1)
    for y in grid_y:
        ax.axhline(y, color='k', dashes=[10, 2], linewidth=1, alpha=1)

    # Add the legend with a slight alpha for better visibility
    legend = plt.legend(facecolor='white', framealpha=0.8)

    # Make sure grid lines are on top
    ax.set_axisbelow(False)
    ax.set_axis_off()


    plt.tight_layout()

    # Save the plot to an SVG file
    plt.savefig(save_path, bbox_inches='tight', dpi=700, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()


    # Show the plot
    plt.show()


if True:
    json_list = ['concrete_cracking.json', 'concrete_delamination.json', 'concrete_erosion.json', 'concrete_spalling.json', 'groutin_damage.json', 'pedestal_damage.json']
    #json_map = {'concrete_cracking.json':'Concrete Cracks', 'concrete_delamination.json':'Concrete Delamination', 'concrete_erosion.json':'Concrete Erosion', 'concrete_spalling.json':'Concrete Spalling', 'groutin_damage.json': 'Grouting Damage', 'pedestal_damage.json': 'Pedestal Damage'}
    json_map = {'concrete_cracking.json':'Concrete Defect Type #1', 
                'concrete_delamination.json':'Concrete Defect Type #2',
                'concrete_erosion.json':'Concrete Defect Type #3',
                'concrete_spalling.json':'Concrete Defect Type #4',
                'groutin_damage.json': 'Concrete Defect Type #5', 
                'pedestal_damage.json': 'Concrete Defect Type #6'}

    colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan']
    sizes = [25]*len(colors)

    padding = 50



    # Example usage with padding set to 100 meters and saving to an SVG file
    padding = 100
    save_path = 'your_plot.png'
    plot_coordinates_with_legends_and_customizations(json_list, json_map, colors, sizes, padding, save_path)

