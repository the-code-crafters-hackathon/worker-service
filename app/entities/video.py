from dataclasses import dataclass

@dataclass
class Video:
    user_id: int
    title: str
    file_path: str
    status: int
    id: int = None

@dataclass
class ProcessingMessage:
    video_id: int
    video_path: str
    timestamp: str
    user_id: int
