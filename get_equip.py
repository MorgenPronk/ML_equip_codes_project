import pandas as pd

def get_equip_format(xl_path: str, equip_num: int):
    df = pd.read_excel(xl_path)
    equipment_data = df[df['Equipment Number'] == equip_num].to_dict()
    print(equipment_data)