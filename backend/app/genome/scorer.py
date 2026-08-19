import math
from typing import List, Dict
from app.db.models.evidence_models import Evidence
from app.genome.taxonomy import get_base_genome_vector

# Heuristic weights for different evidence types
SOURCE_WEIGHTS = {
    "careers": 1.2,     # Leading indicator
    "products": 1.5,    # Strongest structural indicator
    "news": 0.8,        # Announcements (can be noisy)
    "positioning": 1.0  # Core messaging
}

def calculate_trait_score(evidences: List[Evidence]) -> float:
    """
    Deterministically calculate a score (0.0 to 1.0) based on accumulated evidence.
    """
    if not evidences:
        return 0.0
        
    raw_score = 0.0
    
    for ev in evidences:
        # Base confidence from normalizer
        base_val = ev.confidence
        
        # Apply source weight
        source_weight = SOURCE_WEIGHTS.get(ev.type, 1.0)
        
        raw_score += (base_val * source_weight)
        
    # Non-linear asymptotic scaling to keep it bounded strictly below 1.0
    # For example, if raw_score is 0, score is 0. 
    # If raw_score is 10, it approaches 1.0
    # Score = 1 - e^(-k * x)
    k = 0.15
    normalized_score = 1.0 - math.exp(-k * raw_score)
    
    return round(normalized_score, 4)

def score_genome(evidences: List[Evidence]) -> Dict[str, float]:
    """
    Takes all evidence for a company at a given snapshot in time
    and builds the deterministic genome vector.
    """
    genome = get_base_genome_vector()
    
    # Group evidence by trait
    evidence_by_trait = {trait: [] for trait in genome.keys()}
    
    for ev in evidences:
        if ev.trait in evidence_by_trait:
            evidence_by_trait[ev.trait].append(ev)
        else:
            evidence_by_trait["Other"].append(ev)
            
    # Calculate score for each trait
    for trait, trait_evidences in evidence_by_trait.items():
        genome[trait] = calculate_trait_score(trait_evidences)
        
    return genome
