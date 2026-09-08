# Script to list pipes from an IFC file.
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. Upload an IFC file.
# 2. Run the function list_pipes(...)

# Install dependencies if not present
# !pip install ifcopenshell pandas numpy

import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.unit
import sys
import os
import math
import pandas as pd
import numpy as np

# --- CONFIG ---
DEFAULT_IFC_PATH = "minimal.ifc" # Default for Colab

def get_material_name(element):
    """
    Retrieves the material name associated with the element.
    Checks 'HasAssociations' for 'IfcRelAssociatesMaterial'.
    """
    if hasattr(element, "HasAssociations"):
        for rel in element.HasAssociations:
            if rel.is_a("IfcRelAssociatesMaterial"):
                mat = rel.RelatingMaterial
                if mat.is_a("IfcMaterial"):
                    return mat.Name
                elif mat.is_a("IfcMaterialLayerSetUsage"):
                    return "LayerSet" 
                elif mat.is_a("IfcMaterialProfileSetUsage"):
                    return "ProfileSet"
    return "-"

def get_geometry_info(element):
    """
    Calculates geometric information (Length, Z start/end, Slope) for a pipe.
    
    It first tries to find the 'Length' property in 'Qto_DistributionElement'.
    If not found, or to calculate slope, it analyzes the geometry representation.
    """
    length = 0.0
    psets = ifcopenshell.util.element.get_psets(element)
    
    # 1. Try to get length from Property Sets (standard quantity)
    if "Qto_DistributionElement" in psets and "Length" in psets["Qto_DistributionElement"]:
         length = float(psets["Qto_DistributionElement"]["Length"])
    
    start_z = 0.0
    end_z = 0.0
    slope = 0.0
    
    try:
        # Get the 4x4 transformation matrix for the element's local placement
        # This converts local coordinates to world coordinates.
        m = ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement)
        
        axis_rep = None
        body_rep = None
        
        # IFC elements can have multiple representations (e.g., 'Axis' for centerline, 'Body' for 3D shape)
        if element.Representation:
            for rep in element.Representation.Representations:
                if rep.RepresentationIdentifier == "Axis":
                    axis_rep = rep
                elif rep.RepresentationIdentifier == "Body":
                    body_rep = rep
        
        length_geom = 0.0
        z1 = 0.0
        z2 = 0.0
        found_geom = False
        
        # Method A: Use 'Axis' representation (Polyline) - Preferred for pipes
        if axis_rep and axis_rep.Items:
            item = axis_rep.Items[0]
            if item.is_a("IfcPolyline"):
                points = item.Points
                pt_start = points[0].Coordinates
                pt_end = points[-1].Coordinates
                
                def to_3d(pt):
                    return list(pt) + [0.0]*(3-len(pt))
                
                # Convert points to homogeneous coordinates (x, y, z, 1) for matrix multiplication
                v_start = to_3d(pt_start) + [1.0]
                v_end = to_3d(pt_end) + [1.0]
                
                # Apply transformation matrix to get World Coordinates
                w_start = m @ np.array(v_start)
                w_end = m @ np.array(v_end)
                
                z1 = w_start[2]
                z2 = w_end[2]
                length_geom = math.dist(w_start[:3], w_end[:3])
                
                # Calculate Slope (%)
                dist_2d = math.dist(w_start[:2], w_end[:2])
                if dist_2d > 0.001:
                    slope = abs(z1 - z2) / dist_2d * 100.0
                found_geom = True
                
        # Method B: Use 'Body' representation (ExtrudedAreaSolid) if 'Axis' is missing
        if not found_geom and body_rep and body_rep.Items:
            item = body_rep.Items[0]
            if item.is_a("IfcExtrudedAreaSolid"):
                placement = item.Position
                depth = item.Depth
                direction = item.ExtrudedDirection.DirectionRatios
                
                m_ext = ifcopenshell.util.placement.get_axis2placement(placement)
                m_combined = m @ m_ext
                
                v_start = [0.0, 0.0, 0.0, 1.0]
                w_start = m_combined @ np.array(v_start)
                
                d_vec = np.array(list(direction) + [0.0])
                d_norm = np.linalg.norm(d_vec[:3])
                if d_norm > 0:
                    d_vec = d_vec / d_norm
                
                rot_mat = m_combined[:3, :3]
                d_world = rot_mat @ d_vec[:3]
                
                w_end_3 = w_start[:3] + d_world * depth
                
                z1 = w_start[2]
                z2 = w_end_3[2]
                length_geom = depth
                
                dist_2d = math.dist(w_start[:2], w_end_3[:2])
                if dist_2d > 0.001:
                    slope = abs(z1 - z2) / dist_2d * 100.0
                found_geom = True

        if found_geom:
            if length == 0.0:
                length = length_geom
            return length, z1, z2, slope
        
        z1 = m[2, 3]
        return length, z1, 0.0, 0.0
                
    except Exception as e:
        # print(f"Error processing {element.Name}: {e}")
        pass
    
    return length, 0.0, 0.0, 0.0

def list_pipes(ifc_path=DEFAULT_IFC_PATH):
    
    if not os.path.exists(ifc_path):
        print(f"Error: File {ifc_path} not found.")
        return pd.DataFrame()

    print(f"Loading {ifc_path}...")
    ifc_file = ifcopenshell.open(ifc_path)
    
    unit_scale = ifcopenshell.util.unit.calculate_unit_scale(ifc_file)
    
    pipes = ifc_file.by_type("IfcPipeSegment")
    
    data = []
    
    print("Processing pipes...")
    for pipe in pipes:
        name = pipe.Name if pipe.Name else "Unnamed"
        
        psets = ifcopenshell.util.element.get_psets(pipe)
        
        dn = 0.0
        if "Pset_PipeSegmentTypeCommon" in psets and "NominalDiameter" in psets["Pset_PipeSegmentTypeCommon"]:
            dn_val = psets["Pset_PipeSegmentTypeCommon"]["NominalDiameter"]
            if dn_val:
                dn_float = float(dn_val)
                if dn_float < 5.0: 
                    dn = dn_float * 1000.0
                else:
                    dn = dn_float
        
        slope_uhc = 0.0
        if "Pset_BR_NBR8160" in psets and "MinimalSlope" in psets["Pset_BR_NBR8160"]:
            val = psets["Pset_BR_NBR8160"]["MinimalSlope"]
            if val: slope_uhc = float(val)
        
        material = get_material_name(pipe)
        
        length, z_start, z_end, slope_real = get_geometry_info(pipe)
        
        length_m = length * unit_scale
        z_start_m = z_start * unit_scale
        z_end_m = z_end * unit_scale
        
        data.append({
            "GlobalId": pipe.GlobalId,
            "Name": name,
            "DN (mm)": int(dn),
            "Slope UHC (%)": slope_uhc,
            "Material": material,
            "Start Z (m)": z_start_m,
            "End Z (m)": z_end_m,
            "Slope Real (%)": slope_real,
            "Length (m)": length_m
        })
            
    df = pd.DataFrame(data)
    if not df.empty:
        df = df.sort_values(by=["DN (mm)", "Name"], ascending=[False, True])
        
    print(f"Total: {len(pipes)} pipes found.")
    return df

# --- Colab Helper ---
if __name__ == "__main__":
    # df = list_pipes()
    # print(df)
    pass
