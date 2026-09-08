# Script to validate IFC properties directly (Simple Check).
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. Upload an IFC file.
# 2. Run check_properties(...) with validation rules.

# Install dependencies if not present
# !pip install ifcopenshell pandas

import ifcopenshell
import ifcopenshell.util.element
import pandas as pd
import os
import sys

# --- CONFIG ---
DEFAULT_IFC_PATH = "minimal.ifc" # Default for Colab

def check_properties(ifc_class="IfcBuildingElement", required_properties=None, ifc_path=DEFAULT_IFC_PATH):
    """
    Validates if elements of a specific class have required properties.
    required_properties: Dictionary of {Pset_Name: [Prop1, Prop2]}
    
    Example:
    {
        "Pset_WallCommon": ["IsExternal", "LoadBearing"],
        "Qto_WallBaseQuantities": ["NetVolume"]
    }
    """
    
    if not required_properties:
        print("No validation rules provided.")
        return pd.DataFrame()

    if not os.path.exists(ifc_path):
        print(f"Error: File {ifc_path} not found.")
        return pd.DataFrame()

    print(f"Loading {ifc_path}...")
    ifc_file = ifcopenshell.open(ifc_path)
    
    print(f"Validating {ifc_class} against rules: {required_properties}...")
    
    elements = ifc_file.by_type(ifc_class)
    if not elements:
        print(f"No elements found of type {ifc_class}.")
        return pd.DataFrame()
        
    results = []
    
    for el in elements:
        name = el.Name if el.Name else "Unnamed"
        guid = el.GlobalId
        
        # Get all properties flattened or grouped
        # This function returns a dict: { "Pset_Name": { "PropName": Value, ... }, ... }
        psets = ifcopenshell.util.element.get_psets(el)
        
        for pset_req, props_req in required_properties.items():
            # Check if Pset exists
            if pset_req not in psets:
                results.append({
                    "GlobalId": guid,
                    "Name": name,
                    "Type": el.is_a(),
                    "Status": "FAIL",
                    "Missing Pset": pset_req,
                    "Missing Property": "ALL"
                })
                continue
                
            # Check if Properties exist within the Pset
            existing_props = psets[pset_req]
            for prop_req in props_req:
                if prop_req not in existing_props:
                    results.append({
                        "GlobalId": guid,
                        "Name": name,
                        "Type": el.is_a(),
                        "Status": "FAIL",
                        "Missing Pset": pset_req,
                        "Missing Property": prop_req
                    })
                else:
                    # Optional: Check value (not implemented in simple check)
                    pass
                    
    if not results:
        print("Validation Passed! All elements meet requirements.")
        return pd.DataFrame()
        
    df = pd.DataFrame(results)
    print(f"Found {len(df)} violations.")
    return df

# --- Colab Helper ---
if __name__ == "__main__":
    pass
