import json

PETROLEUM_PROPERTIES_TEMPLATES = {
    "Inputs": {
        "Areas": "s",
        "Total thickness": "h",
        "Reservoir thickness": "hef",
        "Porosity": "poro",
        "Oil saturation": "s_o",
        "Water saturation": "s_w",
        "Net-to-gross": "ntg",
        "Formation volume factor": "fvf",
        "Expansion factor": "ef",
        "Oil density": "den",
        "Geometric correction factor": "geomf",
        "Top depth": "top_depth",
        "Bottom depth": "bottom_depth",
        "Oil-water contact": "owc",
        "Gas-water contact": "gwc"
    },
    "Results": {"Total hydrocarbons in-place": "s*hef*poro*s_o*ef*den"},
}

with open('PetroGeoSim/templates/en.json', "w", encoding='utf8') as fp:
    json.dump(PETROLEUM_PROPERTIES_TEMPLATES, fp=fp, indent=4, ensure_ascii=False)
    
PETROLEUM_PROPERTIES_TEMPLATES_RU = {
    "Inputs": {
        "Площадь": "s",
        "Общая мощность": "h",
        "Эффективная мощность": "hef",
        "Пористость": "poro",
        "Нефтенасыщенность": "s_o",
        "Водонасыщенность": "s_w",
        "Коэффициент песчанистости": "ntg",
        "Объемный коэффициент": "fvf",
        "Коэффициент расширения": "ef",
        "Плотность нефти": "den",
        "Геометрический фактор": "geomf",
        "Кровля пласта": "top_depth",
        "Подошва пласта": "bottom_depth",
        "ВНК": "owc",
        "ГНК": "gwc"
        },
    "Results": {
        "Геологические запасы нефти": "s*hef*poro*s_o*ef*den"
    },
}

with open("PetroGeoSim/templates/ru.json", "w", encoding='utf8') as fp:
    json.dump(PETROLEUM_PROPERTIES_TEMPLATES_RU, fp=fp, indent=4, ensure_ascii=False)