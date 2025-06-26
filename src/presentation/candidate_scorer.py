from typing import Dict, List, Optional
from dataclasses import dataclass
import math

from src.domain.models import Candidate, BrokenImport


@dataclass
class ScoringWeights:
    symbol_match: float = 1.0
    path_similarity: float = 0.8
    directory_pattern: float = 0.6
    git_history: float = 0.5
    dependencies: float = 0.7
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'symbol_match': self.symbol_match,
            'path_similarity': self.path_similarity,
            'directory_pattern': self.directory_pattern,
            'git_history': self.git_history,
            'dependencies': self.dependencies
        }


class CandidateScorer:
    
    def __init__(self, weights: Optional[ScoringWeights] = None):
        self.weights = weights or ScoringWeights()
        self._score_distributions: Dict[str, List[float]] = {}
    
    def score_candidates(self, candidates: List[Candidate],
                        broken_import: BrokenImport) -> List[Candidate]:
        for candidate in candidates:
            self._calculate_individual_scores(candidate, broken_import)
        
        self._normalize_scores(candidates)
        
        for candidate in candidates:
            candidate.score.calculate_total(self.weights.to_dict())
        
        return sorted(candidates, reverse=True)
    
    def _calculate_individual_scores(self, candidate: Candidate,
                                   broken_import: BrokenImport):
        if not candidate.score.symbol_match:
            candidate.score.symbol_match = self._calculate_symbol_score(
                candidate, broken_import
            )
        
        candidate.score.path_similarity = self._calculate_path_similarity(
            candidate, broken_import
        )
        
        candidate.score.directory_pattern = self._calculate_directory_pattern_score(
            candidate, broken_import
        )
        
        candidate.score.dependencies = self._calculate_dependency_score(
            candidate, broken_import
        )
    
    def _calculate_symbol_score(self, candidate: Candidate,
                               broken_import: BrokenImport) -> float:
        if not broken_import.imported_names:
            return 0.0
        
        matched = len(candidate.matched_symbols)
        total = len(broken_import.imported_names)
        
        if total == 0:
            return 0.0
        
        return matched / total
    
    def _calculate_path_similarity(self, candidate: Candidate,
                                  broken_import: BrokenImport) -> float:
        import_parts = broken_import.module_path.split('.')
        candidate_parts = candidate.module_path.split('.')
        
        common_prefix_len = 0
        for i, (a, b) in enumerate(zip(import_parts, candidate_parts)):
            if a == b:
                common_prefix_len += 1
            else:
                break
        
        max_len = max(len(import_parts), len(candidate_parts))
        if max_len == 0:
            return 0.0
        
        similarity = common_prefix_len / max_len
        
        if import_parts[-1] == candidate_parts[-1]:
            similarity += 0.2
        
        edit_distance = self._levenshtein_distance(
            broken_import.module_path,
            candidate.module_path
        )
        max_str_len = max(len(broken_import.module_path), len(candidate.module_path))
        if max_str_len > 0:
            distance_score = 1 - (edit_distance / max_str_len)
            similarity = (similarity + distance_score) / 2
        
        return min(similarity, 1.0)
    
    def _calculate_directory_pattern_score(self, candidate: Candidate,
                                         broken_import: BrokenImport) -> float:
        import_path_parts = broken_import.file_path.parent.parts
        candidate_path_parts = candidate.file_path.parent.parts
        
        common_patterns = [
            ('models', 'models'),
            ('views', 'views'),
            ('controllers', 'controllers'),
            ('services', 'services'),
            ('utils', 'utils'),
            ('core', 'core'),
            ('domain', 'domain'),
            ('infrastructure', 'infrastructure'),
            ('tests', 'tests')
        ]
        
        score = 0.0
        
        for pattern_from, pattern_to in common_patterns:
            if (pattern_from in import_path_parts and 
                pattern_to in candidate_path_parts):
                score += 0.3
        
        depth_diff = abs(len(import_path_parts) - len(candidate_path_parts))
        if depth_diff == 0:
            score += 0.4
        elif depth_diff == 1:
            score += 0.2
        
        return min(score, 1.0)
    
    def _calculate_dependency_score(self, candidate: Candidate,
                                   broken_import: BrokenImport) -> float:
        context = candidate.metadata.get('context', {})
        if 'common_dependencies' in context:
            common_deps = context['common_dependencies']
            if common_deps > 5:
                return 1.0
            elif common_deps > 2:
                return 0.7
            elif common_deps > 0:
                return 0.4
        
        return 0.0
    
    def _normalize_scores(self, candidates: List[Candidate]):
        score_types = ['symbol_match', 'path_similarity', 'directory_pattern', 
                      'git_history', 'dependencies']
        
        for score_type in score_types:
            scores = [getattr(c.score, score_type) for c in candidates]
            if not scores:
                continue
            
            min_score = min(scores)
            max_score = max(scores)
            
            if max_score - min_score < 0.001:
                continue
            
            for candidate in candidates:
                current = getattr(candidate.score, score_type)
                normalized = (current - min_score) / (max_score - min_score)
                setattr(candidate.score, score_type, normalized)
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]