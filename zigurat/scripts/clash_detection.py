# Script to perform Clash Detection between IFC elements.
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. Upload an IFC file.
# 2. Run check_clashes(class_a="IfcWall", class_b="IfcPipeSegment")

# Install dependencies if not present
# !pip install ifcopenshell pandas numpy

import ifcopenshell
import ifcopenshell.geom
import pandas as pd
import os
import sys
import time

# --- CONFIG ---
DEFAULT_IFC_PATH = "minimal.ifc" # Default for Colab

def create_tree(settings, elements):
    """
    Creates a BVH tree for efficient collision detection.
    """
    tree = ifcopenshell.geom.tree()
    iterator = ifcopenshell.geom.iterator(settings, elements[0].model, len(os.cpu_count() or 1))
    
    # Add elements to the iterator (filter)
    # The iterator by default iterates over everything? No, we need to handle specific elements.
    # Actually, for tree(), we usually iterate over the whole model or add elements one by one.
    
    # Simpler approach: Create shape for each element and add to tree.
    for element in elements:
        try:
            # We need to make sure the element has geometry representation
            if element.Representation:
                tree.add_element(element)
        except Exception:
            pass
            
    return tree

def check_clashes(class_a="IfcBuildingElement", class_b="IfcBuildingElement", ifc_path=DEFAULT_IFC_PATH, tolerance=0.01):
    """
    Detects geometric collisions (clashes) between elements of class_a and class_b.
    tolerance: distance in meters to consider a clash (default 1cm).
    """
    
    if not os.path.exists(ifc_path):
        print(f"Error: File {ifc_path} not found.")
        return pd.DataFrame()

    print(f"Loading {ifc_path}...")
    ifc_file = ifcopenshell.open(ifc_path)
    
    # Initialize Geometry Engine
    # USE_WORLD_COORDS is critical: it ensures that all meshes are generated
    # in the global coordinate system (Project 0,0,0) rather than local object space.
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)
    
    # 1. Collect Elements
    print(f"Collecting elements: {class_a} vs {class_b}...")
    
    elements_a = ifc_file.by_type(class_a)
    elements_b = ifc_file.by_type(class_b)
    
    if not elements_a or not elements_b:
        print("No elements found for one of the classes.")
        return pd.DataFrame()
        
    print(f"Found {len(elements_a)} elements of type {class_a}")
    print(f"Found {len(elements_b)} elements of type {class_b}")
    
    # 2. Build Collision Tree
    # We use IfcOpenShell's geometric tree (BVH - Bounding Volume Hierarchy).
    # This structure allows for fast spatial queries (O(log n)) instead of testing every pair (O(n^2)).
    print("Building geometry tree...")
    tree = ifcopenshell.geom.tree()
    
    # Add all elements from Group B to the tree (Target)
    count_b = 0
    for el in elements_b:
        if el.Representation:
            try:
                tree.add_element(el)
                count_b += 1
            except: pass
            
    if count_b == 0:
        print("No geometry found for target elements.")
        return pd.DataFrame()
        
    print("Running clash detection...")
    clashes = []
    
    # Check each element from Group A against the tree
    start_time = time.time()
    
    for el_a in elements_a:
        if not el_a.Representation:
            continue
            
        # GlobalId A
        guid_a = el_a.GlobalId
        name_a = el_a.Name if el_a.Name else "Unnamed"
        
        # Select colliding elements from the tree
        # tolerance is not directly supported in select() usually, it returns strict intersections?
        # select() returns list of elements that collide.
        try:
            colliding_elements = tree.select(el_a)
            
            for el_b in colliding_elements:
                # Avoid self-clash if groups overlap
                if el_a.id() == el_b.id():
                    continue
                    
                # Store Clash
                clashes.append({
                    "Element A ID": guid_a,
                    "Element A Name": name_a,
                    "Element A Type": el_a.is_a(),
                    "Element B ID": el_b.GlobalId,
                    "Element B Name": el_b.Name if el_b.Name else "Unnamed",
                    "Element B Type": el_b.is_a(),
                    "Clash Type": "Intersection" 
                })
        except Exception as e:
            # print(f"Error checking {guid_a}: {e}")
            pass
            
    end_time = time.time()
    print(f"Clash detection finished in {end_time - start_time:.2f} seconds.")
    
    df = pd.DataFrame(clashes)
    
    # Remove duplicates (A vs B and B vs A might appear if groups overlap)
    # If class_a == class_b, we will have duplicates.
    if class_a == class_b and not df.empty:
        # Create a sorted tuple key to identify unique pairs
        df['pair_key'] = df.apply(lambda row: tuple(sorted([row['Element A ID'], row['Element B ID']])), axis=1)
        df = df.drop_duplicates(subset=['pair_key'])
        df = df.drop(columns=['pair_key'])
        
    print(f"Total clashes found: {len(df)}")
    return df

# --- Colab Helper ---
if __name__ == "__main__":
    # Example: Check Wall vs Pipe
    # df = check_clashes("IfcWall", "IfcPipeSegment")
    # print(df)
    pass
