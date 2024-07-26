# STR11 Image Processing Project

This project processes images from the STR11 dataset, sorts them by defects, and exports the information to JSON and Excel formats.

## Instructions

1. **Download and extract the STR11.zip file**:
   - Download the file from the following link: [STR11.zip](https://drive.google.com/file/d/1yMk2RoYU1pK2jOYphvsUKoS_Z1X3TN1q/view?usp=drive_link)
   - Extract the contents of the ZIP file.

2. **Place the STR11 folder**:
   - Place the extracted STR11 folder in the same directory as this repository.

3. **Create a new file called `example.py`**:
   - Create a new file named `example.py` in the same directory as this repository.

4. **Add the following code to `example.py`**:

   1. **Import necessary functions**:
      ```python
      from create_images_folders import (
          main_complete_walk_root,
          save_image_info_to_json,
          move_images_to_folders,
          sort_by_defect,
          create_info_dict,
          dict_to_excel
      )
      ```

   2. **Process the STR11 dataset and generate the initial JSON file**:
      ```python
      # Process the STR11 dataset and generate necessary files
      info_dict = main_complete_walk_root('STR11')
      save_image_info_to_json(image_info=info_dict, json_file_path="STR11_info_dict.json")
      ```

   3. **Move images to folders based on the initial sort**:
      ```python
      move_images_to_folders(info_dict, 'First_Sort')
      ```

   4. **Sort images by defect type**:
      ```python
      sort_by_defect('First_Sort', 'STR11_sorted_defects')
      ```

   5. **Manually copy the corrosion folder from `STR11_sorted_defects` to `Corrosion`**:
      - Perform this step manually after running the above code.

   6. **Create an information dictionary for the corrosion images**:
      ```python
      sorted_dict_corrosion = create_info_dict(r"Corrosion")
      ```

   7. **Save the corrosion information to a JSON file**:
      ```python
      save_image_info_to_json(image_info=sorted_dict_corrosion, json_file_path="STR11_Corrosion.json")
      ```

   8. **Export the corrosion information to an Excel file**:
      ```python
      dict_to_excel(sorted_dict_corrosion, 'Corrosion.xlsx')
      ```


## Notes

- Ensure you have the `create_images_folders` module available in the same directory as your script.
- After running the script, manually copy the `corrosion` folder from `STR11_sorted_defects` to `Corrosion` before running the final processing steps.

## Requirements

- Python 3.x
- Pip install requirements.txt.
