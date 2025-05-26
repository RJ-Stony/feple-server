"""
apps/callytics/serializers.py

이 파일은 클라이언트로부터 오디오 파일과 상담자 메타데이터를 받아, Callytics 파이프라인을 트리거하는 API 엔드포인트를 정의합니다.

<설정 안내>
- settings.py에 다음 값을 추가되어 있어야 합니다.
    MEDIA_ROOT = os.getenv("MEDIA_ROOT")  # 업로드된 파일 저장 경로
    MEDIA_URL  = os.getenv("MEDIA_URL")   # 미디어 파일 서빙 URL

<사용 예시>
  POST /api/callytics/upload/  
  Content-Type: multipart/form-data  
  Body: { audio: <file>, user_id: 1, gender: "male", age: 30 }
"""

# serializers.py
from rest_framework import serializers

class FileUploadSerializer(serializers.Serializer):
    audio       = serializers.FileField(write_only=True)
    user_id     = serializers.IntegerField(write_only=True)
    gender      = serializers.CharField(max_length=10, write_only=True)
    age         = serializers.IntegerField(write_only=True)

    def validate_gender(self, value):
        if value.lower() not in ["male", "female", "other"]:
            raise serializers.ValidationError("Gender must be 'male', 'female', or 'other'.")
        return value.lower()