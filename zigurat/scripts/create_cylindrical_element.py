# Script to create a cylindrical element (e.g., IfcBuildingElementProxy) at a specific position.
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. Upload an IFC file or use the default minimal one generated below.
# 2. Run the function create_cylindrical_element(...)

# Install dependencies if not present
# !pip install ifcopenshell

import sys
import os
import uuid
import ifcopenshell
import ifcopenshell.api

# Default settings for Colab
DEFAULT_RADIUS = 0.5
DEFAULT_IFC_CLASS = "IfcBuildingElementProxy"
DEFAULT_FILE_PATH = "minimal.ifc" # Default to local file in Colab

def create_guid():
    """Generates a compressed GUID (Global Unique Identifier) required by IFC."""
    return ifcopenshell.guid.compress(uuid.uuid1().hex)

def create_cylindrical_element(ifc_file, name, x, y, depth, radius, ifc_class_name):
    """
    Creates a cylindrical element extruded downwards.
    
    Logic Overview:
    1. Placement: Position the element in the world (X, Y, Z).
    2. Geometry: Define a circular profile and extrude it.
    3. Representation: Wrap the geometry in IFC representation entities.
    4. Product: Create the IFC Object (e.g. IfcColumn) and link everything.
    """
    print(f"Creating '{name}' ({ifc_class_name}) at ({x}, {y}) with depth {depth} and radius {radius}...")
    
    # --- 1. Create Placement ---
    # Define the insertion point (x, y, 0)
    pt = ifc_file.createIfcCartesianPoint((float(x), float(y), 0.0))
    
    # Define Z-axis (0,0,1)
    axis = ifc_file.createIfcDirection((0.0, 0.0, 1.0))
    
    # Define X-axis reference (1,0,0)
    ref = ifc_file.createIfcDirection((1.0, 0.0, 0.0))
    
    # Create coordinate system
    axis2placement = ifc_file.createIfcAxis2Placement3D(pt, axis, ref)
    local_placement = ifc_file.createIfcLocalPlacement(None, axis2placement)
    
    # --- 2. Create Geometry ---
    # A. Define the 2D Profile (Circle)
    # IfcCircleProfileDef is centered at 0,0 by default
    profile = ifc_file.createIfcCircleProfileDef("AREA", None, None, float(radius))
        
    # B. Define the Extrusion
    # Extrude DOWNWARDS (-Z)
    extrusion_dir = ifc_file.createIfcDirection((0.0, 0.0, -1.0))
    
    # Position of the profile within the element coordinate system
    solid_pos = ifc_file.createIfcAxis2Placement3D(ifc_file.createIfcCartesianPoint((0.0, 0.0, 0.0)))
    
    # Create the Solid
    solid = ifc_file.createIfcExtrudedAreaSolid(profile, solid_pos, extrusion_dir, float(depth))
    
    # C. Create Shape Representation
    context = None
    for ctx in ifc_file.by_type("IfcGeometricRepresentationContext"):
        if ctx.ContextType == "Model":
            context = ctx
            break
    if not context:
        # Fallback
        if len(ifc_file.by_type("IfcGeometricRepresentationContext")) > 0:
            context = ifc_file.by_type("IfcGeometricRepresentationContext")[0]
        else:
             print("Warning: No IfcGeometricRepresentationContext found.")
             raise Exception("No IfcGeometricRepresentationContext found in file.")

    rep = ifc_file.createIfcShapeRepresentation(context, "Body", "SweptSolid", [solid])
    product_def_shape = ifc_file.createIfcProductDefinitionShape(None, None, [rep])
    
    # --- 3. Create Element ---
    try:
        element = ifc_file.create_entity(
            ifc_class_name,
            GlobalId=create_guid(), 
            Name=name,
            ObjectPlacement=local_placement,
            Representation=product_def_shape
        )
    except Exception as e:
        raise Exception(f"Failed to create class '{ifc_class_name}'. Error: {e}")

    if not hasattr(element, "Representation"):
         raise Exception(f"Class '{ifc_class_name}' does not support geometry.")

    # --- 4. Add to Spatial Structure ---
    structure = None
    storeys = ifc_file.by_type("IfcBuildingStorey")
    if storeys:
        structure = storeys[0]
    else:
        sites = ifc_file.by_type("IfcSite")
        if sites:
            structure = sites[0]
        else:
            projs = ifc_file.by_type("IfcProject")
            if projs:
                structure = projs[0]

    if structure:
        rel = None
        for r in ifc_file.by_type("IfcRelContainedInSpatialStructure"):
            if r.RelatingStructure == structure:
                rel = r
                break
        
        if rel:
            rel.RelatedElements = list(rel.RelatedElements) + [element]
        else:
            ifc_file.createIfcRelContainedInSpatialStructure(create_guid(), None, "Building Storey Container", None, [element], structure)
            
    print(f"Created {ifc_class_name}: {element.GlobalId}")
    return element

# --- Colab Helper Function ---
def run_example_cylinder():
    """
    Creates a minimal IFC file (if missing) and adds a cylindrical element.
    """
    filename = "minimal_cylinder.ifc"
    
    # Check if file exists, if not create a minimal one
    if not os.path.exists(filename):
        print(f"Creating base file: {filename}")
        # Create a minimal IFC4 file in memory
        f = ifcopenshell.file(schema="IFC4")
        
        # Basic Project Structure
        org = f.createIfcOrganization()
        app = f.createIfcApplication(org, "1.0", "ColabApp", "ColabApp")
        owner_hist = f.createIfcOwnerHistory(f.createIfcPersonAndOrganization(f.createIfcPerson(), org), app, None, "ADDED", 1234567890)
        
        project = f.createIfcProject(create_guid(), owner_hist, "MinimalProject", None, None, None, None, None, f.createIfcUnitAssignment([]))
        
        # Context
        ctx = f.createIfcGeometricRepresentationContext(None, "Model", 3, 1.0E-5, f.createIfcAxis2Placement3D(f.createIfcCartesianPoint((0.,0.,0.))), None)
        project.RepresentationContexts = [ctx]
        
        f.write(filename)
    
    # Open and edit
    ifc_file = ifcopenshell.open(filename)
    
    # Add Element
    create_cylindrical_element(
        ifc_file=ifc_file,
        name="PILAR-COLAB-01",
        x=5.0,
        y=5.0,
        depth=3.0, # 3m height
        radius=0.3, # 30cm radius
        ifc_class_name="IfcColumn" # Example: Creating a Column
    )
    
    # Save
    ifc_file.write(filename)
    print(f"Saved updated file to {filename}")
    
    # Optional: Download in Colab
    # from google.colab import files
    # files.download(filename)

if __name__ == "__main__":
    # If running as script in Colab
    run_example_cylinder()
