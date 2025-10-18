"""
Provenance Tracker - Track sources, timestamps, and metadata for strategies
Maintains audit trail of where strategy information came from.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from urllib.parse import urlparse


class ProvenanceTracker:
    """Track and manage strategy provenance information."""
    
    SOURCE_TYPES = [
        "user_input", "web_article", "youtube", "tiktok", 
        "social_post", "pdf", "other"
    ]
    
    def __init__(self):
        """Initialize the provenance tracker."""
        self.sources = []
    
    def add_source(
        self,
        url: Optional[str] = None,
        source_type: str = "user_input",
        author: Optional[str] = None,
        snippet: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a provenance source.
        
        Args:
            url: Source URL (if applicable)
            source_type: Type of source
            author: Author name
            snippet: Short excerpt from source
            additional_metadata: Any other metadata
            
        Returns:
            The created source record
        """
        if source_type not in self.SOURCE_TYPES:
            source_type = "other"
        
        source = {
            "fetched_at": datetime.now().isoformat(),
            "type": source_type
        }
        
        if url:
            source["url"] = url
            # Auto-detect source type from URL if not explicitly set
            if source_type == "user_input" or source_type == "other":
                detected_type = self._detect_source_type_from_url(url)
                if detected_type:
                    source["type"] = detected_type
        
        if author:
            source["author"] = author
        
        if snippet:
            # Truncate snippet if too long
            source["snippet"] = snippet[:500] if len(snippet) > 500 else snippet
        
        if additional_metadata:
            source.update(additional_metadata)
        
        self.sources.append(source)
        return source
    
    def add_user_input(self, input_text: str, username: str = "user") -> Dict[str, Any]:
        """Add a user input as a source."""
        snippet = input_text[:200] if len(input_text) > 200 else input_text
        return self.add_source(
            source_type="user_input",
            author=username,
            snippet=snippet
        )
    
    def add_web_article(
        self,
        url: str,
        author: Optional[str] = None,
        title: Optional[str] = None,
        snippet: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a web article as a source."""
        metadata = {}
        if title:
            metadata["title"] = title
        
        return self.add_source(
            url=url,
            source_type="web_article",
            author=author,
            snippet=snippet,
            additional_metadata=metadata
        )
    
    def add_video_source(
        self,
        url: str,
        platform: str = "youtube",
        author: Optional[str] = None,
        title: Optional[str] = None,
        transcript_snippet: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a video source (YouTube, TikTok, etc.)."""
        metadata = {}
        if title:
            metadata["title"] = title
        
        source_type = platform.lower()
        if source_type not in ["youtube", "tiktok"]:
            source_type = "other"
        
        return self.add_source(
            url=url,
            source_type=source_type,
            author=author,
            snippet=transcript_snippet,
            additional_metadata=metadata
        )
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """Get all tracked sources."""
        return self.sources.copy()
    
    def get_provenance_summary(self) -> str:
        """Get a human-readable summary of provenance."""
        if not self.sources:
            return "No sources tracked"
        
        summary_parts = []
        for i, source in enumerate(self.sources, 1):
            source_type = source.get("type", "unknown")
            author = source.get("author", "Unknown")
            url = source.get("url", "N/A")
            
            summary_parts.append(
                f"{i}. {source_type.replace('_', ' ').title()} by {author} ({url})"
            )
        
        return "\n".join(summary_parts)
    
    def to_canonical_format(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert to canonical strategy schema format."""
        return {"sources": self.sources}
    
    def _detect_source_type_from_url(self, url: str) -> Optional[str]:
        """Auto-detect source type from URL."""
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc
            
            if "youtube.com" in domain or "youtu.be" in domain:
                return "youtube"
            elif "tiktok.com" in domain:
                return "tiktok"
            elif any(x in domain for x in ["twitter.com", "x.com", "facebook.com", "linkedin.com"]):
                return "social_post"
            elif ".pdf" in parsed.path:
                return "pdf"
            else:
                return "web_article"
        except Exception:
            return None
    
    def merge_from_dict(self, provenance_dict: Dict[str, Any]) -> None:
        """Merge provenance data from a dictionary."""
        if "sources" in provenance_dict:
            self.sources.extend(provenance_dict["sources"])


class MetadataManager:
    """Manage strategy metadata (created_at, created_by, confidence, etc.)."""
    
    CONFIDENCE_LEVELS = ["low", "medium", "high"]
    
    def __init__(self, created_by: str):
        """
        Initialize metadata manager.
        
        Args:
            created_by: User or system identifier
        """
        self.metadata = {
            "created_at": datetime.now().isoformat(),
            "created_by": created_by,
            "last_updated": datetime.now().isoformat(),
            "confidence": "low"
        }
    
    def set_confidence(self, confidence: str) -> None:
        """Set confidence level."""
        if confidence in self.CONFIDENCE_LEVELS:
            self.metadata["confidence"] = confidence
            self.update_timestamp()
        else:
            raise ValueError(f"Confidence must be one of {self.CONFIDENCE_LEVELS}")
    
    def add_note(self, note: str) -> None:
        """Add a note to metadata."""
        existing_notes = self.metadata.get("notes", "")
        if existing_notes:
            self.metadata["notes"] = existing_notes + "\n" + note
        else:
            self.metadata["notes"] = note
        self.update_timestamp()
    
    def update_timestamp(self) -> None:
        """Update the last_updated timestamp."""
        self.metadata["last_updated"] = datetime.now().isoformat()
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get the metadata dictionary."""
        return self.metadata.copy()
    
    def to_canonical_format(self) -> Dict[str, Any]:
        """Return metadata in canonical format."""
        return self.metadata


def create_provenance_from_input(
    input_text: str,
    username: str = "user"
) -> ProvenanceTracker:
    """
    Convenience function to create provenance from user input.
    
    Args:
        input_text: Raw input text
        username: Username or identifier
        
    Returns:
        ProvenanceTracker instance
    """
    tracker = ProvenanceTracker()
    tracker.add_user_input(input_text, username)
    return tracker


def create_metadata(
    created_by: str = "user",
    confidence: str = "low",
    notes: Optional[str] = None
) -> MetadataManager:
    """
    Convenience function to create metadata.
    
    Args:
        created_by: User identifier
        confidence: Confidence level
        notes: Optional notes
        
    Returns:
        MetadataManager instance
    """
    manager = MetadataManager(created_by)
    manager.set_confidence(confidence)
    if notes:
        manager.add_note(notes)
    return manager


if __name__ == "__main__":
    # Test provenance tracker
    tracker = ProvenanceTracker()
    
    # Add user input
    tracker.add_user_input(
        "Buy 100 shares when 50 EMA crosses above 200 EMA",
        "nyaga"
    )
    
    # Add web article
    tracker.add_web_article(
        url="https://example.com/strategy",
        author="Jane Doe",
        title="Simple EMA Crossover Strategy",
        snippet="This strategy uses 50/200 EMA crossover..."
    )
    
    print("Provenance Summary:")
    print(tracker.get_provenance_summary())
    
    print("\n\nCanonical Format:")
    import json
    print(json.dumps(tracker.to_canonical_format(), indent=2))
    
    # Test metadata
    print("\n\nMetadata Test:")
    meta = create_metadata("user:nyaga", "medium", "Initial strategy draft")
    print(json.dumps(meta.get_metadata(), indent=2))
