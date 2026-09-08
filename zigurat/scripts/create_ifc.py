# Script to create a minimal IFC4 file.
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. Run the function create_minimal_ifc(target_path="filename.ifc")

import os
import sys

# Minimal IFC4 Content
# This string represents a valid SPF (STEP Physical File) structure.
# Key sections:
# - HEADER: Meta-information (Schema, File Name, View Definition).
# - DATA: The actual IFC entities.
#   - IfcProject (#1): The root of the project structure.
#   - IfcOwnerHistory (#2): Tracks who created the object and when.
#   - IfcGeometricRepresentationContext (#3): Defines the 3D coordinate system (Precision, Dimension).
#   - IfcUnitAssignment (#4): Assigns global units (Meter, Second, etc.).
MINIMAL_IFC_CONTENT = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('minimal.ifc','2025-01-01T00:00:00',(''),(''),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('0jABC_0000000000000000',#2,'MinimalProject',$,$,$,$,(#3),#4);
#2=IFCOWNERHISTORY(#5,#6,$,.ADDED.,$,$,$,1234567890);
#3=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.0E-5,#7,$);
#4=IFCUNITASSIGNMENT((#8,#9,#10,#11));
#5=IFCPERSON($,'User',$,$,$,$,$,$);
#6=IFCORGANIZATION($,'Organization',$,$,$);
#7=IFCAXIS2PLACEMENT3D(#12,$,$);
#8=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#9=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
#10=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
#11=IFCSIUNIT(*,.TIMEUNIT.,$,.SECOND.);
#12=IFCCARTESIANPOINT((0.,0.,0.));
ENDSEC;
END-ISO-10303-21;
"""

def create_minimal_ifc(target_path="minimal.ifc"):
    """
    Creates a minimal IFC file at the specified path.
    """
    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(os.path.abspath(target_path))
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(MINIMAL_IFC_CONTENT)
        
        print(f"Success: IFC file created at: {os.path.abspath(target_path)}")
        return target_path
        
    except Exception as e:
        print(f"Error creating IFC file: {e}")
        return None

if __name__ == "__main__":
    # If run as script
    input_path = sys.argv[1] if len(sys.argv) > 1 else "minimal.ifc"
    create_minimal_ifc(input_path)
