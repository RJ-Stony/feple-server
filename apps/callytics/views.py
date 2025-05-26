"""
apps/callytics/views.py

이 파일은 클라이언트로부터 오디오 파일과 상담자 메타데이터를 받아,
Callytics 파이프라인을 트리거하는 API 엔드포인트를 정의합니다.

<설정 안내>
- settings.py에 다음 값을 추가되어 있어야 합니다.
    MEDIA_ROOT = os.getenv("MEDIA_ROOT")  # 업로드된 파일 저장 경로
    MEDIA_URL  = os.getenv("MEDIA_URL")   # 미디어 파일 서빙 URL

<사용 예시>
  POST /api/callytics/upload/  
  Content-Type: multipart/form-data  
  Body: { audio: <file>, user_id: 1, gender: "male", age: 30, topic_name: "상품 문의" }
"""

import os
from uuid import uuid4
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FileUploadSerializer
from .tasks import run_callytics_pipeline

class FileUploadView(APIView):
    """
    상담 오디오 + 메타데이터를 받아 Callytics 파이프라인을 실행하는 API
    - POST 요청으로 audio, user_id, gender, age, topic_name을 multipart/form-data로 받음
    - 파일을 MEDIA_ROOT/uploads/UUID.ext 경로에 저장
    - run_callytics_pipeline 태스크에 파일 경로와 메타데이터 dict 전달
    """
    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 업로드된 오디오 파일 저장
        audio_file = serializer.validated_data['audio']
        ext = os.path.splitext(audio_file.name)[1]
        filename = f"uploads/{uuid4().hex}{ext}"
        saved_path = default_storage.save(filename, audio_file)
        full_path = os.path.join(settings.MEDIA_ROOT, saved_path)

        # 메타데이터 구성
        metadata = {
            'user_id':    serializer.validated_data['user_id'],
            'gender':     serializer.validated_data['gender'],
            'age':        serializer.validated_data['age'],
        }

        # 비동기로 파이프라인 실행
        run_callytics_pipeline.delay(full_path, metadata)

        return Response({'status': 'processing'}, status=status.HTTP_202_ACCEPTED)