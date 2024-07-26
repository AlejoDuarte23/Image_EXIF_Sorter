

from create_images_folders import (main_complete_walk_root,
                                      save_image_info_to_json,
                                      move_images_to_folders,
                                      sort_by_defect,
                                      create_info_dict,
                                      dict_to_excel)





info_dict = main_complete_walk_root('STR11')
save_image_info_to_json(image_info = info_dict ,json_file_path= "STR11_info_dict.json")
move_images_to_folders(info_dict, 'First_Sort')
sort_by_defect('First_Sort','STR11_sorted_defects') 

#Mannualy copy the the corrosion folder from STR11_sorted_defects to Corrosion 

sorted_dict_corrosion = create_info_dict(r"Corrosion")
save_image_info_to_json(image_info = sorted_dict_corrosion ,
                        json_file_path= "STR11_Corrosion.json")
dict_to_excel(sorted_dict_corrosion,'Corrosion.xlsx')
