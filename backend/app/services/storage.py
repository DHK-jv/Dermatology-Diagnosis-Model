"""
Storage service for diagnosis history
Supports both MongoDB and JSON file fallback
"""
import json
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path
import logging

from ..config import settings
from ..models.schemas import PredictionResponse, DiagnosisHistory

logger = logging.getLogger(__name__)


class StorageService:
    """Handle storage operations for diagnosis history"""
    
    def __init__(self):
        """Initialize storage service"""
        self.use_mongodb = settings.USE_MONGODB
        self.history_file = settings.HISTORY_FILE
        
        if self.use_mongodb:
            try:
                from pymongo import MongoClient
                self.client = MongoClient(settings.MONGODB_URL)
                self.db = self.client[settings.MONGODB_DB_NAME]
                self.collection = self.db.diagnoses
                logger.info("Connected to MongoDB")
            except Exception as e:
                logger.warning(f"MongoDB connection failed: {e}. Falling back to JSON file.")
                self.use_mongodb = False
        
        if not self.use_mongodb:
            # Ensure JSON file exists
            if not self.history_file.exists():
                self.history_file.write_text("[]", encoding='utf-8')
                logger.info(f"Created history file: {self.history_file}")
    
    def _read_json_file(self) -> List[Dict]:
        """Read all records from JSON file"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading history file: {e}")
            return []
    
    def _write_json_file(self, data: List[Dict]):
        """Write all records to JSON file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error writing history file: {e}")
    
    async def save_diagnosis(self, prediction: PredictionResponse) -> bool:
        """
        Save a diagnosis record
        
        Args:
            prediction: PredictionResponse object
            
        Returns:
            Success status
        """
        record = {
            "diagnosis_id": prediction.diagnosis_id,
            "predicted_class": prediction.predicted_class,
            "disease_name_vi": prediction.disease_name_vi,
            "disease_name_en": prediction.disease_name_en,
            "confidence": prediction.confidence,
            "risk_level": prediction.risk_level,
            "risk_level_vi": prediction.risk_level_vi,
            "all_predictions": prediction.all_predictions,
            "recommendations": prediction.recommendations,
            "timestamp": prediction.timestamp.isoformat(),
            "image_filename": f"{prediction.diagnosis_id}.jpg"
        }
        
        if self.use_mongodb:
            try:
                self.collection.insert_one(record)
                logger.info(f"Saved diagnosis to MongoDB: {prediction.diagnosis_id}")
                return True
            except Exception as e:
                logger.error(f"Error saving to MongoDB: {e}")
                return False
        else:
            # JSON file storage
            try:
                data = self._read_json_file()
                data.append(record)
                self._write_json_file(data)
                logger.info(f"Saved diagnosis to JSON: {prediction.diagnosis_id}")
                return True
            except Exception as e:
                logger.error(f"Error saving to JSON: {e}")
                return False
    
    async def get_all_diagnoses(self, limit: int = 100) -> List[DiagnosisHistory]:
        """
        Get all diagnosis records
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of DiagnosisHistory objects
        """
        if self.use_mongodb:
            try:
                cursor = self.collection.find().sort("timestamp", -1).limit(limit)
                records = list(cursor)
                return [
                    DiagnosisHistory(
                        diagnosis_id=r["diagnosis_id"],
                        predicted_class=r["predicted_class"],
                        disease_name_vi=r["disease_name_vi"],
                        confidence=r["confidence"],
                        risk_level=r["risk_level"],
                        risk_level_vi=r["risk_level_vi"],
                        timestamp=datetime.fromisoformat(r["timestamp"]) if isinstance(r["timestamp"], str) else r["timestamp"],
                        image_filename=r.get("image_filename")
                    )
                    for r in records
                ]
            except Exception as e:
                logger.error(f"Error fetching from MongoDB: {e}")
                return []
        else:
            # JSON file storage
            try:
                data = self._read_json_file()
                # Sort by timestamp descending
                data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                data = data[:limit]
                
                return [
                    DiagnosisHistory(
                        diagnosis_id=r["diagnosis_id"],
                        predicted_class=r["predicted_class"],
                        disease_name_vi=r["disease_name_vi"],
                        confidence=r["confidence"],
                        risk_level=r["risk_level"],
                        risk_level_vi=r["risk_level_vi"],
                        timestamp=datetime.fromisoformat(r["timestamp"]) if isinstance(r["timestamp"], str) else r["timestamp"],
                        image_filename=r.get("image_filename")
                    )
                    for r in data
                ]
            except Exception as e:
                logger.error(f"Error fetching from JSON: {e}")
                return []
    
    async def get_diagnosis_by_id(self, diagnosis_id: str) -> Optional[PredictionResponse]:
        """
        Get a single diagnosis by ID
        
        Args:
            diagnosis_id: Unique diagnosis ID
            
        Returns:
            PredictionResponse object or None
        """
        if self.use_mongodb:
            try:
                record = self.collection.find_one({"diagnosis_id": diagnosis_id})
                if record:
                    return PredictionResponse(**record)
                return None
            except Exception as e:
                logger.error(f"Error fetching from MongoDB: {e}")
                return None
        else:
            # JSON file storage
            try:
                data = self._read_json_file()
                for record in data:
                    if record["diagnosis_id"] == diagnosis_id:
                        # Convert timestamp back to datetime
                        if isinstance(record["timestamp"], str):
                            record["timestamp"] = datetime.fromisoformat(record["timestamp"])
                        return PredictionResponse(**record)
                return None
            except Exception as e:
                logger.error(f"Error fetching from JSON: {e}")
                return None


# Create global instance
storage_service = StorageService()
