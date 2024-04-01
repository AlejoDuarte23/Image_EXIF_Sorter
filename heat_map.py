import json
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
import numpy as np
import pandas as pd 

from scipy.interpolate import griddata

from shapely.geometry import Point, Polygon
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.colorbar import ColorbarBase

# Assuming get_comments_info is defined in create_images_folders
from create_images_folders import get_comments_info

from scipy.stats import gaussian_kde

from scipy.ndimage import gaussian_filter


from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle
from matplotlib.colorbar import ColorbarBase

# Function to remove outliers

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


# Function to load JSON data and assign weights based on damage type
def load_and_weight_json_data(json_files, damage_weights):
    points = []
    weights = []
    for json_file in json_files:
        with open(json_file, 'r') as file:
            file_data = json.load(file)
        for image_path, info in file_data.items():
            if info['latitude'] and info['longitude']:
                point = Point(info['longitude'], info['latitude'])
                # Assign weights based on the damage type
                weight = damage_weights.get(json_file, 0)
                points.append((info['longitude'], info['latitude']))  # Change to tuple
                weights.append(weight)
            else:
                print(f"Skipping image {image_path} due to missing GPS information.")
    return points, weights



def add_heatmap_on_transparent_on_top(points, weights, base_map_provider, save_path):
    # Prepare the data
    df = pd.DataFrame(points, columns=['Longitude', 'Latitude'])
    df['Weight'] = weights
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude), crs="EPSG:4326")  # WGS 84

    # Convert to Web Mercator for contextily
    gdf = gdf.to_crs(epsg=3857)

    # Plot the points with a satellite base map
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf.plot(ax=ax, color='magenta', markersize=10, alpha=0.5)  # Adjust markersize and alpha as needed
    
    # Add basemap
    ctx.add_basemap(ax, source=base_map_provider)  # Using Esri's World Imagery service

    # Adjust the visible area by setting the limits


    # Create a grid to interpolate
    x = np.linspace(xlim[0], xlim[1], 1000)
    y = np.linspace(ylim[0], ylim[1], 1000)
    x, y = np.meshgrid(x, y)
    # Interpolate using points' weights
    z = griddata((gdf.geometry.x, gdf.geometry.y), weights, (x, y), method='cubic', fill_value=0)

    # Overlay the heatmap
    ax.imshow(z, extent=xlim+ylim, origin='lower', alpha=0.6, cmap='hot', aspect='auto')

    ax.set_axis_off()

    plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
    plt.show()

def add_hotspot_heatmap_with_transparency(points, weights, save_path):



    df = pd.DataFrame(points, columns=['Longitude', 'Latitude'])
    df['Weight'] = weights
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude), crs="EPSG:4326")  # WGS 84

    # Convert to Web Mercator for contextily
    gdf_web_mercator = gdf.to_crs(epsg=3857)

    # Plot the points with a satellite base map
    fig, ax = plt.subplots(figsize=(10, 10))
    gdf_web_mercator.plot(ax=ax, color='magenta', markersize=10, alpha=0.5)  # Adjust markersize and alpha as needed
    
    # Add basemap
    ctx.add_basemap(ax, source=base_map_provider)  # Using Esri's World Imagery service

    # Adjust the visible area by setting the limits
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    xs = gdf_web_mercator.geometry.x
    ys = gdf_web_mercator.geometry.y


    # KDE
    kde = gaussian_kde(np.vstack([xs, ys]), weights=weights)
    xmin, xmax = xs.min(), xs.max()
    ymin, ymax = ys.min(), ys.max()

    # Grid
    xx, yy = np.mgrid[xmin:xmax:500j, ymin:ymax:500j]
    grid_coords = np.vstack([xx.ravel(), yy.ravel()])
    zz = np.reshape(kde(grid_coords), xx.shape)

    # Normalize density values to [0, 1] for alpha mapping
    zz_normalized = zz / zz.max()

    # Create an RGBA heatmap where low densities are transparent
    heatmap_rgba = plt.cm.hot(zz_normalized)
    # Set the alpha channel according to density
    heatmap_rgba[..., 3] = np.clip(zz_normalized, 0.1, 1)

    ax.imshow(heatmap_rgba, origin='lower', extent=[xmin, xmax, ymin, ymax], aspect='auto')
    
    ax.axis('off')
    plt.savefig(save_path)
    plt.show()


def add_heatmap_with_transparency_new(points, weights, save_path, base_map_provider,smoothing_sigma=1.3):
    # Creating a GeoDataFrame with the points and their associated weights
    df = pd.DataFrame(points, columns=['Longitude', 'Latitude'])
    df['Weight'] = weights
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude), crs="EPSG:4326")  # WGS 84

    # Convert to Web Mercator for contextily
    gdf_web_mercator = gdf.to_crs(epsg=3857)

    # Plot the points with a satellite base map
    fig, ax = plt.subplots(figsize=(5, 10))
    gdf_web_mercator.plot(ax=ax, color='k', markersize=2, alpha=0.1)  # Adjust markersize and alpha as needed
    
    # Add basemap
    ctx.add_basemap(ax, source=base_map_provider,attribution="")  # Using Esri's World Imagery service

    # Adjust the visible area by setting the limits
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()

    padding_x = (xlim[1] - xlim[0]) * 0.8 # Increased padding for x
    padding_y = (ylim[1] - ylim[0]) * 0.8  # Increased padding for y
    ax.set_xlim([xlim[0] - padding_x, xlim[1] + padding_x])
    ax.set_ylim([ylim[0] - padding_y, ylim[1] + padding_y])



    x = gdf_web_mercator.geometry.x
    y = gdf_web_mercator.geometry.y

    heatmap, xedges, yedges = np.histogram2d(x, y, bins=100, weights=gdf['Weight'], density=True)
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    heatmap_smoothed = gaussian_filter(heatmap, sigma=smoothing_sigma)  # Adjust the sigma value for more or less smoothing
    # Plot heatmap
    heatmap_image = ax.imshow(heatmap_smoothed.T, extent=extent, origin='lower', cmap='seismic', alpha=0.3)
    #ax.imshow(heatmap_smoothed.T, extent=extent, origin='lower', cmap='hot', alpha=0.3)

    
    # Create color bar
    cbar = fig.colorbar(heatmap_image, ax=ax, orientation='vertical', fraction=0.02, pad=0.04)
    cbar.set_ticks([np.min(heatmap_smoothed), np.max(heatmap_smoothed)/2, np.max(heatmap_smoothed)])
    cbar.set_ticklabels(['Low', 'Moderate', 'Major'])



    ax.set_xticks([])
    ax.set_yticks([])   
    grid_x = np.linspace(start=min(x), stop=max(x), num=10)
    grid_y = np.linspace(start=min(y), stop=max(y), num=10)
    for x in grid_x:
        ax.axvline(x, color='k', linestyle='--', linewidth=.1, alpha=1)
    for y in grid_y:
        ax.axhline(y, color='k', linestyle='--', linewidth=0.1, alpha=1)

        
    # Adjust the limits and save the plot
    ax.set_xlim(gdf_web_mercator.total_bounds[[0, 2]])
    ax.set_ylim(gdf_web_mercator.total_bounds[[1, 3]])
    #ax.axis('off')



    fig.patch.set_facecolor('white')  # Set the outer color
    plt.savefig(save_path, bbox_inches='tight', dpi=700, pad_inches=0.1, edgecolor='white')
    plt.close(fig)


def add_heatmap_with_transparency_new_box(points, weights, save_path, base_map_provider, smoothing_sigma=1.3):
     # Creating a GeoDataFrame with the points and their associated weights
    # Creating a GeoDataFrame with the points and their associated weights
    df = pd.DataFrame(points, columns=['Longitude', 'Latitude'])
    df['Weight'] = weights
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude), crs="EPSG:4326")

    # Convert to Web Mercator for contextily
    gdf_web_mercator = gdf.to_crs(epsg=3857)

    # Plot the points with a satellite base map
    fig, ax = plt.subplots(figsize=(10, 10))  # Adjusted for square aspect ratio
    gdf_web_mercator.plot(ax=ax, color='k', markersize=1, alpha=0)  # Made points invisible

    # Add basemap
    ctx.add_basemap(ax, source=base_map_provider, attribution="")

    # Creating heatmap...
    x = gdf_web_mercator.geometry.x
    y = gdf_web_mercator.geometry.y
    heatmap, xedges, yedges = np.histogram2d(x, y, bins=100, weights=gdf['Weight'], density=True)
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
    heatmap_smoothed = gaussian_filter(heatmap, sigma=smoothing_sigma)

    # Overlay heatmap
    heatmap_image = ax.imshow(heatmap_smoothed.T, extent=extent, origin='lower', cmap='hot', alpha=0.25)

    # Adjust the aspect ratio and the limits to match the basemap
    ax.set_aspect('equal')
    ax.set_xlim([xedges[0], xedges[-1]])
    ax.set_ylim([yedges[0], yedges[-1]])

    # Customizing the color bar
    cbar_ax = fig.add_axes([0.93, ax.get_position().y0, 0.02, ax.get_position().height])
    cbar = ColorbarBase(cbar_ax, cmap='hot', norm=Normalize(vmin=0, vmax=1), orientation='vertical')
    cbar.set_ticks([0, 0.5, 1])
    cbar.set_ticklabels(['Low', 'Moderate', 'Major'])
    cbar.ax.yaxis.set_label_position('left')  # Move the label to the LHS of the bar
    cbar.set_label('Defect Rating', rotation=270, labelpad=15)  # Adjust labelpad as needed

    # Adding gridlines
    grid_x = np.linspace(start=min(x), stop=max(x), num=10)
    grid_y = np.linspace(start=min(y), stop=max(y), num=10)
    for gx in grid_x:
        ax.axvline(gx, color='k', dashes=[10, 2], linewidth=1, alpha=1)
    for gy in grid_y:
        ax.axhline(gy, color='k', dashes=[10, 2], linewidth=1, alpha=1)

    # Rotate x-tick labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

    # Change transparent figure background to white
    fig.patch.set_facecolor('white')
    ax.patch.set_facecolor('white')

    # Save the figure with no surrounding transparent space
    #plt.savefig(save_path, bbox_inches='tight', dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.savefig(save_path,format = 'svg' ,bbox_inches='tight', facecolor=fig.get_facecolor(), edgecolor='none')
    
    plt.close(fig)
# Example usage
damage_weights = {  
    'concrete_cracking.json': 20,
    'concrete_delamination.json': 35,
    'concrete_erosion.json': 10,
    'concrete_spalling.json': 95,
    'groutin_damage.json': 40,
    'pedestal_damage.json': 90
} 
json_files = list(damage_weights.keys())
base_map_provider = ctx.providers.Esri.WorldImagery
save_path_overlay = 'heatmap_concrete.svg'
points, weights = load_and_weight_json_data(json_files, damage_weights)
add_heatmap_with_transparency_new_box(points, weights,  save_path_overlay,base_map_provider)