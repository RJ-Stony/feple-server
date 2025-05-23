"""
apps/callytics/models.py

이 파일은 Callytics 모델 분석 결과를 저장하기 위한 Django 모델 정의입니다.
각 클래스와 필드에 대한 상세 설명과, 프레임(frame) 단위 데이터를 초(second)로 변환하는 유틸 프로퍼티를 포함합니다.

<설정 안내>
- settings.py에 다음 값을 추가해주세요.
    HOP_LENGTH = 512   # 분석 시 프레임 간 hop length
    # 샘플링 레이트(sr)는 분석 시 입력된 audio 파일의 rate 필드를 사용합니다.

< 마이그레이션 안내 >
1) 모델 변경사항 반영 파일 생성할 때에는
   $ python manage.py makemigrations callytics
2) 실제 DB에 테이블 생성/변경할 때에는
   $ python manage.py migrate

다른 파일에 사용 예시
  from apps.callytics.models import File, Utterance, Topic
  # API로부터 받은 JSON을 이 모델에 매핑해 저장할 수 있습니다.
"""

from django.db import models
from django.conf import settings


class Topic(models.Model):
    """
    대화 토픽 정보를 저장하는 테이블
    - Django는 각 모델에 기본 키(primary key)로 id라는 AutoField를 자동 추가하기 때문에 id는 명시하지 않습니다.
    - name: 토픽 이름 (예를 들어 '상품 문의', '결제 문제' 등)
    """
    name = models.CharField(max_length=100, verbose_name="토픽 이름")

    def __str__(self):
        return self.name


class File(models.Model):
    """
    업로드된 상담 오디오 파일의 분석 결과를 저장하는 테이블
    주요 컬럼 설명
      - name        : 파일 이름(확장자 제외)
      - topic       : Topic 테이블과의 외래키
      - extension   : 파일 확장자('.wav', '.mp3' 등)
      - path        : 저장된 파일 경로
      - rate        : 샘플링 레이트(Hz, 초 단위 변환할 때 sr로 사용)
      - bit_depth   : 비트 깊이(16, 24 등)
      - channels    : 채널 수(1=모노, 2=스테레오)
      - duration    : 총 프레임 수 (frame 단위, 초 아님)
      - zero_cross  : 음성의 거칠기 판단 지표
      - spec_cent   : 음색 중심 주파수 지표
      - spec_bw     : 스펙트럼 분산도 지표
      - spec_flat   : 톤성 vs 잡음성 비율 지표
      - rolloff     : 스펙트럼 누적 에너지의 경계 주파수
      - chroma_stft : 12개 음계별 에너지 강도
      - spec_contr  : 주파수 대역 간 강도 대비
      - tonnetz     : 조화적 관계 측정 지표
      - mfcc        : MFCC 계수 0~13
      - summary     : LLM이 생성한 통화 요약 텍스트
      - conflict    : 갈등 플래그(True=갈등 있음)
      - silence     : 침묵 구간 총 프레임 수
      - created_at  : 분석 시각
    프레임 단위 수치는 duration_seconds, silence_seconds 프로퍼티로 초 단위 변환 가능
    """
    name        = models.CharField(max_length=200, verbose_name="파일 이름")
    topic       = models.ForeignKey(Topic, on_delete=models.CASCADE, verbose_name="관련 토픽")
    extension   = models.CharField(max_length=10, verbose_name="확장자")
    path        = models.TextField(verbose_name="파일 경로")
    rate        = models.IntegerField(verbose_name="샘플링 레이트 (Hz)")
    bit_depth   = models.IntegerField(verbose_name="비트 깊이")
    channels    = models.IntegerField(verbose_name="채널 수")
    duration    = models.BigIntegerField(verbose_name="전체 프레임 수")
    min_freq    = models.IntegerField(verbose_name="최소 주파수 (Hz)")
    max_freq    = models.IntegerField(verbose_name="최대 주파수 (Hz)")
    rms_loud    = models.FloatField(verbose_name="평균 음량 RMS")
    zero_cross  = models.BigIntegerField(verbose_name="영점 교차 프레임 수")
    spec_cent   = models.BigIntegerField(verbose_name="스펙트럼 무게중심 프레임 수")
    spec_bw     = models.BigIntegerField(verbose_name="스펙트럼 대역폭 프레임 수")
    spec_flat   = models.BigIntegerField(verbose_name="스펙트럼 평탄도 프레임 수")
    rolloff     = models.BigIntegerField(verbose_name="롤-오프 프레임 수")
    chroma_stft = models.JSONField(verbose_name="크로마 STFT (12d per frame)")
    spec_contr  = models.JSONField(verbose_name="스펙트럴 대비")
    tonnetz     = models.JSONField(verbose_name="Tonnetz 특성")
    mfcc        = models.JSONField(verbose_name="MFCC 계수 0~13")
    summary     = models.TextField(null=True, blank=True, verbose_name="통화 요약 텍스트")
    conflict    = models.BooleanField(default=False, verbose_name="갈등 플래그", choices=[(False, "없음"), (True, "있음")])
    silence     = models.BigIntegerField(verbose_name="침묵 프레임 수")
    created_at  = models.DateTimeField(auto_now_add=True, verbose_name="분석 시각")

    def __str__(self):
        return f"{self.name} ({self.topic})"

    @property
    def duration_seconds(self) -> float:
        """
        전체 프레임(duration)을 초 단위로 변환
        계산: duration_frames * hop_length / sampling_rate
        hop_length: settings.HOP_LENGTH (기본 512)
        """
        hop_length = getattr(settings, "HOP_LENGTH", 512)
        sr = self.rate
        return self.duration * hop_length / sr

    @property
    def silence_seconds(self) -> float:
        """
        침묵 프레임(silence)을 초 단위로 변환
        """
        hop_length = getattr(settings, "HOP_LENGTH", 512)
        sr = self.rate
        return self.silence * hop_length / sr


class Utterance(models.Model):
    """
    발화(Unit of speech) 단위로 분석된 결과 저장
    컬럼 설명
      - file       : File 테이블과의 외래키
      - speaker    : 발화 주체(agent/customer)
      - sequence   : 파일 내 발화 순번
      - start_time : 시작 프레임 번호
      - end_time   : 종료 프레임 번호
      - content    : 발화 내용 텍스트
      - sentiment  : 감정 레이블
      - profane    : 비속어 사용 여부 플래그
    duration_seconds 프로퍼티로 발화 길이 초 단위 확인 가능
    """
    file       = models.ForeignKey(File, on_delete=models.CASCADE, verbose_name="관련 파일")
    speaker    = models.CharField(max_length=10, choices=[("agent", "agent"), ("customer", "customer")], verbose_name="발화자")
    sequence   = models.IntegerField(verbose_name="발화 순번")
    start_time = models.BigIntegerField(verbose_name="시작 프레임 번호")
    end_time   = models.BigIntegerField(verbose_name="종료 프레임 번호")
    content    = models.TextField(verbose_name="발화 내용")
    sentiment  = models.CharField(max_length=10, verbose_name="감정 레이블")
    profane    = models.BooleanField(default=False, verbose_name="비속어 플래그")

    def __str__(self):
        return f"Utterance {self.file} of File {self.file.name})"

    @property
    def duration_seconds(self) -> float:
        """
        발화 길이(frame 수)를 초 단위로 변환
        """
        hop_length = getattr(settings, "HOP_LENGTH", 512)
        sr = self.file.rate
        return (self.end_time - self.start_time) * hop_length / sr
