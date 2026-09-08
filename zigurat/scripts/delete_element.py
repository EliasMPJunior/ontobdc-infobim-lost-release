# Script to delete IFC elements by GlobalId (Smart Delete).
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. Upload an IFC file.
# 2. Run the function delete_elements(...)

# Install dependencies if not present
# !pip install ifcopenshell

import sys
import os
import ifcopenshell
import ifcopenshell.api

DEFAULT_FILE_PATH = "minimal.ifc" # Default for Colab

def get_exclusive_dependencies(f, element):
    """
    Identifies dependencies that should be deleted if the element is deleted.
    Returns a list of IFC entity instances.
    
    In IFC, deleting an object (like a Wall) is not enough. We must also delete
    objects that strictly depend on it to avoid "orphaned" data.
    These include:
    1. ObjectPlacement: The coordinate system of the object.
    2. Representation: The 3D geometry definitions.
    3. Ports: Connection points (IfcDistributionPort) nested in the element.
    4. Property Sets: Data containers defined specifically for this instance.
    """
    candidates = []
    
    # 1. ObjectPlacement
    if hasattr(element, "ObjectPlacement") and element.ObjectPlacement:
        candidates.append(element.ObjectPlacement)
        
    # 2. Representation
    if hasattr(element, "Representation") and element.Representation:
        candidates.append(element.Representation)
        if element.Representation.is_a("IfcProductDefinitionShape"):
             for rep in element.Representation.Representations:
                 candidates.append(rep)
                 for item in rep.Items:
                     candidates.append(item)
    
    # 3. Ports (IfcRelNests)
    # Ports are "nested" in the element. If the element is gone, ports should be too.
    if hasattr(element, "IsNestedBy"):
        for rel in element.IsNestedBy:
            if rel.is_a("IfcRelNests"):
                for nested in rel.RelatedObjects:
                    candidates.append(nested)
                    # Recursively get dependencies of the port (e.g., its placement)
                    candidates.extend(get_exclusive_dependencies(f, nested))
                    
    # 4. Property Sets (IfcRelDefinesByProperties)
    # We only delete Psets if they are specific to this element instance (not shared types).
    if hasattr(element, "IsDefinedBy"):
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                pset = rel.RelatingPropertyDefinition
                if pset and pset.is_a("IfcPropertySet"):
                    candidates.append(pset)

    return candidates

def delete_elements(ifc_file, global_ids):
    """
    Deletes elements identified by global_ids (list of strings) and their exclusive dependencies.
    """
    
    # 1. Resolve Elements
    elements_to_delete = []
    for guid in global_ids:
        try:
            el = ifc_file.by_guid(guid)
            if el:
                elements_to_delete.append(el)
            else:
                print(f"Warning: GUID {guid} not found.")
        except:
            print(f"Warning: Invalid GUID {guid}.")

    if not elements_to_delete:
        print("No valid elements found to delete.")
        return

    # 2. Collect all IDs to be deleted (Elements + Exclusive Dependencies)
    primary_ids = set(e.id() for e in elements_to_delete)
    
    # First pass: Collect potential candidates
    candidates = []
    for el in elements_to_delete:
        candidates.extend(get_exclusive_dependencies(ifc_file, el))
        
    # Filter candidates: Must be unique
    unique_candidates = list({c.id(): c for c in candidates}.values())
    
    candidate_map = {c.id(): c for c in unique_candidates}
    current_delete_set = primary_ids.union(candidate_map.keys())
    
    # Check exclusivity (Simplified for Colab script)
    # Real implementations check if dependencies are shared by other objects.
    # Here we assume standard structure where Placement/Shape are not shared.
    stable = False
    while not stable:
        stable = True
        ids_to_remove_from_delete = set()
        
        for cid, c_entity in candidate_map.items():
            if cid not in current_delete_set:
                continue
                
            # Check inverse references
            inverse = ifc_file.get_inverse(c_entity)
            is_kept = False
            for ref in inverse:
                if ref.id() not in current_delete_set:
                    # Special Logic for Relationships
                    if ref.is_a("IfcRelDefinesByProperties"):
                         related = ref.RelatedObjects
                         if not any(r.id() not in current_delete_set for r in related):
                             continue
                    
                    is_kept = True
                    break
            
            if is_kept:
                ids_to_remove_from_delete.add(cid)
                stable = False
        
        if ids_to_remove_from_delete:
            current_delete_set -= ids_to_remove_from_delete
            
    # 3. Execute Deletion
    print(f"Deleting {len(elements_to_delete)} primary elements and {len(current_delete_set) - len(primary_ids)} dependencies...")
    
    for el in elements_to_delete:
        print(f" - Removing Product: {el.Name} ({el.GlobalId})")
        try:
            ifcopenshell.api.run("root.remove_product", ifc_file, product=el)
        except Exception as e:
            print(f"   Error removing product {el.GlobalId}: {e}")
            
    for cid in current_delete_set:
        if cid in primary_ids: 
            continue 
            
        try:
            entity = ifc_file.by_id(cid)
            # print(f" - Removing Dependency: {entity.is_a()} (#{cid})")
            ifc_file.remove(entity)
        except:
            pass

    print("Deletion complete.")

# --- Colab Helper ---
def run_example_delete(filename="minimal.ifc", guid_to_delete=None):
    if not os.path.exists(filename):
        print(f"File {filename} not found.")
        return

    f = ifcopenshell.open(filename)
    
    if not guid_to_delete:
        # Try to find something to delete
        proxies = f.by_type("IfcBuildingElementProxy")
        if proxies:
            guid_to_delete = proxies[0].GlobalId
        else:
            print("No proxies found to delete.")
            return

    delete_elements(f, [guid_to_delete])
    
    f.write(filename)
    print(f"Saved updated file to {filename}")

if __name__ == "__main__":
    pass
