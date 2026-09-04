"""
MedScribe Dashboard — Entity Card Component Helpers
"""

def render_diagnosis_card(description: str, code: str = None, severity_badge_html: str = "") -> str:
    icd_html = f"<span style='color:#64748b;font-size:0.8rem;margin-left:10px;'>ICD: {code}</span>" if code else ""
    return f"""
    <div class="entity-card">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
                <span style="font-weight:600;color:#f1f5f9;font-size:1rem;">🏥 {description}</span>
                {icd_html}
            </div>
            {severity_badge_html}
        </div>
    </div>
    """
