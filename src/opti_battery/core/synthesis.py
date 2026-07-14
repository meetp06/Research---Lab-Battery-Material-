import datetime
from io import StringIO
from pymatgen.core import Structure
from pymatgen.io.cif import CifParser

def generate_cro_rfq(cif_string: str) -> dict:
    """
    Parses a CIF string to extract chemical information and generates
    a Request for Quotation (RFQ) and technical dossier for a Contract Research Organization.
    """
    try:
        parser = CifParser(StringIO(cif_string))
        structure = parser.get_structures()[0]
        
        formula = structure.composition.reduced_formula
        elements = [str(e) for e in structure.composition.elements]
        
        a = structure.lattice.a
        b = structure.lattice.b
        c = structure.lattice.c
        alpha = structure.lattice.alpha
        beta = structure.lattice.beta
        gamma = structure.lattice.gamma
        volume = structure.lattice.volume
        density = structure.density
        space_group = structure.get_space_group_info()
        
        today = datetime.date.today().strftime("%B %d, %Y")
        
        subject = f"Request for Quotation: Synthesis of {formula} Solid-State Battery Material"
        
        email_body = f"""Dear CRO Laboratory Team,

We are requesting a formal quotation for the custom synthesis and characterization of a novel solid-state battery material: {formula}.

Our computational screening has identified this crystal structure as a high-priority candidate. We require laboratory-scale synthesis (e.g., 50g - 100g powder batch) with high phase purity to begin coin-cell prototyping.

Please find the technical synthesis specifications attached below.
We can provide the full .cif crystallographic file upon request.

Could you please provide:
1. Estimated lead time.
2. Estimated cost for synthesis and basic characterization (XRD, SEM).
3. Feasibility assessment for scaling to 1kg if initial tests succeed.

Best regards,
Lead Researcher
Opti-Battery Informatics Platform
"""
        
        technical_dossier = f"""==================================================
TECHNICAL SYNTHESIS DOSSIER: {formula}
Generated on: {today}
==================================================

1. TARGET MATERIAL
--------------------------------------------------
Chemical Formula: {formula}
Constituent Elements: {', '.join(elements)}
Target Application: Advanced Solid-State Battery Material

2. CRYSTALLOGRAPHIC PARAMETERS
--------------------------------------------------
Space Group: {space_group[0]} (Number: {space_group[1]})
Lattice Parameters:
  a = {a:.4f} Å
  b = {b:.4f} Å
  c = {c:.4f} Å
  α = {alpha:.4f}°
  β = {beta:.4f}°
  γ = {gamma:.4f}°
Unit Cell Volume: {volume:.4f} Å³
Theoretical Density: {density:.4f} g/cm³

3. REQUIRED SPECIFICATIONS
--------------------------------------------------
- Target Phase Purity: > 98% (verified via XRD)
- Moisture Content: < 10 ppm (material must be handled in an Argon glovebox)
- Particle Size: D50 = 1 - 5 μm preferred
- Required Deliverables:
  * Synthesized powder (50g) sealed under Argon
  * XRD pattern comparing synthesized powder to target CIF
  * SEM images (Optional but preferred)

4. RECOMMENDED CRO PARTNERS TO CONTACT
--------------------------------------------------
- NEI Corporation (Custom Battery Materials Synthesis)
- MSE Supplies (Custom Synthesis Services)
- A-Lab / Lawrence Berkeley National Laboratory (Automated Synthesis)
- Argonne National Laboratory (Scale-up Facility)
==================================================
"""
        
        return {
            "success": True,
            "formula": formula,
            "subject": subject,
            "email_body": email_body,
            "technical_dossier": technical_dossier
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
