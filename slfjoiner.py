import sys
import os
from datetime import datetime
from lxml import etree
import copy
import uuid

FIELDS = [
    "altitudeDifferencesDownhill", "altitudeDifferencesUphill", "averageHeartrate", "averageSpeed",
    "averageTemperature", "calories", "distance", "exerciseTime", "manualTemperature",
    "maximumAltitude", "maximumHeartrate", "maximumIncline", "maximumSpeed", "maximumTemperature",
    "minimumAltitude", "minimumHeartrate", "minimumIncline", "minimumTemperature", "pauseTime",
    "score", "timeInIntensityZone1", "timeInIntensityZone2", "timeInIntensityZone3",
    "timeInIntensityZone4", "timeUnderIntensityZone", "trainingTime", "zoneTargetMaxHeartRate",
    "averageCadenceCalc", "averagePowerCalc", "startDate"
]
DATE_FORMAT = "%a %b %d %H:%M:%S GMT%z %Y"

def print_help():
    print("usage: python slfjoiner.py <input1.slf> <input2.slf> <output.slf>")
    print("Both input files must be valid SLF files. The output file will be created.")

def parse_files(file1_path, file2_path):
    try:
        file1 = etree.parse(file1_path)
        file2 = etree.parse(file2_path)
        return file1.getroot(), file2.getroot()
    except Exception as e:
        print(f"Error reading input file : {e}")
        print_help()
        sys.exit(1)

def extract_general_info(root, fields):
    data = {}
    for field in fields:
        elem = root.find(f'./GeneralInformation/{field}')
        data[field] = elem.text if elem is not None else None
    return data

def merge_general_info(dataOne, dataTwo, fields):
    dataOut = {}
    start1 = datetime.strptime(dataOne["startDate"], DATE_FORMAT)
    start2 = datetime.strptime(dataTwo["startDate"], DATE_FORMAT)
    for field in fields:
        if dataOne[field] is not None and dataTwo[field] is not None:
            if field in [ "averageHeartrate", "averageTemperature", "averageCadenceCalc", "averagePowerCalc", "manualTemperature", "zoneTargetMaxHeartRate" ]:
                dataOut[field] = int(round((float(dataOne[field]) + float(dataTwo[field])) / 2))
            elif field in ["averageSpeed"]:
                dataOut[field] = round((float(dataOne[field]) + float(dataTwo[field])) / 2, 3)
            elif field in ["maximumHeartrate", "maximumTemperature", "maximumAltitude", "maximumIncline"]:
                dataOut[field] = max(int(dataOne[field]), int(dataTwo[field]))
            elif field in ["maximumSpeed"]:
                dataOut[field] = round(max(float(dataOne[field]), float(dataTwo[field])), 3)
            elif field in ["minimumSpeed", "minimumHeartrate", "minimumTemperature", "minimumAltitude", "minimumIncline"]:
                dataOut[field] = min(int(dataOne[field]), int(dataTwo[field]))
            elif field in ["startDate"]:
                dataOut[field] = start1.strftime(DATE_FORMAT) if start1 < start2 else start2.strftime(DATE_FORMAT)
            elif field in [ "altitudeDifferencesDownhill", "altitudeDifferencesUphill", "calories", "exerciseTime", "pauseTime", "score", "timeInIntensityZone1", "timeInIntensityZone2", "timeInIntensityZone3", "timeInIntensityZone4", "timeUnderIntensityZone", "trainingTime" ]:
                dataOut[field] = int(dataOne[field]) + int(dataTwo[field])
            else:
                dataOut[field] = (float(dataOne[field]) + float(dataTwo[field]))
        elif dataOne[field] is not None:
            dataOut[field] = dataOne[field]
        elif dataTwo[field] is not None:
            dataOut[field] = dataTwo[field]
        else:
            dataOut[field] = None
    return dataOut, start1, start2

def update_general_info(rootOut, dataOut, fields):
    for field in fields:
        elem = rootOut.find(f'./GeneralInformation/{field}')
        if elem is not None:
            elem.text = str(dataOut[field]) if dataOut[field] is not None else None

def merge_entries_and_markers(rootOut, firstRoot, secondRoot, firstData, secondData, dataOut, firstIsEarlier):
    # Entries zusammenführen
    rootOut.append(firstRoot.find('./Entries'))
    timeToAdd = None
    distToAdd = None
    for entry in rootOut.findall('./Entries/Entry'):
        t = int(entry.get('trainingTimeAbsolute', '0'))
        d = float(entry.get('distanceAbsolute', '0'))
        timeToAdd = t if timeToAdd is None or t > timeToAdd else timeToAdd
        distToAdd = d if distToAdd is None or d > distToAdd else distToAdd
    for e in secondRoot.findall('./Entries/Entry'):
        new_entry = copy.deepcopy(e)
        new_entry.set('distanceAbsolute', str(round(float(e.get('distanceAbsolute', '0')) + distToAdd, 1)))
        new_entry.set('trainingTimeAbsolute', str(int(e.get('trainingTimeAbsolute', '0')) + timeToAdd))
        rootOut.find('./Entries').append(new_entry)
    # Markers zusammenführen
    rootOut.append(firstRoot.find('./Markers'))
    totallap = rootOut.find('./Markers/Marker[@type="l"]')
    finallap = secondRoot.find('./Markers/Marker[@type="l"]')
    maxNumber = None
    for marker in rootOut.findall('./Markers/Marker'):
        n = int(marker.get('number', '0'))
        maxNumber = n if maxNumber is None or n > maxNumber else maxNumber
    if totallap is not None:
        update_totallap(totallap, finallap, dataOut)
    for m in secondRoot.findall('./Markers/Marker'):
        if m.get('type') != 'l':
            new_marker = copy.deepcopy(m)
            new_marker.set('distanceAbsolute', str(float(new_marker.get('distanceAbsolute', '0')) + float(firstData["distance"])))
            new_marker.set('timeAbsolute', str(float(new_marker.get('timeAbsolute', '0')) + float(firstData["trainingTime"])))
            new_marker.set('number', str(maxNumber + int(new_marker.get('number', '0'))))
            rootOut.find('./Markers').append(new_marker)

def update_totallap(totallap, finallap, dataOut):
    totallap.set('altitudeDownhill', str(dataOut["altitudeDifferencesDownhill"]))
    totallap.set('altitudeUphill', str(dataOut["altitudeDifferencesUphill"]))
    totallap.set('averageCadence', str(dataOut["averageCadenceCalc"]))
    totallap.set('averageHeartrate', str(dataOut["averageHeartrate"]))
    totallap.set('averagePower', str(dataOut["averagePowerCalc"]))
    totallap.set('averageSpeed', str(dataOut["averageSpeed"]))
    totallap.set('calories', str(dataOut["calories"]))
    totallap.set('distance', str(dataOut["distance"]))
    totallap.set('distanceAbsolute', str(dataOut["distance"]))
    totallap.set('maximumAltitude', str(dataOut["maximumAltitude"]))
    totallap.set('maximumHeartrate', str(dataOut["maximumHeartrate"]))
    totallap.set('maximumSpeed', str(dataOut["maximumSpeed"]))
    totallap.set('minimumHeartrate', str(dataOut["minimumHeartrate"]))
    totallap.set('time', str(dataOut["trainingTime"]))
    totallap.set('timeAbsolute', str(dataOut["trainingTime"]))
    totallap.set('latitude', finallap.get('latitude', '0'))
    totallap.set('longitude', finallap.get('longitude', '0'))
    totallap.set('endTime', finallap.get('endTime', '0'))

def fix_average_speed(rootOut):
    total_distance = 0.0
    total_time = 0
    for marker in rootOut.findall('./Markers/Marker[@type="al"]'):
        distance = float(marker.get('distance', '0'))
        time = int(marker.get('time', '0'))
        total_distance += distance
        total_time += time
    if total_time > 0:
        average_speed = round(total_distance / (total_time / 100), 3) 
    else:
        average_speed = 0.0
    rootOut.find('./GeneralInformation/averageSpeed').text = str(average_speed)
    rootOut.find('./Markers/Marker[@type="l"]').set('averageSpeed', str(average_speed))


def finalize_and_write(rootOut, root2, output_filename):
    rootOut.find('./GeneralInformation/GUID').text = str(uuid.uuid4())
    name_elem = rootOut.find('./GeneralInformation/name')
    name_text = f"{name_elem.text} + {root2.find('./GeneralInformation/name').text} joined"
    name_elem.text = etree.CDATA(name_text)
    etree.ElementTree(rootOut).write(output_filename, encoding='utf-8', xml_declaration=True, pretty_print=True)

def main():
    if len(sys.argv) != 4:
        print_help()
        sys.exit(1)
    file1_path = sys.argv[1]
    file2_path = sys.argv[2]
    output_filename = sys.argv[3]
    if not os.path.isfile(file1_path) or not os.path.isfile(file2_path):
        print("one or both input files does not exist.")
        print_help()
        sys.exit(1)
    root1, root2 = parse_files(file1_path, file2_path)
    rootOut = copy.deepcopy(root1)
    for f in [ './Entries', './Markers' ]:
        rootOut.remove(rootOut.find(f))
    dataOne = extract_general_info(root1, FIELDS)
    dataTwo = extract_general_info(root2, FIELDS)
    dataOut, start1, start2 = merge_general_info(dataOne, dataTwo, FIELDS)
    update_general_info(rootOut, dataOut, FIELDS)
    # Nur noch eine Funktion für beide Richtungen
    if start1 < start2:
        merge_entries_and_markers(rootOut, root1, root2, dataOne, dataTwo, dataOut, True)
    else:
        merge_entries_and_markers(rootOut, root2, root1, dataTwo, dataOne, dataOut, False)
    fix_average_speed(rootOut)
    finalize_and_write(rootOut, root2 if start1 < start2 else root1, output_filename)

if __name__ == "__main__":
    main()

