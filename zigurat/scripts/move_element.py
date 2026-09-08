# Script to move an IFC element (Relative Translation).
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. Upload an IFC file.
# 2. Run the function move_element(...)

# Install dependencies if not present
# !pip install ifcopenshell

import ifcopenshell
import sys
import os

# --- CONFIG ---
DEFAULT_FILE_PATH = "minimal.ifc" # Default for Colab

def move_element(global_id, x_offset, y_offset, z_offset, ifc_path=DEFAULT_FILE_PATH):
    """
    Moves an element by a relative offset (x, y, z).
    
    This function modifies the 'ObjectPlacement' of the element.
    It specifically looks for 'RelativePlacement' (IfcAxis2Placement3D)
    and updates its 'Location' coordinates.
    """
    
    if not os.path.exists(ifc_path):
        print(f"Error: File {ifc_path} not found.")
        return

    print(f"Loading {ifc_path}...")
    ifc = ifcopenshell.open(ifc_path)
    
    print(f"Searching for element: {global_id}...")
    
    element = None
    try:
        element = ifc.by_guid(global_id)
    except Exception:
        # Fallback search by Name or GlobalId scan if standard by_guid fails or input is not guid
        for e in ifc.by_type("IfcRoot"):
            if e.GlobalId == global_id or e.Name == global_id:
                element = e
                break
        
    if not element:
        print(f"Error: Element {global_id} not found.")
        return
        
    print(f"Found: {element.Name} ({element.is_a()})")
    
    if not hasattr(element, "ObjectPlacement") or not element.ObjectPlacement:
        print("Error: Element has no ObjectPlacement.")
        return
        
    placement = element.ObjectPlacement
    
    # Handle different placement types
    # IfcLocalPlacement defines position relative to another item (PlacementRelTo)
    if not placement.is_a("IfcLocalPlacement"):
        print(f"Error: ObjectPlacement is not IfcLocalPlacement (got {placement.is_a()}).")
        return
        
    rel_placement = placement.RelativePlacement
    
    # IfcAxis2Placement3D defines Location, Axis (Z), and RefDirection (X)
    if not rel_placement.is_a("IfcAxis2Placement3D"):
        print(f"Error: RelativePlacement is not IfcAxis2Placement3D (got {rel_placement.is_a()}).")
        return
        
    location = rel_placement.Location
    x, y, z = location.Coordinates
    
    new_x = x + float(x_offset)
    new_y = y + float(y_offset)
    new_z = z + float(z_offset)
    
    print(f"Moving from ({x:.2f}, {y:.2f}, {z:.2f}) to ({new_x:.2f}, {new_y:.2f}, {new_z:.2f})")
    
    # Update coordinates tuple
    location.Coordinates = (new_x, new_y, new_z)
            
    print(f"Saving to {ifc_path}...")
    ifc.write(ifc_path)
    print("Done.")

# --- Colab Helper ---
if __name__ == "__main__":
    pass
