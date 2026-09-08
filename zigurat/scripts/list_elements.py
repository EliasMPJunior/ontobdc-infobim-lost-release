# Script to list generic IFC elements by Class.
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. Upload an IFC file.
# 2. Run list_elements(ifc_class="IfcWall") or any other class.

# Install dependencies if not present
# !pip install ifcopenshell pandas

import ifcopenshell
import ifcopenshell.util.element
import sys
import os
import pandas as pd

# --- CONFIG ---
DEFAULT_IFC_PATH = "minimal.ifc" # Default for Colab

def get_basic_properties(element):
    """
    Extracts basic properties like Name, Description, Tag, ObjectType.
    
    In IFC, every object (IfcRoot) has attributes like:
    - GlobalId: A unique 22-character string.
    - Name: A human-readable name.
    - Description: Additional text description.
    - ObjectType: Specifies the type definition.
    - Tag: An external identifier (e.g., from the authoring tool).
    """
    props = {
        "GlobalId": element.GlobalId,
        "Name": element.Name if element.Name else "-",
        "Description": element.Description if element.Description else "-",
        "ObjectType": element.ObjectType if hasattr(element, "ObjectType") and element.ObjectType else "-",
        "Tag": element.Tag if hasattr(element, "Tag") and element.Tag else "-"
    }
    return props

def get_quantities(element):
    """
    Tries to extract common quantities (Area, Volume, Length) from Qto_*
    
    'ifcopenshell.util.element.get_psets(element, qtos_only=True)' is a helper
    that retrieves all Quantity Sets (Qto) assigned to the element.
    Standard quantities often include 'NetVolume', 'GrossArea', etc.
    """
    qtos = {}
    psets = ifcopenshell.util.element.get_psets(element, qtos_only=True)
    
    # Flatten Qto dict
    for pset_name, props in psets.items():
        for name, value in props.items():
            # Common quantity names
            if name in ["Area", "GrossArea", "NetArea", "Volume", "GrossVolume", "NetVolume", "Length", "Height", "Width"]:
                key = f"{name}" 
                # If duplicate, append pset name? usually not needed for simple list
                qtos[key] = value
                
    return qtos

def get_material_name(element):
    """
    Retrieves the material name associated with the element.
    
    Materials in IFC can be associated in different ways:
    1. IfcMaterial: A single material.
    2. IfcMaterialList: A list of materials (e.g., composite element).
    3. IfcMaterialLayerSetUsage: For layered elements like walls (Core, Finish, etc.).
    4. IfcMaterialProfileSetUsage: For profile-based elements like beams/columns.
    """
    mat = ifcopenshell.util.element.get_material(element)
    if not mat:
        return "-"
    if mat.is_a("IfcMaterial"):
        return mat.Name
    if mat.is_a("IfcMaterialList"):
        return ", ".join([m.Name for m in mat.Materials])
    if mat.is_a("IfcMaterialLayerSetUsage"):
        if mat.ForLayerSet and mat.ForLayerSet.MaterialLayers:
             return ", ".join([l.Material.Name for l in mat.ForLayerSet.MaterialLayers if l.Material])
    if mat.is_a("IfcMaterialProfileSetUsage"):
        if mat.ForProfileSet and mat.ForProfileSet.MaterialProfiles:
             return ", ".join([p.Material.Name for p in mat.ForProfileSet.MaterialProfiles if p.Material])
    return "-"

def list_elements(ifc_class="IfcBuildingElement", ifc_path=DEFAULT_IFC_PATH):
    """
    Lists all elements of a specific IFC class (e.g., IfcWall, IfcWindow, IfcBuildingElementProxy).
    Returns a pandas DataFrame.
    """
    
    if not os.path.exists(ifc_path):
        print(f"Error: File {ifc_path} not found.")
        return pd.DataFrame()

    print(f"Loading {ifc_path}...")
    try:
        # Open the IFC file using IfcOpenShell
        ifc_file = ifcopenshell.open(ifc_path)
    except Exception as e:
        print(f"Error opening file: {e}")
        return pd.DataFrame()
    
    print(f"Searching for elements of type: {ifc_class}...")
    
    try:
        # 'by_type' returns all instances of the specified class (and subclasses).
        elements = ifc_file.by_type(ifc_class)
    except:
        print(f"Invalid IFC Class: {ifc_class}")
        return pd.DataFrame()
    
    if not elements:
        print(f"No elements found of type {ifc_class}.")
        return pd.DataFrame()
        
    data = []
    
    print(f"Processing {len(elements)} elements...")
    
    for el in elements:
        # 1. Basic Props
        row = get_basic_properties(el)
        
        # 2. Material
        row["Material"] = get_material_name(el)
        
        # 3. Quantities (Optional - adds columns dynamically)
        # qtos = get_quantities(el)
        # row.update(qtos)
        
        # 4. Class specific info (e.g. PredefinedType)
        if hasattr(el, "PredefinedType"):
            row["PredefinedType"] = el.PredefinedType
            
        data.append(row)
            
    df = pd.DataFrame(data)
    
    # Reorder columns for better readability
    cols = ["GlobalId", "Name", "ObjectType", "Material", "PredefinedType", "Description", "Tag"]
    # Filter only existing columns
    cols = [c for c in cols if c in df.columns]
    # Add remaining columns (like Quantities)
    remaining = [c for c in df.columns if c not in cols]
    
    df = df[cols + remaining]
    
    if not df.empty:
        df = df.sort_values(by="Name")
        
    print(f"Found {len(df)} elements.")
    return df

# --- Colab Helper ---
if __name__ == "__main__":
    # Example usage:
    # df = list_elements("IfcWall")
    # print(df.head())
    pass
