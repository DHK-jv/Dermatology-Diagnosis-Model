"""
Dịch vụ lưu trữ lịch sử chẩn đoán
Hỗ trợ cả MongoDB và lưu trữ dự phòng bằng file JSON
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
    """Xử lý các thao tác lưu trữ cho lịch sử chẩn đoán"""
    
    def __init__(self):
        """Khởi tạo dịch vụ lưu trữ"""
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
            # Đảm bảo file JSON dự phòng tồn tại
            if not self.history_file.exists():
                self.history_file.write_text("[]", encoding='utf-8')
                logger.info(f"Created history file: {self.history_file}")
    
    def _read_json_file(self) -> List[Dict]:
        """Đọc tất cả bản ghi từ file JSON"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading history file: {e}")
            return []
    
    def _write_json_file(self, data: List[Dict]):
        """Ghi tất cả bản ghi vào file JSON"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error writing history file: {e}")
    
    async def save_diagnosis(self, prediction: PredictionResponse, user_id: str = None) -> bool:
        """
        Lưu một bản ghi chẩn đoán
        
        Args:
            prediction: Đối tượng PredictionResponse chứa kết quả dự đoán
            user_id: ID tùy chọn của người dùng đang tạo chẩn đoán này
            
        Returns:
            Trạng thái thành công
        """
        record = {
            "diagnosis_id": prediction.diagnosis_id,
            "user_id": user_id,
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
            # Lưu trữ bằng file JSON
            try:
                data = self._read_json_file()
                data.append(record)
                self._write_json_file(data)
                logger.info(f"Saved diagnosis to JSON: {prediction.diagnosis_id}")
                return True
            except Exception as e:
                logger.error(f"Error saving to JSON: {e}")
                return False
    
    async def get_all_diagnoses(self, limit: int = 100, user_id: str = None) -> List[DiagnosisHistory]:
        """
        Lấy tất cả bản ghi chẩn đoán
        
        Args:
            limit: Số lượng bản ghi tối đa để trả về
            user_id: Dùng để lọc bản ghi của một User ID chỉ định
            
        Returns:
            Danh sách các đối tượng DiagnosisHistory
        """
        if self.use_mongodb:
            try:
                query = {}
                if user_id:
                    query["user_id"] = user_id
                cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
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
            # Lưu trữ bằng file JSON
            try:
                data = self._read_json_file()
                
                # Lọc theo user_id nếu có
                if user_id:
                    data = [r for r in data if r.get("user_id") == user_id]
                    
                # Sắp xếp theo thời gian mới nhất giảm dần
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
        Lấy chi tiết một chẩn đoán theo ID
        
        Args:
            diagnosis_id: ID duy nhất của chẩn đoán
            
        Returns:
            Đối tượng PredictionResponse hoặc None
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
            # Lưu trữ bằng file JSON
            try:
                data = self._read_json_file()
                for record in data:
                    if record["diagnosis_id"] == diagnosis_id:
                        # Chuyển timestamp trở lại thành datetime
                        if isinstance(record["timestamp"], str):
                            record["timestamp"] = datetime.fromisoformat(record["timestamp"])
                        return PredictionResponse(**record)
                return None
            except Exception as e:
                logger.error(f"Error fetching from JSON: {e}")
                return None

    async def save_feedback(self, feedback: Dict) -> bool:
        """
        Lưu đánh giá phản hồi cho một chẩn đoán
        
        Args:
            feedback: Dictionary chứa dữ liệu đánh giá
            
        Returns:
            Trạng thái thành công
        """
        from datetime import datetime
        feedback['timestamp'] = datetime.now().isoformat()
        
        if self.use_mongodb:
            try:
                feedback_collection = self.db.feedback
                feedback_collection.insert_one(feedback)
                
                # Cập nhật chẩn đoán gốc để trỏ cờ báo đã có đánh giá
                self.collection.update_one(
                    {"diagnosis_id": feedback["diagnosis_id"]},
                    {"$set": {"has_feedback": True}}
                )
                
                logger.info(f"Saved feedback for {feedback['diagnosis_id']} to MongoDB")
                return True
            except Exception as e:
                logger.error(f"Error saving feedback to MongoDB: {e}")
                return False
        else:
            try:
                feedback_file = self.history_file.parent / 'feedback.json'
                if not feedback_file.exists():
                    feedback_file.write_text("[]", encoding='utf-8')
                
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data.append(feedback)
                
                with open(feedback_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2, default=str)
                
                # Cập nhật trong file JSON lịch sử chẩn đoán
                diagnoses = self._read_json_file()
                for d in diagnoses:
                    if d.get("diagnosis_id") == feedback["diagnosis_id"]:
                        d["has_feedback"] = True
                        break
                self._write_json_file(diagnoses)
                    
                logger.info(f"Saved feedback for {feedback['diagnosis_id']} to JSON")
                return True
            except Exception as e:
                logger.error(f"Error saving feedback to JSON: {e}")
                return False

    def _read_users_json(self) -> List[Dict]:
        """Đọc danh sách người dùng từ file JSON"""
        users_file = self.history_file.parent / 'users.json'
        if not users_file.exists():
            return []
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []

    def _write_users_json(self, data: List[Dict]):
        """Ghi danh sách người dùng vào file JSON"""
        users_file = self.history_file.parent / 'users.json'
        try:
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error writing users file: {e}")

    async def get_all_users(self) -> List[Dict]:
        """Lấy tất cả người dùng đã đăng ký"""
        if self.use_mongodb:
            try:
                users = list(self.db.users.find({}, {"hashed_password": 0}))  # Loại trừ mật khẩu
                # Chuyển đổi ObjectId thành chuỗi
                for u in users:
                    u["_id"] = str(u["_id"])
                return users
            except Exception as e:
                logger.error(f"Error fetching users from MongoDB: {e}")
                return []
        else:
            users = self._read_users_json()
            # Xóa mật khẩu đã băm trước khi trả về
            return [{k: v for k, v in u.items() if k != "hashed_password"} for u in users]
            
    async def get_dashboard_stats(self) -> Dict:
        """Lấy số liệu thống kê cho bảng điều khiển admin"""
        stats = {
            "total_users": 0,
            "total_diagnoses": 0,
            "today_diagnoses": 0,
            "high_risk_cases": 0
        }
        
        today_prefix = datetime.now().strftime("%Y-%m-%d")
        
        if self.use_mongodb:
            try:
                stats["total_users"] = self.db.users.count_documents({})
                stats["total_diagnoses"] = self.collection.count_documents({})
                
                # Chẩn đoán trong ngày hôm nay (giả sử timestamp được lưu dưới dạng chuỗi ISO)
                stats["today_diagnoses"] = self.collection.count_documents({
                    "timestamp": {"$regex": f"^{today_prefix}"}
                })
                
                # Trường hợp rủi ro cao
                stats["high_risk_cases"] = self.collection.count_documents({
                    "risk_level": {"$in": ["high", "very_high", "critical"]}
                })
            except Exception as e:
                logger.error(f"Error fetching stats from MongoDB: {e}")
        else:
            try:
                users = self._read_users_json()
                diagnoses = self._read_json_file()
                
                stats["total_users"] = len(users)
                stats["total_diagnoses"] = len(diagnoses)
                
                for d in diagnoses:
                    ts = d.get("timestamp", "")
                    if ts.startswith(today_prefix):
                        stats["today_diagnoses"] += 1
                    if d.get("risk_level") in ["high", "very_high", "critical"]:
                        stats["high_risk_cases"] += 1
                        
            except Exception as e:
                logger.error(f"Error fetching stats from JSON: {e}")
                
        return stats

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Lấy thông tin người dùng theo tên đăng nhập"""
        if self.use_mongodb:
            return self.db.users.find_one({"username": username})
        else:
            users = self._read_users_json()
            for u in users:
                if u.get("username") == username:
                    return u
            return None

    async def create_user(self, user_data: Dict) -> Optional[Dict]:
        """Tạo người dùng mới"""
        if self.use_mongodb:
            try:
                # Kiểm tra xem người dùng đã tồn tại chưa
                if self.db.users.find_one({"username": user_data.get("username")}):
                    return None
                    
                result = self.db.users.insert_one(user_data)
                user_data["_id"] = result.inserted_id
                return user_data
            except Exception as e:
                logger.error(f"Error creating user in MongoDB: {e}")
                return None
        else:
            users = self._read_users_json()
            # Kiểm tra xem người dùng đã tồn tại chưa
            if any(u.get("username") == user_data.get("username") for u in users):
                return None
                
            users.append(user_data)
            self._write_users_json(users)
            return user_data

    async def update_user_role(self, username: str, new_role: str) -> bool:
        """Cập nhật quyền của người dùng (admin/user)"""
        if self.use_mongodb:
            try:
                result = self.db.users.update_one(
                    {"username": username},
                    {"$set": {"role": new_role}}
                )
                return result.modified_count > 0
            except Exception as e:
                logger.error(f"Error updating user role in MongoDB: {e}")
                return False
        else:
            try:
                users = self._read_users_json()
                modified = False
                for u in users:
                    if u.get("username") == username:
                        u["role"] = new_role
                        modified = True
                        break
                        
                if modified:
                    self._write_users_json(users)
                    return True
                return False
            except Exception as e:
                logger.error(f"Error updating user role in JSON: {e}")
                return False



# Tạo instance toàn cục
storage_service = StorageService()
