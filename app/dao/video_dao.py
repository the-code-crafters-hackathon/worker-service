from sqlalchemy.exc import IntegrityError

from app.models.video import Video as VideoModel
import logging

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

class VideoDAO:
    
    def __init__(self, db_session):
        self.db_session = db_session
        
    def update_video_status(self, video_id: int, status: int, file_path: str = None):
        try:
            video = self.db_session.query(VideoModel).filter(VideoModel.id == video_id).first()

            if not video:
                raise Exception(f"Vídeo com ID {video_id} não encontrado")
            video.status = status

            if file_path:
                video.file_path = file_path
            
            self.db_session.commit()
            self.db_session.refresh(video)
            
            return video
        except IntegrityError as e:
            self.db_session.rollback()
            raise Exception(f"Erro ao atualizar vídeo: {e}")
    
    def get_video_by_id(self, video_id: int):
        try:
            video = self.db_session.query(VideoModel).filter(
                VideoModel.id == video_id
            ).first()
            
            return video
        except Exception as e:
            raise Exception(f"Erro ao buscar vídeo: {e}")
