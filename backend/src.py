from fastapi import HTTPException
import json
import math
from PIL import Image, ImageDraw
import random

#----------------------------------------------
def load_airport_data(filename):
    with  open(filename, 'r') as f:
        data = json.load(f)
    return data

AIRPORTS = load_airport_data('airports.json')
AIRPORT_IDS = load_airport_data('airport_ids.json')
AIRPORT_IDS_KEYS = list(AIRPORT_IDS.keys())
RADIUS = 6371
EMISSION = 0.1

#----------------------------------------------

def get_airport_info(icao):
    try:
        return AIRPORTS[icao]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"{icao} is not a valid IOCA")

def get_airport_matches(airport_search, only_major=False):
    airport_matches = [item for item in AIRPORT_IDS_KEYS if item.lower().startswith(airport_search.lower())]
    airport_icaos = {}
    for match in airport_matches:
        for icao in AIRPORT_IDS[match]:
            if icao not in airport_icaos:
                iata = AIRPORTS[icao]['iata']
                if only_major == True:
                    if len(iata)>0:
                        airport_icaos[icao] = {'matched': [match], 'iata': iata}
                else:
                    airport_icaos[icao]= {'matched': [match], 'iata': iata}
            else:
                airport_icaos[icao]['matched'].append(match)
    if not airport_icaos:
        raise HTTPException(
            status_code=400,
            detail=f"{airport_search} did not match any known airport"
        )
    return airport_icaos
#----------------------------------------------
 
def calculate_distance(lon1, lat1, lon2, lat2):
    dlon = math.radians(lon2 - lon1)
    dlat = math.radians(lat2 - lat1)
    a = math.sin(dlat / 2) ** 2  + math.sin(dlon / 2) ** 2 * math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) 
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = RADIUS * c 
    return distance

#----------------------------------------------

def make_flight(date, dep, arr):
    '''
    Infer data from one flight key
    '''
    ai1 = get_airport_info(dep)
    ai2 = get_airport_info(arr)
    distance_km = calculate_distance(ai1['lon'], ai1['lat'], ai2['lon'], ai2['lat'])
    if ai1['country'] == ai2['country']:
        flight_type = "domestic"
    else:
        flight_type = "international"
    flight_emissions_co2_kg = distance_km * EMISSION
    return {"INFO": { 
                    "CO2 [kg]": int(flight_emissions_co2_kg),
                    "Distance [km]": int(distance_km), 
                    "Type": flight_type,
                    "Date": date}, 
                "DEPARTURE": ai1, 
                "ARRIVAL": ai2}

def make_history(s_history):
    '''
    Infer data for the history
    '''
    history = {"FLIGHTS": {}, "ORDER": s_history}
    for key in history["ORDER"]:
        date, dep, arr= split_key(key)
        history["FLIGHTS"][key] = make_flight(date, dep, arr)
    history["STATS"] = {"Number of flights": len(history["ORDER"]),
                        "Total CO2 [kg]": sum([history["FLIGHTS"][key]["INFO"]["CO2 [kg]"] for key in history["ORDER"]]),
                        "Total Distance [km]": sum([history["FLIGHTS"][key]["INFO"]["Distance [km]"] for key in history["ORDER"]])}
    return history

def build_key(date, dep, arr):
    '''
    Build a flight key
    '''
    _=get_airport_info(dep)
    _=get_airport_info(arr)
    return f"{date.strftime('%Y-%m-%d')}_{dep}_{arr}"

def split_key(key):
    '''
    Split a key
    '''
    date, dep, arr = key.split("_")
    return date, dep, arr

#----------------------------------------------


def generate_tree_canopy(width, height, theme):
    # Ensure theme is between 0 and 1
    theme = max(0, min(1, theme))
    
    # Create a new image with a green base for the healthy forest
    img = Image.new('RGB', (width, height), color=(0, 128, 0))  # Green background
    draw = ImageDraw.Draw(img)
    
    # Color scaling based on the theme (0 = greenish, 1 = reddish)
    def get_patch_color(x, y):
        if random.random() < theme:  # As theme increases, more red patches appear
            # Base colors for burning forest (red, orange, yellow)
            r_base = int(255 * theme)  # Red increases as theme approaches 1
            g_base = int(255 * (1 - theme))  # Green decreases as theme approaches 1
            b_base = int(50 + 100 * (1 - theme))  # Blue stays somewhat in the middle

            # Introduce small random variations to make the patches look more natural
            r_variation = random.randint(-30, 30)
            g_variation = random.randint(-30, 30)
            b_variation = random.randint(-30, 30)
            
            # Apply variations to the base color and clamp to valid RGB range
            r = max(0, min(255, r_base + r_variation))
            g = max(0, min(255, g_base + g_variation))
            b = max(0, min(255, b_base + b_variation))
            
            return (r, g, b)
        else:
            # Base color for healthy (greenish)
            r_base = 0  # Red stays low
            g_base = 128  # Green stays constant for healthy leaves
            b_base = 0  # Blue stays low

            # Introduce random variation to make the green look more natural
            r_variation = random.randint(-20, 20)
            g_variation = random.randint(-20, 20)
            b_variation = random.randint(-20, 20)
            
            # Apply variations to the base color and clamp to valid RGB range
            r = max(0, min(255, r_base + r_variation))
            g = max(0, min(255, g_base + g_variation))
            b = max(0, min(255, b_base + b_variation))
            
            return (r, g, b)
    
    # Randomly place rectangular patches of leaves in the image
    patch_width = 30  # Width of each patch (in pixels)
    patch_height = 10  # Height of each patch (in pixels)
    patch_density = 0.1  # Density of patches (can be adjusted)

    # More red patches as theme increases
    for _ in range(int(width * height * patch_density)):
        # Random position for the top-left corner of the patch
        x = random.randint(0, width - patch_width)
        y = random.randint(0, height - patch_height)
        
        # Get the color for the current patch
        color = get_patch_color(x, y)
        
        # Draw the rectangular patch
        draw.rectangle([(x, y), (x + patch_width, y + patch_height)], fill=color)
    
    # Save or return the image
    # img.show()  # Display the image
    return img

# Example usage
