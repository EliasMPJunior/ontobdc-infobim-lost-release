# Script to inspect and filter IFC elements by Property Sets.
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. inspect_element(guid="...") -> Shows all properties
# 2. filter_elements(ifc_class="IfcWall", filters={"LoadBearing": True}) -> Returns matching elements

# Install dependencies if not present
# !pip install ifcopenshell pandas

import ifcopenshell
import ifcopenshell.util.element
import pandas as pd
import os
import sys
import json

# --- CONFIG ---
DEFAULT_IFC_PATH = "minimal.ifc" # Default for Colab

def inspect_element(guid_or_name, ifc_path=DEFAULT_IFC_PATH):
    """
    Prints ALL properties and quantities of a specific element.
    This is useful for debugging and understanding the data structure of an element.
    """
    if not os.path.exists(ifc_path):
        print(f"Error: File {ifc_path} not found.")
        return

    print(f"Loading {ifc_path}...")
    ifc_file = ifcopenshell.open(ifc_path)
    
    element = None
    try:
        element = ifc_file.by_guid(guid_or_name)
    except:
        # Try by Name or Type scan
        for e in ifc_file.by_type("IfcRoot"):
            if e.Name == guid_or_name or e.GlobalId == guid_or_name:
                element = e
                break
                
    if not element:
        print(f"Element '{guid_or_name}' not found.")
        return

    print(f"\n--- Inspection Report for: {element.Name} ({element.is_a()}) ---")
    print(f"GlobalId: {element.GlobalId}")
    
    # Get Psets using ifcopenshell utility
    # This automatically resolves IfcRelDefinesByProperties
    psets = ifcopenshell.util.element.get_psets(element)
    
    # Print formatted JSON
    print(json.dumps(psets, indent=4, default=str))
    
    return psets

def filter_elements(ifc_class="IfcBuildingElement", filters=None, ifc_path=DEFAULT_IFC_PATH):
    """
    Filters elements of a class based on property values.
    
    Arguments:
        ifc_class: The IFC class to search for (e.g. "IfcWall")
        filters: Dictionary of conditions.
                 Format: { "PropertyName": Value } or { "PsetName.PropertyName": Value }
                 
    Example:
        filter_elements("IfcWall", {"LoadBearing": True})
        filter_elements("IfcWindow", {"Pset_WindowCommon.IsExternal": True})
    """
    
    if not os.path.exists(ifc_path):
        print(f"Error: File {ifc_path} not found.")
        return pd.DataFrame()

    if not filters:
        print("No filters provided. Returning all elements.")
        pass

    print(f"Loading {ifc_path}...")
    ifc_file = ifcopenshell.open(ifc_path)
    
    elements = ifc_file.by_type(ifc_class)
    print(f"Scanning {len(elements)} elements of type {ifc_class}...")
    
    matches = []
    
    for el in elements:
        psets = ifcopenshell.util.element.get_psets(el)
        
        # Check all filters
        is_match = True
        if filters:
            for key, required_value in filters.items():
                found_prop = False
                
                # Handle "Pset.Prop" syntax (More specific)
                if "." in key:
                    pset_name, prop_name = key.split(".", 1)
                    if pset_name in psets and prop_name in psets[pset_name]:
                        actual_value = psets[pset_name][prop_name]
                        # Comparison (str conversion for safety)
                        if str(actual_value) == str(required_value):
                            found_prop = True
                else:
                    # Search in ALL psets (Loose matching)
                    for pset_name, props in psets.items():
                        if key in props:
                            actual_value = props[key]
                            if str(actual_value) == str(required_value):
                                found_prop = True
                                break
                
                if not found_prop:
                    is_match = False
                    break
        
        if is_match:
            matches.append({
                "GlobalId": el.GlobalId,
                "Name": el.Name,
                "Type": el.is_a(),
                "Matched Filters": str(filters)
            })
            
    df = pd.DataFrame(matches)
    print(f"Found {len(df)} matching elements.")
    return df

# --- Colab Helper ---
if __name__ == "__main__":
    pass
