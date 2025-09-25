# app/state.py
"""
Application State Management for FA-GPT
Centralizes all session state variables into a clean dataclass structure
"""
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

@dataclass
class AppState:
    """
    A centralized class to hold the FA-GPT application's session state.
    This replaces scattered st.session_state variables with organized state management.
    """
    # Core session management
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_start_time: datetime = field(default_factory=datetime.now)
    
    # UI Navigation State
    current_view: str = "intelligence_hub"
    active_tab: str = "📊 INTELLIGENCE HUB"
    
    # Chat and Conversation State
    messages: List[Dict[str, Any]] = field(default_factory=list)
    conversation_mode: bool = True
    last_query: str = ""
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Document Processing State
    processing_status: str = "idle"  # idle, processing, completed, error
    last_processed_document: Optional[str] = None
    processing_progress: float = 0.0
    processing_messages: List[str] = field(default_factory=list)
    
    # Fire Support Planning State (from original app/main.py)
    current_target: Optional[Dict[str, Any]] = None
    firing_units: List[Dict[str, Any]] = field(default_factory=list)
    mission_data: Dict[str, Any] = field(default_factory=dict)
    ballistic_calculations: Dict[str, Any] = field(default_factory=dict)
    
    # System Status and Configuration
    system_health: Dict[str, Any] = field(default_factory=lambda: {
        "database": "unknown",
        "ollama": "unknown", 
        "gpu": "unknown",
        "models": "unknown"
    })
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    
    # File Upload and Management State
    uploaded_files: List[Dict[str, Any]] = field(default_factory=list)
    file_processing_queue: List[str] = field(default_factory=list)
    
    # Advanced Features State
    multimodal_enabled: bool = True
    vision_analysis_enabled: bool = True
    advanced_extraction: bool = True
    
    def add_message(self, role: str, content: str, **kwargs):
        """Add a message to the conversation history with metadata"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            **kwargs
        }
        self.messages.append(message)
    
    def clear_messages(self):
        """Clear all messages from current conversation"""
        self.messages.clear()
    
    def update_processing_status(self, status: str, progress: float = 0.0, message: str = ""):
        """Update document processing status with optional progress and message"""
        self.processing_status = status
        self.processing_progress = progress
        if message:
            self.processing_messages.append(f"{datetime.now().strftime('%H:%M:%S')}: {message}")
    
    def reset_session(self):
        """Reset session state while preserving configuration"""
        self.session_id = str(uuid.uuid4())
        self.session_start_time = datetime.now()
        self.messages.clear()
        self.conversation_history.clear()
        self.processing_messages.clear()
        self.processing_status = "idle"
        self.processing_progress = 0.0
        self.current_target = None
        self.firing_units.clear()
        self.mission_data.clear()
        self.ballistic_calculations.clear()
        self.uploaded_files.clear()
        self.file_processing_queue.clear()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session for debugging/logging"""
        return {
            "session_id": self.session_id,
            "session_duration": (datetime.now() - self.session_start_time).total_seconds(),
            "messages_count": len(self.messages),
            "current_view": self.current_view,
            "processing_status": self.processing_status,
            "system_health": self.system_health,
            "active_features": {
                "multimodal": self.multimodal_enabled,
                "vision_analysis": self.vision_analysis_enabled,
                "advanced_extraction": self.advanced_extraction
            }
        }