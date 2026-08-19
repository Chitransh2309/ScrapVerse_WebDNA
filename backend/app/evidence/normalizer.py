import logging
from typing import List
from datetime import datetime
from app.db.models.evidence_models import RawSnapshot, Evidence

logger = logging.getLogger(__name__)

# Basic rule-based classification mapping for the MVP
TRAIT_KEYWORDS = {
    "AI Infrastructure": ["ai", "cuda", "gpu", "inference", "tensor", "machine learning", "deep learning"],
    "Consumer Hardware": ["geforce", "rtx", "gaming", "laptop", "desktop", "consumer"],
    "Data Center": ["data center", "server", "networking", "hpc", "dgx", "infiniband"],
    "Robotics": ["robotics", "isaac", "autonomous machines", "robot", "manipulation"],
    "Automotive": ["automotive", "drive", "autonomous vehicle", "self-driving", "adas", "car"],
    "Enterprise": ["enterprise", "vdi", "omniverse", "workstation"],
    "Cloud": ["cloud", "aws", "azure", "gcp", "saas", "paas"],
    "Developer Tools": ["sdk", "api", "developer", "toolkit", "compiler", "nsight"],
    "Software": ["software", "driver", "os", "linux", "windows"],
}

def classify_trait(text: str) -> str:
    """Classify text into a genome trait based on keywords."""
    text = text.lower()
    best_trait = "Other"
    max_matches = 0
    
    for trait, keywords in TRAIT_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in text)
        if matches > max_matches:
            max_matches = matches
            best_trait = trait
            
    return best_trait

def normalize_careers(snapshot: RawSnapshot) -> List[Evidence]:
    """Normalize a careers raw snapshot into evidence."""
    evidences = []
    if not snapshot.raw_data or not isinstance(snapshot.raw_data, list):
        return evidences
        
    for item in snapshot.raw_data:
        title = item.get("job_title", "")
        skills = " ".join(item.get("skills", []))
        desc = f"{title} {skills}"
        
        trait = classify_trait(desc)
        
        evidences.append(Evidence(
            company_id=snapshot.company_id,
            snapshot_id=snapshot.id,
            type="careers",
            trait=trait,
            title=f"Hiring: {title}",
            content=f"Skills: {skills}",
            url=item.get("url", ""),
            source="Bright Data Careers",
            confidence=0.8, # Hardcoded baseline confidence for now
            observed_at=snapshot.timestamp
        ))
    return evidences

def normalize_products(snapshot: RawSnapshot) -> List[Evidence]:
    """Normalize a products raw snapshot into evidence."""
    evidences = []
    if not snapshot.raw_data or not isinstance(snapshot.raw_data, list):
        return evidences
        
    for item in snapshot.raw_data:
        name = item.get("product_name", "")
        desc = item.get("description", "")
        combined = f"{name} {desc}"
        
        trait = classify_trait(combined)
        
        evidences.append(Evidence(
            company_id=snapshot.company_id,
            snapshot_id=snapshot.id,
            type="products",
            trait=trait,
            title=f"Product: {name}",
            content=desc,
            url=item.get("url", ""),
            source="Bright Data Products",
            confidence=0.85,
            observed_at=snapshot.timestamp
        ))
    return evidences

def normalize_news(snapshot: RawSnapshot) -> List[Evidence]:
    """Normalize a news raw snapshot into evidence."""
    evidences = []
    if not snapshot.raw_data or not isinstance(snapshot.raw_data, list):
        return evidences
        
    for item in snapshot.raw_data:
        title = item.get("title", "")
        summary = item.get("summary", "")
        combined = f"{title} {summary}"
        
        trait = classify_trait(combined)
        
        evidences.append(Evidence(
            company_id=snapshot.company_id,
            snapshot_id=snapshot.id,
            type="news",
            trait=trait,
            title=f"News: {title}",
            content=summary,
            url=item.get("url", ""),
            source="Bright Data News",
            confidence=0.7,
            observed_at=snapshot.timestamp
        ))
    return evidences

def normalize_snapshot(snapshot: RawSnapshot, source_type: str) -> List[Evidence]:
    """Route normalization based on source type."""
    if source_type == "careers":
        return normalize_careers(snapshot)
    elif source_type == "products":
        return normalize_products(snapshot)
    elif source_type == "news":
        return normalize_news(snapshot)
    else:
        logger.warning(f"Unknown source type for normalization: {source_type}")
        return []
