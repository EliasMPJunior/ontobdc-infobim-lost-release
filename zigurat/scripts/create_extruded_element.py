# Script to create an extruded element (e.g., IfcBuildingElementProxy) at a specific position.
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. Upload an IFC file or use the default minimal one generated below.
# 2. Run the function create_extruded_element(...)

# Install dependencies if not present
# !pip install ifcopenshell

import sys
import os
import uuid
import ifcopenshell
import ifcopenshell.api

# Default settings for Colab
DEFAULT_WIDTH = 1.0
DEFAULT_LENGTH = 1.0
DEFAULT_IFC_CLASS = "IfcBuildingElementProxy"
DEFAULT_FILE_PATH = "minimal.ifc" # Default to local file in Colab

def create_guid():
    """Generates a compressed GUID (Global Unique Identifier) required by IFC."""
    return ifcopenshell.guid.compress(uuid.uuid1().hex)

def create_extruded_element(ifc_file, name, x, y, depth, width, length, ifc_class_name):
    """
    Creates a rectangular element extruded downwards.
    
    Step-by-step logic:
    1. Define WHERE the element is (Placement).
    2. Define WHAT the element looks like (Geometry/Representation).
    3. Create the element instance itself.
    4. Link the element to the spatial structure (e.g., Building Storey).
    """
    print(f"Creating '{name}' ({ifc_class_name}) at ({x}, {y}) with depth {depth}...")
    
    # --- 1. Create Placement (Location and Orientation) ---
    # In IFC, placement is defined by a point (Location) and two vectors (Axis and RefDirection).
    
    # Define the insertion point (x, y, 0)
    pt = ifc_file.createIfcCartesianPoint((float(x), float(y), 0.0))
    
    # Define Z-axis (Vertical direction, usually 0,0,1)
    axis = ifc_file.createIfcDirection((0.0, 0.0, 1.0))
    
    # Define X-axis reference (Rotation in plan, usually 1,0,0)
    ref = ifc_file.createIfcDirection((1.0, 0.0, 0.0))
    
    # Create the coordinate system (Axis2Placement3D)
    axis2placement = ifc_file.createIfcAxis2Placement3D(pt, axis, ref)
    
    # Create the Local Placement object (relative to world/absolute in this simple case)
    local_placement = ifc_file.createIfcLocalPlacement(None, axis2placement)
    
    # --- 2. Create Geometry (Body Representation) ---
    # We will use an "Extruded Area Solid" (Swept Solid).
    # This consists of a 2D Profile swept along a direction.
    
    # A. Define the 2D Profile (Rectangle) centered at local 0,0
    profile = ifc_file.createIfcRectangleProfileDef("AREA", None, None, float(width), float(length))
        
    # B. Define the Extrusion
    # Extrude DOWNWARDS (-Z) to represent depth/thickness (like a slab or footing)
    extrusion_dir = ifc_file.createIfcDirection((0.0, 0.0, -1.0))
    
    # The profile is placed at the origin of the element's coordinate system
    solid_pos = ifc_file.createIfcAxis2Placement3D(ifc_file.createIfcCartesianPoint((0.0, 0.0, 0.0)))
    
    # Create the 3D Solid
    solid = ifc_file.createIfcExtrudedAreaSolid(profile, solid_pos, extrusion_dir, float(depth))
    
    # C. Create the Shape Representation Container
    # We need a Geometric Representation Context (usually "Model" / "Body")
    context = None
    for ctx in ifc_file.by_type("IfcGeometricRepresentationContext"):
        if ctx.ContextType == "Model":
            context = ctx
            break
    if not context:
        # Fallback if file is empty
        if len(ifc_file.by_type("IfcGeometricRepresentationContext")) > 0:
            context = ifc_file.by_type("IfcGeometricRepresentationContext")[0]
        else:
             print("Warning: No IfcGeometricRepresentationContext found. Creating a basic one might fail if project structure is missing.")
             raise Exception("No IfcGeometricRepresentationContext found in file.")

    # Wrap the solid in a Representation Item
    rep = ifc_file.createIfcShapeRepresentation(context, "Body", "SweptSolid", [solid])
    
    # Link Representation to Product Definition Shape
    product_def_shape = ifc_file.createIfcProductDefinitionShape(None, None, [rep])
    
    # --- 3. Create Element Instance ---
    try:
        # Use create_entity to support dynamic class name (e.g. IfcWall, IfcColumn)
        element = ifc_file.create_entity(
            ifc_class_name,
            GlobalId=create_guid(), 
            Name=name,
            ObjectPlacement=local_placement,
            Representation=product_def_shape
        )
    except Exception as e:
        raise Exception(f"Failed to create class '{ifc_class_name}'. It might not exist or does not support geometry (ObjectPlacement/Representation). Error: {e}")

    # Double check if the created entity actually has Representation attribute
    if not hasattr(element, "Representation"):
         raise Exception(f"Class '{ifc_class_name}' does not support geometry (no Representation attribute).")

    # --- 4. Add to Spatial Structure ---
    # Elements must be contained in a spatial structure (e.g., IfcBuildingStorey) to appear in most viewers.
    
    structure = None
    storeys = ifc_file.by_type("IfcBuildingStorey")
    if storeys:
        structure = storeys[0]
    else:
        # Fallback: IfcSite or IfcProject
        sites = ifc_file.by_type("IfcSite")
        if sites:
            structure = sites[0]
        else:
            projs = ifc_file.by_type("IfcProject")
            if projs:
                structure = projs[0]

    if structure:
        # Check if a container relationship already exists
        rel = None
        for r in ifc_file.by_type("IfcRelContainedInSpatialStructure"):
            if r.RelatingStructure == structure:
                rel = r
                break
        
        if rel:
            # Add to existing relationship
            rel.RelatedElements = list(rel.RelatedElements) + [element]
        else:
            # Create new relationship: Structure -> Element
            ifc_file.createIfcRelContainedInSpatialStructure(create_guid(), None, "Building Storey Container", None, [element], structure)
            
    print(f"Created {ifc_class_name}: {element.GlobalId}")
    return element

# --- Colab Helper Function ---
def run_example_extrusion():
    """
    Creates a minimal IFC file (if missing) and adds an extruded element.
    """
    filename = "minimal_extrusion.ifc"
    
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
    create_extruded_element(
        ifc_file=ifc_file,
        name="PLACA-COLAB-01",
        x=2.0,
        y=3.0,
        depth=0.2, # 20cm thickness
        width=1.5,
        length=2.5,
        ifc_class_name="IfcBuildingElementProxy"
    )
    
    # Save
    ifc_file.write(filename)
    print(f"Saved updated file to {filename}")
    
    # Optional: Download in Colab
    # from google.colab import files
    # files.download(filename)

if __name__ == "__main__":
    # If running as script in Colab
    run_example_extrusion()
