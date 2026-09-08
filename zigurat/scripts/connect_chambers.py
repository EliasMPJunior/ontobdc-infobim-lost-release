# Script to connect two IfcDistributionChamberElements with an IfcPipeSegment.
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. Upload an IFC file.
# 2. Run the function connect_chambers(...)

# Install dependencies if not present
# !pip install ifcopenshell numpy

import sys
import os
import math
import uuid
import time
import ifcopenshell
import ifcopenshell.api
import ifcopenshell.util.placement
import ifcopenshell.util.selector
import numpy as np

# Default settings
DEFAULT_PIPE_DIAMETER = 0.15  # 150mm
DEFAULT_FILE_PATH = "minimal.ifc" # Default for Colab

def create_guid():
    """Generates a compressed GUID (Global Unique Identifier) required by IFC."""
    return ifcopenshell.guid.compress(uuid.uuid1().hex)

def world_to_local(element, world_point):
    """
    Transforms a point from World Coordinates to Element Local Coordinates.
    
    Why: IFC relationships (like Ports) are defined relative to the element they belong to.
    We know where we want to connect in the World (e.g., face center), but we need to tell
    the element where that is in its own local space.
    """
    # Get the 4x4 Transformation Matrix of the element (Local -> World)
    placement_matrix = ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement)
    
    # Invert the matrix to get (World -> Local)
    inv_matrix = np.linalg.inv(placement_matrix)
    
    # Point to homogeneous coordinates (x, y, z, 1) for matrix multiplication
    wp = np.append(np.array(world_point), 1.0)
    
    # Apply transformation
    lp = np.dot(inv_matrix, wp)
    
    # Return x, y, z
    return tuple(lp[:3])

def connect_ports(ifc_file, port_source, port_sink):
    """
    Connects two ports using IfcRelConnectsPorts.
    This creates a logical flow connection in the IFC model.
    """
    ifc_file.createIfcRelConnectsPorts(
        create_guid(),
        None,
        "Port Connection",
        None,
        port_source, # RelatingPort (Flow Out)
        port_sink,   # RelatedPort (Flow In)
        None
    )

def get_geometry_center_and_dimensions(element):
    """
    Calculates the geometric center of the element in WORLD coordinates.
    This handles the complexity of nested placements and extrusions.
    """
    # Default values
    center_world = np.array([0.0, 0.0, 0.0])
    dims = (1.0, 1.0, 1.0)
    
    # Get Element Placement Matrix (Local -> World)
    placement_matrix = ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement)
    
    if element.Representation:
        for rep in element.Representation.Representations:
            for item in rep.Items:
                if item.is_a("IfcExtrudedAreaSolid"):
                    # 1. Get Profile Dimensions
                    profile = item.SweptArea
                    x_dim = 0.0
                    y_dim = 0.0
                    if profile.is_a("IfcRectangleProfileDef"):
                        x_dim = profile.XDim
                        y_dim = profile.YDim
                    elif profile.is_a("IfcCircleProfileDef"):
                        x_dim = profile.Radius * 2
                        y_dim = profile.Radius * 2
                    
                    # 2. Get Extrusion Vector
                    depth = item.Depth
                    direction = item.ExtrudedDirection.DirectionRatios
                    
                    vec = np.array(direction)
                    norm = np.linalg.norm(vec)
                    if norm > 0:
                        vec = vec / norm
                    
                    extrusion_vec = vec * depth
                    z_dim = abs(depth) 
                    
                    # 3. Get Solid Position (Local to Element)
                    solid_pos_matrix = ifcopenshell.util.placement.get_axis2placement(item.Position)
                    
                    # 4. Calculate Center in Solid Local System (Midpoint of extrusion)
                    center_solid_local = np.array([0.0, 0.0, 0.0]) + (extrusion_vec / 2.0)
                    
                    # 5. Transform to Element Local System
                    p_solid = np.append(center_solid_local, 1.0)
                    p_element = np.dot(solid_pos_matrix, p_solid)
                    
                    # 6. Transform to World System
                    p_world = np.dot(placement_matrix, p_element)
                    
                    center_world = p_world[:3]
                    dims = (x_dim, y_dim, z_dim)
                    
                    return center_world, dims

    # Fallback if no geometry found
    p_origin = np.array([0.0, 0.0, 0.0, 1.0])
    p_world = np.dot(placement_matrix, p_origin)
    return p_world[:3], dims

def get_face_center(center_pos, dimensions, face_direction):
    """
    Calculates the center point of a specific face (N, S, E, W).
    """
    cx, cy, cz = center_pos
    dx, dy, dz = dimensions
    
    if face_direction == 'E': # +X
        return (cx + dx/2.0, cy, cz)
    elif face_direction == 'W': # -X
        return (cx - dx/2.0, cy, cz)
    elif face_direction == 'N': # +Y
        return (cx, cy + dy/2.0, cz)
    elif face_direction == 'S': # -Y
        return (cx, cy - dy/2.0, cz)
    
    return (cx, cy, cz)


def create_port(ifc_file, element, name, flow_direction, relative_placement_point):
    """
    Creates an IfcDistributionPort on the element.
    """
    # Port Placement
    pt_coords = tuple(float(x) for x in relative_placement_point)
    pt = ifc_file.createIfcCartesianPoint(pt_coords)
    axis = ifc_file.createIfcDirection((0.0, 0.0, 1.0))
    ref = ifc_file.createIfcDirection((1.0, 0.0, 0.0))
    
    # Placement relative to the element
    placement = ifc_file.createIfcLocalPlacement(element.ObjectPlacement, ifc_file.createIfcAxis2Placement3D(pt, axis, ref))
    
    port = ifc_file.createIfcDistributionPort(
        create_guid(),
        None,
        name,
        None,
        None,
        placement,
        None,
        flow_direction # FlowDirection (SOURCE/SINK)
    )
    
    # Handle Schema differences
    if ifc_file.schema == "IFC4":
        port.PredefinedType = "PIPE" 
        # IfcRelNests: Element nests Port
        ifc_file.createIfcRelNests(create_guid(), None, "Port Nesting", None, element, [port])
    else:
        # IFC2x3 compatibility
        ifc_file.createIfcRelConnectsPortToElement(create_guid(), None, "Port Connection", None, port, element)
        
    return port

def create_pipe(ifc_file, p1, p2, diameter, name):
    """
    Creates a Pipe Segment connecting two 3D points.
    Includes geometry creation (swept solid) and ports.
    """
    print(f"Creating pipe from {p1} to {p2}...")
    
    p1 = tuple(float(x) for x in p1)
    p2 = tuple(float(x) for x in p2)
    
    # 1. Create geometric points
    pt1 = ifc_file.createIfcCartesianPoint(p1)
    # pt2 is used for calculation but not directly for placement origin
    
    # 2. Calculate Pipe Vector and Length
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    dz = p2[2] - p1[2]
    length = math.sqrt(dx*dx + dy*dy + dz*dz)
    
    if length < 1e-6:
        print("Error: Distance too short")
        return None, None, None
        
    # Normalized Axis Vector
    axis_vec = (dx/length, dy/length, dz/length)
    
    # Calculate Reference Vector (must be orthogonal to axis)
    # Simple logic: if axis is mostly vertical, use X as ref. Else use Z.
    if abs(axis_vec[2]) < 0.9:
        ref_vec = (0.0, 0.0, 1.0)
    else:
        ref_vec = (1.0, 0.0, 0.0)
        
    axis = ifc_file.createIfcDirection(axis_vec)
    ref = ifc_file.createIfcDirection(ref_vec)
    
    # Placement of the Pipe Element
    placement = ifc_file.createIfcAxis2Placement3D(pt1, axis, ref)
    
    # 3. Create Geometry (ExtrudedAreaSolid)
    # Profile
    profile = ifc_file.createIfcCircleProfileDef("AREA", None, None, diameter/2.0)
    
    # Extrusion Direction
    # IMPORTANT: In the pipe's local coordinate system, the axis IS the Z-axis (0,0,1).
    extrusion_dir = ifc_file.createIfcDirection((0.0, 0.0, 1.0))
    
    solid_pos = ifc_file.createIfcAxis2Placement3D(ifc_file.createIfcCartesianPoint((0.0,0.0,0.0)))
    solid = ifc_file.createIfcExtrudedAreaSolid(profile, solid_pos, extrusion_dir, length)
    
    # 4. Shape Representation
    contexts = ifc_file.by_type("IfcGeometricRepresentationContext")
    if contexts:
        context = contexts[0]
    else:
        print("Warning: No Geometric Context found, pipe geometry might be invalid.")
        return None, None, None

    rep = ifc_file.createIfcShapeRepresentation(context, "Body", "SweptSolid", [solid])
    product_def_shape = ifc_file.createIfcProductDefinitionShape(None, None, [rep])
    
    # 5. Create Element
    local_placement = ifc_file.createIfcLocalPlacement(None, placement)
    
    pipe = ifc_file.createIfcPipeSegment(create_guid(), None, name, None, "PipeSegment", local_placement, product_def_shape, None)
    
    # Create Ports (Start/End)
    # Start: 0,0,0 relative to pipe
    port_start = create_port(ifc_file, pipe, "Montante", "SINK", (0.0, 0.0, 0.0))
    # End: 0,0,Length relative to pipe (along Z axis which is the pipe axis)
    port_end = create_port(ifc_file, pipe, "Jusante", "SOURCE", (0.0, 0.0, length))
    
    return pipe, port_start, port_end

def execute_connect_chambers(ifc_file, source_id, target_id, diameter=DEFAULT_PIPE_DIAMETER):
    """
    Main logic to connect two elements.
    1. Finds elements.
    2. Determines connection points (faces).
    3. Creates pipe.
    4. Links everything.
    """
    
    # Find elements
    source = None
    target = None
    
    def find_element(eid):
        try:
            el = ifc_file.by_id(eid)
            if el: return el
        except: pass
        
        try:
            el = ifc_file.by_guid(eid)
            if el: return el
        except: pass
        
        for el_type in ["IfcDistributionChamberElement", "IfcBuildingElementProxy", "IfcWasteTerminal"]:
            for el in ifc_file.by_type(el_type):
                if el.GlobalId == eid or el.Name == eid:
                    return el
        return None

    source = find_element(source_id)
    target = find_element(target_id)
    
    if not source:
        print(f"Source element '{source_id}' not found.")
        return None
    if not target:
        print(f"Target element '{target_id}' not found.")
        return None

    print(f"Connecting {source.Name} ({source.GlobalId}) -> {target.Name} ({target.GlobalId})")
    
    # Calculate Geometry Centers
    pos1, dim1 = get_geometry_center_and_dimensions(source)
    pos2, dim2 = get_geometry_center_and_dimensions(target)
    
    # Determine best faces to connect
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    
    face1 = ''
    face2 = ''
    
    # Simple Heuristic: If delta X is bigger, connect East-West. Else North-South.
    if abs(dx) > abs(dy):
        if dx > 0:
            face1 = 'E'; face2 = 'W'
        else:
            face1 = 'W'; face2 = 'E'
    else:
        if dy > 0:
            face1 = 'N'; face2 = 'S'
        else:
            face1 = 'S'; face2 = 'N'
            
    p1 = get_face_center(pos1, dim1, face1)
    p2 = get_face_center(pos2, dim2, face2)
    
    # Create Pipe
    pipe_name = f"{source.Name} -> {target.Name}"
    pipe, port_pipe_in, port_pipe_out = create_pipe(ifc_file, p1, p2, diameter, pipe_name)
    
    if pipe:
        # Add to Spatial Container (same as source)
        if source.ContainedInStructure:
            rel = source.ContainedInStructure[0]
            rel.RelatedElements = list(rel.RelatedElements) + [pipe]
        
        # Add Logical Connections (IfcRelConnectsElements)
        # This tells BIM software that these elements are physically connected
        ifc_file.createIfcRelConnectsElements(create_guid(), None, "Connection", None, None, source, pipe)
        ifc_file.createIfcRelConnectsElements(create_guid(), None, "Connection", None, None, pipe, target)
        
        # Connect Ports (Flow Topology)
        print("Connecting ports...")
        
        # Source (Out) -> Pipe (In)
        p1_local = world_to_local(source, p1)
        port_source = create_port(ifc_file, source, "Saida", "SOURCE", p1_local)
        connect_ports(ifc_file, port_source, port_pipe_in)
        
        # Pipe (Out) -> Target (In)
        p2_local = world_to_local(target, p2)
        port_target = create_port(ifc_file, target, "Entrada", "SINK", p2_local)
        connect_ports(ifc_file, port_pipe_out, port_target)
        
        print(f"Pipe created: {pipe.GlobalId}")
        return pipe
    
    return None

# --- Colab Helper ---
def run_example_connect(filename="minimal.ifc"):
    if not os.path.exists(filename):
        print(f"File {filename} not found. Please create it first (e.g., using create_ifc.py).")
        return

    f = ifcopenshell.open(filename)
    
    # Try to find existing proxies/chambers
    elements = f.by_type("IfcBuildingElementProxy")
    if len(elements) < 2:
        print("Need at least 2 elements to connect. Create them first (e.g. using create_extruded_element.py)")
        return
        
    source = elements[0]
    target = elements[1]
    
    execute_connect_chambers(f, source.GlobalId, target.GlobalId)
    
    f.write(filename)
    print(f"Saved updated file to {filename}")

if __name__ == "__main__":
    # If run as script, can be used to test
    # run_example_connect()
    pass
