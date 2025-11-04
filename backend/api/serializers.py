"""
DRF Serializers for API
"""
from rest_framework import serializers
from api.models import (
    Applicant, Interviewer, Room, Schedule, 
    AlgorithmConfig, ScheduleResult
)


class ApplicantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicant
        fields = '__all__'
        read_only_fields = ('_id', 'created_at', 'updated_at')


class InterviewerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interviewer
        fields = '__all__'
        read_only_fields = ('_id', 'created_at', 'updated_at')


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'
        read_only_fields = ('_id', 'created_at', 'updated_at')


class ScheduleSerializer(serializers.ModelSerializer):
    applicant_detail = ApplicantSerializer(source='applicant', read_only=True)
    interviewer_detail = InterviewerSerializer(source='interviewer', read_only=True)
    room_detail = RoomSerializer(source='room', read_only=True)
    
    class Meta:
        model = Schedule
        fields = '__all__'
        read_only_fields = ('_id', 'created_at', 'updated_at')


class AlgorithmConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlgorithmConfig
        fields = '__all__'
        read_only_fields = ('_id', 'created_at', 'updated_at')


class ScheduleResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScheduleResult
        fields = '__all__'
        read_only_fields = ('_id', 'created_at')


class ExcelImportSerializer(serializers.Serializer):
    """Serializer for Excel import"""
    file = serializers.FileField()
    sheet_type = serializers.ChoiceField(
        choices=['applicants', 'interviewers', 'rooms', 'all']
    )


class RunAlgorithmSerializer(serializers.Serializer):
    """Serializer for running scheduling algorithm"""
    algorithm = serializers.ChoiceField(
        choices=['GA', 'GREEDY', 'SA', 'ALL'],
        default='GA'
    )
    config = serializers.JSONField(required=False)


class CompareAlgorithmsSerializer(serializers.Serializer):
    """Serializer for comparing multiple algorithms"""
    algorithms = serializers.ListField(
        child=serializers.ChoiceField(choices=['GA', 'GREEDY', 'SA']),
        default=['GA', 'GREEDY', 'SA']
    )
    config = serializers.JSONField(required=False)
