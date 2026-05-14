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
    
    for folder in folders:
        placemarks = folder.findall('kml:Placemark', ns)
        
        point_placemarks = []
        latest_time = None
        latest_point_pm = None
        
        for pm in placemarks:
            if pm.find('kml:Point', ns) is not None:
                point_placemarks.append(pm)
                time_node = pm.find('.//kml:TimeStamp/kml:when', ns)
                if time_node is not None and time_node.text:
                    try:
                        # Convert "2026-05-14T10:59:00Z" to "+00:00" for parsing
                        t_str = time_node.text.replace('Z', '+00:00')
                        t = datetime.datetime.fromisoformat(t_str)
                        if latest_time is None or t > latest_time:
                            latest_time = t
                            latest_point_pm = pm
                    except ValueError:
                        pass
        
        # Remove all point placemarks, then add back only the latest
        if point_placemarks and latest_point_pm is not None:
            for pm in point_placemarks:
                folder.remove(pm)
            folder.append(latest_point_pm)

    tree.write(output_file, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python process_kml.py <input.kml> <output.kml>")
        sys.exit(1)
    process_kml(sys.argv[1], sys.argv[2])
