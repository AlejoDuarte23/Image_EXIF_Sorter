import os 
import json 
import shutil
import pandas as pd 

from PIL import Image

def get_decimal_from_dms(dms: float, ref: str) -> float:
    '''Converts GPS coordinates from degrees, minutes, seconds to decimal format'''
    degrees, minutes, seconds = dms
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def get_comments_info(image_path:str)->dict:
    ''' Get the metadata using exif data: date, coordinates, location and description'''
    with Image.open(image_path) as img:
       
        info = img._getexif()

        decoded_string = info[37510].decode('ascii')
        cleaned_string = decoded_string.replace('ASCII', '').replace('\x00', '').strip()
        parts = cleaned_string.split(',', 1)
        location = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else '' 
        
        date = info[36867]
        gps_info = info.get(34853)

        if gps_info:
            latitude = get_decimal_from_dms(gps_info[2], gps_info[1])
            longitude = get_decimal_from_dms(gps_info[4], gps_info[3])
        else:
            latitude, longitude = 10, 10  # Default to None if GPS info is not present
        return {
            'location': location,
            'description': description,
            'date': date,
            'latitude': latitude,
            'longitude': longitude,
            'path': image_path
        }

def move_images_to_folders(image_info: dict, base_folder: str) -> None:
    '''Move images to folders based on the location and description'''

    for location, info_list in image_info.items():
            # Sanitize the location string to avoid issues with invalid folder names
            folder_name = sanitize_folder_name(location)
            location_folder = os.path.join(base_folder, folder_name)
            
            # Ensure the location folder exists
            try:
                os.makedirs(location_folder, exist_ok=True)
                
                for info in info_list:
                    description = sanitize_folder_name(info['description']) if info['description'] else 'No Description'
                    target_subfolder = os.path.join(location_folder, description)
                    
                    # Ensure the description subfolder exists
                    os.makedirs(target_subfolder, exist_ok=True)
                    
                    source_path = info['path']
                    destination_path = os.path.join(target_subfolder, os.path.basename(source_path))
                    try:
                        shutil.move(source_path, destination_path)
                        print(f"Moved: {source_path} to {destination_path}")
                    except Exception as e:
                        print(f"Error moving {source_path} to {destination_path}: {e}")
            except:
                print(location_folder,'Dont work')


def sanitize_folder_name(name: str) -> str:
    '''Sanitize a string to remove invalid characters for folder names'''
    invalid_chars = '<>:"/\\|?*\n'
    for char in invalid_chars:
        name = name.replace(char, ' ')
    return name

def save_image_info_to_json(image_info: dict, json_file_path: str) -> None:
    '''Save image_info dictionart to a JSON file'''
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(image_info, f, ensure_ascii=False, indent=4)
        print(f"Image info successfully saved to {json_file_path}")
    except Exception as e:
        print(f"Error saving image info to JSON: {e}")

def main_complete_walk_root(image_folder: str) -> dict:
    ''' walks through the root folder and returns a dictionary with the image information'''
    image_info = {}
    for root, dirs, files in os.walk(image_folder):
        image_files = [f for f in files if f.lower().endswith('.jpg')]
        for image_name in image_files:
            try:
                image_path = os.path.join(root, image_name)
                _image_info = get_comments_info(image_path=image_path)
                location = _image_info['location']
                if location in image_info:
                    # If location exists, append the new info to the list
                    image_info[location].append(_image_info)
                else:
                    # If location does not exist, create a new list with the info
                    image_info[location] = [_image_info]
            except Exception as e:
                print(f"{image_path} failed to parse due to {e}")
    return image_info

def dict_to_excel(deteriorated_data: dict, excel_path: str)->None:
    ''' Converts a dicto of image information associated with a deffect to an excel file'''

    # Initialize a list to hold the flattened data
    flat_data = []

    # Iterate through each entry in the provided dictionary
    for key, value in deteriorated_data.items():
        entry_data = {
            'location': value['location'],
            'description': value['description'],
            'latitude': value['latitude'],
            'longitude': value['longitude'],
        }

        # Add image data, which creates a new column for each photo
        for image_key, image_path in value['images'].items():
            # Create a unique key for each photo (e.g., photo1, photo2, etc.)
            photo_column_name = f'photo{image_key}'
            entry_data[photo_column_name] = image_path

        # Append the flattened entry data to the list
        flat_data.append(entry_data)

    # Convert the list of flat data to a pandas DataFrame
    df = pd.DataFrame(flat_data)

    # Write the DataFrame to an Excel file at the specified path
    df.to_excel(excel_path, index=False)

    print(f'Data successfully written to {excel_path}')

def create_info_dict(base_path: str) -> dict:
    '''Create a dictionary with image information
    Note: This function only works with folder with 1 subfolder level
    first ensure the folder has the right format using root_walk function and 
    move_images_to_folders functions'''

    final_dict = {}
    subfolders = [f.path for f in os.scandir(base_path) if f.is_dir()]
    for folder_path in subfolders:
        folder_name = os.path.basename(folder_path)
        images = [os.path.join(folder_path, img) for img in os.listdir(folder_path) if img.upper().endswith('.JPG')]
        description_key = folder_name.split()[-1]  # Use last word in folder name to distinguish keys
        for image_path in images:
            info = get_comments_info(image_path)
            if info:
                base_key = info['location']
                full_key = f"{base_key}.{description_key}"
                if full_key not in final_dict:
                    final_dict[full_key] = {'location': info['location'], 'description': info['description'],
                                            'latitude': info['latitude'], 'longitude': info['longitude'], 'images': {}}
                img_count = len(final_dict[full_key]['images']) + 1
                final_dict[full_key]['images'][str(img_count)] = info['path']
    return final_dict

def sort_by_defect(source:str, destination:str) -> None:
    '''
    This function load all images from a folder that ONLY has 1 level of subfolders and performs two
    operations:
    1. Renames the subfolders with a conuter, this allows to have a unique name for each subfolder
    2. Moves the subfolders to a new destination folder

    THe output folder will be use to manually select defects that belong category and create and excelfile 
    using the create_excel_from_folder function
    '''
    # Define the source and destination directories
    source_dir = source
    destination_dir = destination

    # Ensure the destination directory exists
    os.makedirs(destination_dir, exist_ok=True)

    # Initialize a counter
    counter = 1

    # Iterate over each first-level directory
    for first_level in os.listdir(source_dir):
        first_level_path = os.path.join(source_dir, first_level)
        if os.path.isdir(first_level_path):
            # Iterate over each second-level directory
            for second_level in os.listdir(first_level_path):
                second_level_path = os.path.join(first_level_path, second_level)
                if os.path.isdir(second_level_path):
                    # Construct the new name with a counter
                    new_second_level_name = f"{second_level} {counter}"
                    # Increment the counter
                    counter += 1
                    # Construct destination path for the second-level directory with the new name
                    destination_second_level_path = os.path.join(destination_dir, new_second_level_name)
                    # Move and rename the second-level directory
                    shutil.move(second_level_path, destination_second_level_path)
                    print(f"Moved and renamed '{second_level}' to '{new_second_level_name}' at '{destination_dir}'")

    print("All specified second-level directories have been moved and renamed successfully.")

def load_json(json_path):
    '''Load a JSON file and return the contents as a dictionary'''
    with open(json_path, 'r') as f:
        output_json = json.load(f)
    return output_json

def create_excel_from_folder(defect_class:str , folder_direction:str)->any:
    '''Creates an excel file from a folder with images, this function is used when the users creates
    a subfolder with a deffect class'''
    sort_dict = create_info_dict(folder_direction)
    json_file_path = f"sort_dict_{defect_class}.json"
    save_image_info_to_json(image_info =  sort_dict, json_file_path = json_file_path)
    json2dict = load_json(json_file_path)
    dict_to_excel(json2dict,f'{defect_class}.xlsx')

#%% Section to run the files 
if __name__ == '__main__': 

    info_dict = main_complete_walk_root('STR11')
    save_image_info_to_json(image_info = info_dict ,json_file_path= "STR11_info_dict.json")
    move_images_to_folders(info_dict, 'First_Sort')
    sort_by_defect('First_Sort','STR11_sorted_defects') 
    
    #Mannualy copy the the corrosion folder from STR11_sorted_defects to Corrosion 

    sorted_dict_corrosion = create_info_dict(r"Corrosion")
    save_image_info_to_json(image_info = sorted_dict_corrosion ,
                            json_file_path= "STR11_Corrosion.json")
    dict_to_excel(sorted_dict_corrosion,'Corrosion.xlsx')


