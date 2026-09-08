# Script to validate IFC elements using IDS (Information Delivery Specification).
# Adapted for Google Colab.
#
# Usage in Colab:
# 1. Upload an IFC file and an IDS file (.xml).
# 2. Run validate_ids(ifc_file="model.ifc", ids_file="requirements.ids")

# Install dependencies if not present
# !pip install ifcopenshell ifctester

import ifcopenshell
import sys
import os
import ifctester
import ifctester.reporter

# --- CONFIG ---
DEFAULT_IFC_PATH = "minimal.ifc" # Default for Colab
DEFAULT_IDS_PATH = "requirements.ids"

def validate_ids(ifc_path=DEFAULT_IFC_PATH, ids_path=DEFAULT_IDS_PATH, output_html="validation_report.html"):
    """
    Validates an IFC file against an IDS specification using IfcTester.
    Generates an HTML report.
    
    IDS (Information Delivery Specification) is a standard (buildingSMART) for defining
    machine-readable requirements. 'ifctester' is the official Python library to check
    if an IFC model meets these requirements (e.g., correct classification, properties, materials).
    """
    
    if not os.path.exists(ifc_path):
        print(f"Error: IFC file {ifc_path} not found.")
        return

    if not os.path.exists(ids_path):
        print(f"Error: IDS file {ids_path} not found.")
        return

    print(f"Loading {ifc_path}...")
    ifc_file = ifcopenshell.open(ifc_path)
    
    print(f"Loading IDS {ids_path}...")
    my_ids = ifctester.ids.open(ids_path)
    
    print("Validating...")
    # Validate the model against the IDS rules
    my_ids.validate(ifc_file)
    
    # Generate Report
    print(f"Generating report: {output_html}...")
    reporter = ifctester.reporter.Html(my_ids)
    reporter.report()
    reporter.to_file(output_html)
    
    print("Done! You can download the report.")
    
    # Optional: Print summary to console
    print("\n--- Validation Summary ---")
    total_specs = len(my_ids.specifications)
    passed_specs = sum(1 for s in my_ids.specifications if s.status)
    print(f"Specifications Checked: {total_specs}")
    print(f"Passed: {passed_specs}")
    print(f"Failed: {total_specs - passed_specs}")

# --- Colab Helper ---
if __name__ == "__main__":
    pass
