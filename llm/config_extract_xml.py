# Import the xml module
import xml.etree.ElementTree as ET

# Read the hadoop core-default.xml file as a string
with open('tmp.xml', 'r') as f:
    xml_string = f.read()

# Strip the comments and spaces from the xml string
xml_string = ET.tostring(ET.fromstring(xml_string), encoding='unicode')

# Parse the xml string
tree = ET.ElementTree(ET.fromstring(xml_string))

# Get the root element
root = tree.getroot()

# Iterate through all the property elements
for prop in root.findall('property'):
    # Get the name and description elements
    name = prop.find('name')
    description = prop.find('description')

    if name != None and description != None:
        # Print the name and description text
        print(f'Name: {name.text}')
        print(f'Description: {description.text}')
        print()
