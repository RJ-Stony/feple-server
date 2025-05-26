"""
apps/consultlytics/models.py

이 파일은 LightGBM 기반 'Consultlytics' 서비스의 결과를 저장하기 위해
다중 테이블로 정규화된 Django 모델 정의를 담고 있습니다.
각 테이블은 상담 세션(Session), 명사 분석(TopNoun), 감정 점수(EmotionScore),
카테고리(Category), 스크립트 지표(ScriptMetric), 최종 결과(ResultClassification)를
별도 관리하며, 관계 설정 및 필드 설명을 자세히 작성했습니다.

<마이그레이션 안내>
1) 앱 생성·등록 후
   $ python manage.py makemigrations consultlytics
2) 테이블 생성/변경 반영
   $ python manage.py migrate

<사용 예시>
  from apps.consultlytics.models import Session, EmotionScore, ResultClassification
  # 모델 인스턴스를 생성·조회하여 ORM으로 데이터 관리 가능
"""

from django.db import models


class Session(models.Model):
    """
    상담 세션의 기본 정보 저장
      - session_id       : 상담 세션 고유 ID
      - speech_count     : 총 발화(turn) 수
      - consulting_text  : 전체 상담 텍스트
      - asr_segments     : ASR 분할 발화 JSON
    """
    session_id      = models.CharField(max_length=100, primary_key=True, verbose_name="세션 ID", help_text="상담 세션 고유 식별자")
    speech_count    = models.IntegerField(verbose_name="총 발화 수", help_text="상담 세션에서 인식된 총 발화 수")
    consulting_text= models.TextField(verbose_name="상담 텍스트", help_text="원본 상담 대화 전체 내용")
    asr_segments    = models.JSONField(verbose_name="ASR 세그먼트", help_text="고객/상담사 발화를 분리한 JSON 리스트")
    created_at      = models.DateTimeField(auto_now_add=True, verbose_name="분석 시각")

    def __str__(self):
        return f"Session {self.session_id}"


class TopNoun(models.Model):
    """
    세션별 주요 명사 Top10 저장
      - session (FK)
      - nouns   : 명사 리스트(JSON)
    """
    session = models.ForeignKey(Session, on_delete=models.CASCADE, verbose_name="세션", related_name="top_nouns")
    nouns   = models.JSONField(verbose_name="Top10 명사", help_text="추출된 상위 10개 명사 리스트")

    def __str__(self):
        return f"Top Nouns for {self.session.session_id}"


class EmotionScore(models.Model):
    """
    고객/상담사별 1~5★ 감정 비율 및 평균·레이블 저장
      - session          : 세션 FK
      - actor            : 'customer' or 'agent'
      - star1~star5      : 1★~5★ 비율 (float)
      - avg_score        : 평균 감정 점수
      - label            : 분류된 감정 레이블
    """
    ACTOR_CHOICES = [("customer", "고객"), ("agent", "상담사")]

    session   = models.ForeignKey(Session, on_delete=models.CASCADE, verbose_name="세션", related_name="emotion_scores")
    actor     = models.CharField(max_length=10, choices=ACTOR_CHOICES, verbose_name="행위자", help_text="점수 대상: 고객 또는 상담사")
    star1     = models.FloatField(verbose_name="1★ 비율")
    star2     = models.FloatField(verbose_name="2★ 비율")
    star3     = models.FloatField(verbose_name="3★ 비율")
    star4     = models.FloatField(verbose_name="4★ 비율")
    star5     = models.FloatField(verbose_name="5★ 비율")
    avg_score = models.FloatField(verbose_name="평균 점수", help_text="1~5★ 비율의 가중 평균")
    label     = models.CharField(max_length=50, verbose_name="감정 레이블", help_text="평균 점수 기반 분류 라벨")

    class Meta:
        unique_together = ("session", "actor")

    def __str__(self):
        return f"Emotion({self.actor}) @ {self.session.session_id}"


class Category(models.Model):
    """
    상담/유형 카테고리 및 결과 분류 정보 저장
      - session            : 세션 FK
      - mid_category       : 중분류 이름
      - content_category   : 상담 유형 카테고리 이름
      - mid_category_id    : 중분류 ID
      - result_label       : 최종 결과 레이블
      - label_id           : 결과 레이블 ID
    """
    session          = models.OneToOneField(Session, on_delete=models.CASCADE, verbose_name="세션", related_name="category")
    mid_category     = models.CharField(max_length=100, verbose_name="상담 카테고리")
    content_category = models.CharField(max_length=100, verbose_name="상담 유형")
    mid_category_id  = models.IntegerField(verbose_name="카테고리 ID")
    result_label     = models.CharField(max_length=50, verbose_name="최종 결과 레이블")
    label_id         = models.IntegerField(verbose_name="결과 레이블 ID")

    def __str__(self):
        return f"Category @ {self.session.session_id}"


class ScriptMetric(models.Model):
    """
    상담사 스크립트 및 커뮤니케이션 지표 저장
      - session                  : 세션 FK
      - script_phrase_ratio      : 스크립트 준수 비율
      - honorific_ratio          : 존댓말 비율
      - positive_word_ratio      : 긍정 단어 비율
      - euphonious_word_ratio    : 완곡어 사용 비율
      - confirmation_ratio       : 확인 멘트 비율
      - empathy_ratio            : 공감 멘트 비율
      - apology_ratio            : 사과 멘트 비율
      - request_ratio            : 의뢰 멘트 비율
      - alternative_count        : 대안 제안 횟수
      - conflict_flag            : 갈등 발생 여부
      - manual_compliance_ratio  : 매뉴얼 준수 비율
    """
    session               = models.OneToOneField(Session, on_delete=models.CASCADE, verbose_name="세션", related_name="script_metrics")
    script_phrase_ratio   = models.FloatField(verbose_name="스크립트 준수 비율")
    honorific_ratio       = models.FloatField(verbose_name="존댓말 비율")
    positive_word_ratio   = models.FloatField(verbose_name="긍정 단어 비율")
    euphonious_word_ratio = models.FloatField(verbose_name="완곡어 사용 비율")
    confirmation_ratio    = models.FloatField(verbose_name="확인 멘트 비율")
    empathy_ratio         = models.FloatField(verbose_name="공감 멘트 비율")
    apology_ratio         = models.FloatField(verbose_name="사과 멘트 비율")
    request_ratio         = models.FloatField(verbose_name="의뢰 멘트 비율")
    alternative_count     = models.IntegerField(verbose_name="대안 제안 횟수")
    conflict_flag         = models.BooleanField(default=False, verbose_name="갈등 여부", choices=[(False, "없음"),(True, "있음")])
    manual_compliance_ratio = models.FloatField(verbose_name="매뉴얼 준수 비율")

    def __str__(self):
        return f"ScriptMetric @ {self.session.session_id}"


class ResultClassification(models.Model):
    """
    예측 모델의 최종 결과 저장
      - session     : 세션 FK
      - label       : 만족/미흡/추가 상담 필요/해결 불가
    """
    session = models.OneToOneField(Session, on_delete=models.CASCADE, verbose_name="세션", related_name="result")
    label   = models.CharField(max_length=50, verbose_name="결과 레이블", help_text="만족, 미흡, 추가 상담 필요, 해결 불가")

    def __str__(self):
        return f"Result {self.label} @ {self.session.session_id}"


class Meta:
    verbose_name = "Consultlytics 모델 결과"
    verbose_name_plural = "Consultlytics 모델 결과들"
