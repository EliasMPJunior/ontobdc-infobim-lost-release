# Script to list chambers (Caixas/PVs) from an IFC file.
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. Upload an IFC file.
# 2. Run the function list_chambers(...)

# Install dependencies if not present
# !pip install ifcopenshell pandas

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.geom
import sys
import os
import pandas as pd

# --- CONFIG ---
DEFAULT_IFC_PATH = "minimal.ifc" # Default for Colab

def get_dimensions(element, settings):
    """
    Calculates the Bounding Box dimensions (LxW and Depth) from geometry.
    
    This function uses 'ifcopenshell.geom.create_shape' to generate the mesh 
    of the element, then iterates through vertices to find min/max coordinates.
    """
    try:
        # Create a geometry object (mesh)
        shape = ifcopenshell.geom.create_shape(settings, element)
        verts = shape.geometry.verts
        # Group flat list of floats into (x,y,z) tuples
        points = [verts[i:i+3] for i in range(0, len(verts), 3)]
        
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        zs = [p[2] for p in points]
        
        dx = max(xs) - min(xs)
        dy = max(ys) - min(ys)
        dz = max(zs) - min(zs)
        
        dims = f"{dx:.2f}x{dy:.2f}"
        depth = f"{dz:.2f}"
        
        return dims, depth
    except:
        return "-", "-"

def get_material_name(element):
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
    return "-"

def list_chambers(ifc_path=DEFAULT_IFC_PATH):
    
    if not os.path.exists(ifc_path):
        print(f"Error: File {ifc_path} not found.")
        return pd.DataFrame()

    print(f"Loading {ifc_path}...")
    ifc_file = ifcopenshell.open(ifc_path)
    
    chambers = []
    
    # Configure geometry settings for dimension calculation
    # USE_WORLD_COORDS ensures vertices are in global coordinates
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    
    print("Extracting chamber data...")
    
    # Broad search for chambers using multiple potential classes
    candidates = []
    candidates.extend(ifc_file.by_type("IfcDistributionChamberElement"))
    candidates.extend(ifc_file.by_type("IfcBuildingElementProxy"))
    candidates.extend(ifc_file.by_type("IfcWasteTerminal"))
    
    for el in candidates:
        is_chamber = False
        if el.is_a("IfcDistributionChamberElement"):
            is_chamber = True
        elif el.is_a("IfcBuildingElementProxy"):
            # For Proxies, we check the Name for keywords like "Caixa", "PV", "CX"
            name = el.Name.lower() if el.Name else ""
            if any(k in name for k in ["caixa", "pv", "poço", "inspeção", "ralo", "cx"]):
                is_chamber = True
        elif el.is_a("IfcWasteTerminal"):
             name = el.Name.lower() if el.Name else ""
             if any(k in name for k in ["caixa", "ralo"]):
                 is_chamber = True
                 
        if is_chamber:
            dims, depth = get_dimensions(el, settings)
            mat = get_material_name(el)
            type_str = el.ObjectType if el.ObjectType else el.is_a()
            
            chambers.append({
                "GlobalId": el.GlobalId,
                "Name": el.Name if el.Name else "Unnamed",
                "Dimensions": dims,
                "Depth": depth,
                "Material": mat,
                "Type": type_str
            })
    
    df = pd.DataFrame(chambers)
    if not df.empty:
        df = df.sort_values(by="Name")
        
    print(f"Total: {len(chambers)} chambers found.")
    return df

# --- Colab Helper ---
if __name__ == "__main__":
    # df = list_chambers()
    # print(df)
    pass
