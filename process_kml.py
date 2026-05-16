import xml.etree.ElementTree as ET
import sys
import datetime

def process_kml(input_file, output_file):
    """
    Minifies a Garmin inReach KML feed for the frontend.
    The feed contains a detailed track (LineString) and a Point placemark 
    for every tracking update. Each Point placemark has a huge ExtendedData block.
    This script removes all Point placemarks except the latest one, drastically
    reducing file size while preserving the historical track line and the most 
    recent telemetry data needed by the dashboard.
    """
    namespaces = {
        '': 'http://www.opengis.net/kml/2.2',
        'gx': 'http://www.google.com/kml/ext/2.2',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'xsd': 'http://www.w3.org/2001/XMLSchema'
    }
    # Register namespaces to preserve them cleanly in the output
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)
        
    tree = ET.parse(input_file)
    root = tree.getroot()
    ns = {'kml': 'http://www.opengis.net/kml/2.2'}
    
    folders = root.findall('.//kml:Folder', ns)
    
    def haversine_nm(lon1, lat1, lon2, lat2):
        import math
        R = 3440.065 # Radius of earth in nautical miles
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi/2.0)**2 + math.cos(phi1)*math.cos(phi2) * math.sin(delta_lambda/2.0)**2
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1-a)))

    for folder in folders:
        placemarks = folder.findall('kml:Placemark', ns)
        
        point_placemarks = []
        parsed_points = []
        
        for pm in placemarks:
            pt = pm.find('kml:Point', ns)
            if pt is not None:
                point_placemarks.append(pm)
                time_node = pm.find('.//kml:TimeStamp/kml:when', ns)
                coords_node = pt.find('kml:coordinates', ns)
                if time_node is not None and time_node.text and coords_node is not None and coords_node.text:
                    try:
                        t_str = time_node.text.replace('Z', '+00:00')
                        t = datetime.datetime.fromisoformat(t_str)
                        coords = coords_node.text.strip().split(',')
                        if len(coords) >= 2:
                            parsed_points.append({
                                'pm': pm,
                                'time': t,
                                'lon': float(coords[0]),
                                'lat': float(coords[1])
                            })
                    except ValueError:
                        pass
        
        if not parsed_points:
            continue
            
        # Sort points chronologically
        parsed_points.sort(key=lambda x: x['time'])
        latest_point = parsed_points[-1]
        latest_point_pm = latest_point['pm']
        latest_time = latest_point['time']
        
        def calc_avg_speed(window_hours):
            target_time = latest_time - datetime.timedelta(hours=window_hours)
            distance = 0.0
            for i in range(len(parsed_points)-1, 0, -1):
                p1 = parsed_points[i]
                p2 = parsed_points[i-1]
                distance += haversine_nm(p1['lon'], p1['lat'], p2['lon'], p2['lat'])
                if p2['time'] <= target_time:
                    time_diff_hours = (latest_time - p2['time']).total_seconds() / 3600.0
                    return distance / time_diff_hours if time_diff_hours > 0 else None
            # If we didn't reach the target time, use whatever history we have
            time_diff_hours = (latest_time - parsed_points[0]['time']).total_seconds() / 3600.0
            # Only return a valid average if we have at least 10% of the requested window to avoid misleading data
            if time_diff_hours > (window_hours * 0.1):
                return distance / time_diff_hours
            return None

        speed_1hr = calc_avg_speed(1)
        speed_24hr = calc_avg_speed(24)
        
        # Inject the new calculated data into the latest point's ExtendedData
        extended_data = latest_point_pm.find('kml:ExtendedData', ns)
        if extended_data is None:
            extended_data = ET.SubElement(latest_point_pm, 'ExtendedData')
            
        if speed_1hr is not None:
            data_1hr = ET.SubElement(extended_data, 'Data', {'name': 'Speed 1hr'})
            val_1hr = ET.SubElement(data_1hr, 'value')
            val_1hr.text = f"{speed_1hr:.1f} kn"
            
        if speed_24hr is not None:
            data_24hr = ET.SubElement(extended_data, 'Data', {'name': 'Speed 24hr'})
            val_24hr = ET.SubElement(data_24hr, 'value')
            val_24hr.text = f"{speed_24hr:.1f} kn"
        
        # Remove all point placemarks, then add back only the latest
        for pm in point_placemarks:
            folder.remove(pm)
        folder.append(latest_point_pm)

    tree.write(output_file, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python process_kml.py <input.kml> <output.kml>")
        sys.exit(1)
    process_kml(sys.argv[1], sys.argv[2])
