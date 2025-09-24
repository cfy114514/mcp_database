import json
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

class Tagger:
    def __init__(self, schema_path: Path):
        try:
            with schema_path.open('r', encoding='utf-8') as f:
                self.schema = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Failed to load tag schema from {schema_path}: {e}")
            self.schema = {}

    def _normalize_tags(self, tags: list) -> List[str]:
        """Normalizes a list of tags: flattens, removes whitespace, duplicates, and non-string elements."""
        flat_tags = []
        
        def flatten(tag_list):
            for item in tag_list:
                if isinstance(item, list):
                    flatten(item)
                elif isinstance(item, str) and item.strip():
                    flat_tags.append(item.strip().lower())

        flatten(tags)
        return sorted(list(set(flat_tags)))

    def infer_tags(self, content: str, filename: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[List[str], Dict[str, Any]]:
        """
        Infers tags and enhances metadata for a document based on filename, content, and existing metadata.
        """
        if metadata is None:
            metadata = {}
        
        inferred_tags = set(self.schema.get('default_tags', []))

        # 1. Path mapping
        for path_part, tags in self.schema.get('path_map', {}).items():
            if path_part in filename:
                inferred_tags.update(tags)

        # 2. Keyword mapping
        for keyword, tags in self.schema.get('keyword_map', {}).items():
            if keyword in content:
                inferred_tags.update(tags)

        # 3. Regex mapping
        for pattern, tags in self.schema.get('regex_map', {}).items():
            if re.search(pattern, content):
                inferred_tags.update(tags)

        # 4. Merge with metadata tags (metadata has priority)
        final_tags = inferred_tags
        metadata_tags = metadata.get('tags', [])
        if metadata_tags:
            # Normalize metadata tags before merging
            normalized_metadata_tags = self._normalize_tags(metadata_tags)
            final_tags.update(normalized_metadata_tags)

        # 5. Infer enforcement and importance
        enhanced_metadata = metadata.copy()
        
        # Enforcement
        enforcement_rules = self.schema.get('enforcement_rules', {})
        if any(tag in final_tags for tag in enforcement_rules.get('tags', [])) or \
           any(kw in content for kw in enforcement_rules.get('keywords', [])):
            enhanced_metadata['enforcement'] = True
        else:
            enhanced_metadata['enforcement'] = enhanced_metadata.get('enforcement', False)

        # Importance
        importance_rules = self.schema.get('importance_rules', {})
        current_importance = enhanced_metadata.get('importance')
        if not current_importance: # Only infer if not already set
            if any(tag in final_tags for tag in importance_rules.get('high', {}).get('tags', [])) or \
               any(kw in content for kw in importance_rules.get('high', {}).get('keywords', [])):
                enhanced_metadata['importance'] = 'high'
            elif any(tag in final_tags for tag in importance_rules.get('medium', {}).get('tags', [])) or \
                 any(kw in content for kw in importance_rules.get('medium', {}).get('keywords', [])):
                enhanced_metadata['importance'] = 'medium'
            elif any(tag in final_tags for tag in importance_rules.get('low', {}).get('tags', [])) or \
                 any(kw in content for kw in importance_rules.get('low', {}).get('keywords', [])):
                enhanced_metadata['importance'] = 'low'

        # 6. Check for conflicts
        conflict_rules = self.schema.get('conflict_rules', {})
        tag_conflicts = {}
        for prefix, max_count in conflict_rules.items():
            conflicting = [t for t in final_tags if t.startswith(f"{prefix}:")]
            if len(conflicting) > max_count:
                tag_conflicts[prefix] = conflicting
        
        if tag_conflicts:
            enhanced_metadata['__tag_conflict'] = tag_conflicts
            logger.warning(f"Tag conflict detected for {filename}: {tag_conflicts}")

        # Final normalization and return
        normalized_final_tags = self._normalize_tags(list(final_tags))
        
        # Update metadata with the final tags, removing the old 'tags' if it exists
        enhanced_metadata['tags'] = normalized_final_tags

        return normalized_final_tags, enhanced_metadata

# Global tagger instance
_schema_path = Path(__file__).parent.parent / 'configs' / 'tag_schema.json'
_tagger_instance = Tagger(_schema_path)

def infer_tags(content: str, filename: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[List[str], Dict[str, Any]]:
    """
    Global function to access the tagger instance.
    """
    return _tagger_instance.infer_tags(content, filename, metadata)
