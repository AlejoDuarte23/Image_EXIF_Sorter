import os 
import json 
import shutil

from PIL import Image


def get_decimal_from_dms(dms, ref):
    degrees, minutes, seconds = dms
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    if ref in ['S', 'W']:
        decimal = -decimal
    return decimal

def get_comments_info(image_path:str)->dict:
    # 37510 is the field where the comment are stored
    #  b'ASCII\x00\x00\x00Intermediate Pump Station Balance Tank, North Access Stairs'
    with Image.open(image_path) as img:
        info = img._getexif()

        decoded_string = info[37510].decode('ascii')
        cleaned_string = decoded_string.replace('ASCII', '').replace('\x00', '').strip()
        parts = cleaned_string.split(',', 1)
        location = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else ''  # Ensure description is empty if no comma

        
        date = info[36867]

        gps_info = info.get(34853)
        if gps_info:
            latitude = get_decimal_from_dms(gps_info[2], gps_info[1])
            longitude = get_decimal_from_dms(gps_info[4], gps_info[3])
        else:
            latitude, longitude = None, None  # Default to None if GPS info is not present
        return {
            'location': location,
            'description': description,
            'date': date,
            'latitude': latitude,
            'longitude': longitude,
            'path':image_path
        }
    
def main(image_folder: str) -> dict:
    image_info = {}
    image_files = [f for f in os.listdir(image_folder) if f.endswith('.JPG')]
    for image_name in image_files:
        try:
            image_path = os.path.join(image_folder, image_name)
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

def move_images_to_folders(image_info: dict, base_folder: str) -> None:

 for location, info_list in image_info.items():
        # Sanitize the location string to avoid issues with invalid folder names
        folder_name = sanitize_folder_name(location)
        location_folder = os.path.join(base_folder, folder_name)
        
        # Ensure the location folder exists
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

def sanitize_folder_name(name: str) -> str:

    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name


def save_image_info_to_json(image_info: dict, json_file_path: str) -> None:

    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(image_info, f, ensure_ascii=False, indent=4)
        print(f"Image info successfully saved to {json_file_path}")
    except Exception as e:
        print(f"Error saving image info to JSON: {e}")



# %% Runn the hole thing !
# where the folder will be created 
base_folder =  r"E:\example_maria"
# root folder for the images 
# image_folder= r"C:\Users\aleja\Documents\drive-download-20240215T231704Z-001"
image_folder= r"E:\alex_pictures_examples" 

image_info = main(image_folder=image_folder)
move_images_to_folders(image_info, base_folder)

json_file_path = r"C:\Users\aleja\Documents\image_info2.json"


#  save json file 
save_image_info_to_json(image_info, json_file_path)


# %%



