"""
API Views for Interview Scheduler - MongoDB compatible version
"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import pandas as pd
from datetime import datetime
from bson import ObjectId
import time

from api.mongo_models import (
    Applicant, Interviewer, Room, Schedule,
    AlgorithmConfig, ScheduleResult
)
from scheduler.genetic_algorithm import GeneticAlgorithm
from scheduler.greedy_algorithm import GreedyScheduler
from scheduler.simulated_annealing import SimulatedAnnealing


class ApplicantAPIView(APIView):
    """API endpoint for Applicants"""
    
    def get(self, request, pk=None):
        if pk:
            applicant = Applicant.find_by_id(pk)
            if applicant:
                return Response(applicant)
            return Response({'error': 'Applicant not found'}, status=status.HTTP_404_NOT_FOUND)
        
        applicants = Applicant.find_all()
        return Response(applicants)
    
    def post(self, request):
        data = request.data
        if not Applicant.validate(data):
            return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
        
        applicant_id = Applicant.create(data)
        applicant = Applicant.find_by_id(applicant_id)
        return Response(applicant, status=status.HTTP_201_CREATED)
    
    def put(self, request, pk):
        result = Applicant.update(pk, request.data)
        if result:
            applicant = Applicant.find_by_id(pk)
            return Response(applicant)
        return Response({'error': 'Applicant not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        if Applicant.delete(pk):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Applicant not found'}, status=status.HTTP_404_NOT_FOUND)


class InterviewerAPIView(APIView):
    """API endpoint for Interviewers"""
    
    def get(self, request, pk=None):
        if pk:
            interviewer = Interviewer.find_by_id(pk)
            if interviewer:
                return Response(interviewer)
            return Response({'error': 'Interviewer not found'}, status=status.HTTP_404_NOT_FOUND)
        
        interviewers = Interviewer.find_all()
        return Response(interviewers)
    
    def post(self, request):
        data = request.data
        if not Interviewer.validate(data):
            return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
        
        interviewer_id = Interviewer.create(data)
        interviewer = Interviewer.find_by_id(interviewer_id)
        return Response(interviewer, status=status.HTTP_201_CREATED)
    
    def put(self, request, pk):
        result = Interviewer.update(pk, request.data)
        if result:
            interviewer = Interviewer.find_by_id(pk)
            return Response(interviewer)
        return Response({'error': 'Interviewer not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        if Interviewer.delete(pk):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Interviewer not found'}, status=status.HTTP_404_NOT_FOUND)


class RoomAPIView(APIView):
    """API endpoint for Rooms"""
    
    def get(self, request, pk=None):
        if pk:
            room = Room.find_by_id(pk)
            if room:
                return Response(room)
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
        
        rooms = Room.find_all()
        return Response(rooms)
    
    def post(self, request):
        data = request.data
        if not Room.validate(data):
            return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
        
        room_id = Room.create(data)
        room = Room.find_by_id(room_id)
        return Response(room, status=status.HTTP_201_CREATED)
    
    def put(self, request, pk):
        result = Room.update(pk, request.data)
        if result:
            room = Room.find_by_id(pk)
            return Response(room)
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        if Room.delete(pk):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


class ScheduleAPIView(APIView):
    """API endpoint for Schedules"""
    
    def get(self, request, pk=None):
        if pk:
            schedule = Schedule.find_by_id(pk)
            if schedule:
                return Response(schedule)
            return Response({'error': 'Schedule not found'}, status=status.HTTP_404_NOT_FOUND)
        
        schedules = Schedule.find_all()
        return Response(schedules)
    
    def post(self, request):
        data = request.data
        if not Schedule.validate(data):
            return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
        
        schedule_id = Schedule.create(data)
        schedule = Schedule.find_by_id(schedule_id)
        return Response(schedule, status=status.HTTP_201_CREATED)
    
    def put(self, request, pk):
        result = Schedule.update(pk, request.data)
        if result:
            schedule = Schedule.find_by_id(pk)
            return Response(schedule)
        return Response({'error': 'Schedule not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        if Schedule.delete(pk):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Schedule not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def import_excel(request):
    """Import data from Excel file"""
    try:
        file = request.FILES.get('file')
        data_type = request.data.get('type')  # 'applicants', 'interviewers', 'rooms'
        
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Read Excel file
        df = pd.read_excel(file)
        records = df.to_dict('records')
        
        # Import based on type
        if data_type == 'applicants':
            Applicant.bulk_create(records)
        elif data_type == 'interviewers':
            Interviewer.bulk_create(records)
        elif data_type == 'rooms':
            Room.bulk_create(records)
        else:
            return Response({'error': 'Invalid data type'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': f'Successfully imported {len(records)} {data_type}',
            'count': len(records)
        })
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def dashboard_stats(request):
    """Get dashboard statistics"""
    try:
        stats = {
            'applicants': {
                'total': Applicant.count(),
                'Media': Applicant.count({'position': 'Media'}),
                'HR': Applicant.count({'position': 'HR'}),
                'Event': Applicant.count({'position': 'Event'}),
            },
            'interviewers': {
                'total': Interviewer.count(),
                'available': Interviewer.count(),
            },
            'rooms': {
                'total': Room.count(),
            },
            'schedules': {
                'total': Schedule.count(),
                'scheduled': Schedule.count({'status': 'scheduled'}),
                'completed': Schedule.count({'status': 'completed'}),
                'cancelled': Schedule.count({'status': 'cancelled'}),
            },
        }
        return Response(stats)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def run_genetic_algorithm(request):
    """Run Genetic Algorithm for scheduling"""
    try:
        config = request.data.get('config', {})
        
        # Get data from MongoDB
        applicants = Applicant.find_all()
        interviewers = Interviewer.find_all()
        rooms = Room.find_all()
        
        if not applicants or not interviewers or not rooms:
            return Response({
                'error': 'Insufficient data. Need applicants, interviewers, and rooms.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Run GA
        start_time = time.time()
        ga = GeneticAlgorithm(
            applicants=applicants,
            interviewers=interviewers,
            rooms=rooms,
            config=config
        )
        best_solution, best_fitness, fitness_details, generations = ga.run()
        execution_time = time.time() - start_time
        
        # Save result
        result_data = {
            'algorithm': 'GA',
            'fitness_score': best_fitness,
            'conflict_score': fitness_details.get('conflict', 0),
            'idle_time_score': fitness_details.get('idle_time', 0),
            'fairness_score': fitness_details.get('fairness', 0),
            'matching_score': fitness_details.get('matching', 0),
            'room_usage_score': fitness_details.get('room_usage', 0),
            'execution_time': execution_time,
            'generations': generations,
            'schedule_data': best_solution,
            'config_used': config,
            'created_at': datetime.now()
        }
        
        result_id = ScheduleResult.create(result_data)
        result = ScheduleResult.find_by_id(result_id)
        
        return Response(result)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def run_greedy_algorithm(request):
    """Run Greedy Algorithm for scheduling"""
    try:
        # Get data from MongoDB
        applicants = Applicant.find_all()
        interviewers = Interviewer.find_all()
        rooms = Room.find_all()
        
        if not applicants or not interviewers or not rooms:
            return Response({
                'error': 'Insufficient data. Need applicants, interviewers, and rooms.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Run Greedy
        start_time = time.time()
        greedy = GreedyScheduler(applicants, interviewers, rooms)
        solution = greedy.schedule()
        execution_time = time.time() - start_time
        
        # Calculate fitness (you'll need to implement this)
        fitness_score = 0  # Calculate from solution
        
        # Save result
        result_data = {
            'algorithm': 'GREEDY',
            'fitness_score': fitness_score,
            'conflict_score': 0,
            'idle_time_score': 0,
            'fairness_score': 0,
            'matching_score': 0,
            'room_usage_score': 0,
            'execution_time': execution_time,
            'generations': None,
            'schedule_data': solution,
            'config_used': {},
            'created_at': datetime.now()
        }
        
        result_id = ScheduleResult.create(result_data)
        result = ScheduleResult.find_by_id(result_id)
        
        return Response(result)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def run_simulated_annealing(request):
    """Run Simulated Annealing for scheduling"""
    try:
        config = request.data.get('config', {})
        
        # Get data from MongoDB
        applicants = Applicant.find_all()
        interviewers = Interviewer.find_all()
        rooms = Room.find_all()
        
        if not applicants or not interviewers or not rooms:
            return Response({
                'error': 'Insufficient data. Need applicants, interviewers, and rooms.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Run SA
        start_time = time.time()
        sa = SimulatedAnnealing(
            applicants=applicants,
            interviewers=interviewers,
            rooms=rooms,
            config=config
        )
        best_solution, best_fitness = sa.run()
        execution_time = time.time() - start_time
        
        # Save result
        result_data = {
            'algorithm': 'SA',
            'fitness_score': best_fitness,
            'conflict_score': 0,
            'idle_time_score': 0,
            'fairness_score': 0,
            'matching_score': 0,
            'room_usage_score': 0,
            'execution_time': execution_time,
            'generations': None,
            'schedule_data': best_solution,
            'config_used': config,
            'created_at': datetime.now()
        }
        
        result_id = ScheduleResult.create(result_data)
        result = ScheduleResult.find_by_id(result_id)
        
        return Response(result)
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def algorithm_results(request):
    """Get recent algorithm results"""
    try:
        results = ScheduleResult.find_all(limit=20)
        return Response(results)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AlgorithmConfigAPIView(APIView):
    """API endpoint for Algorithm Configuration"""
    
    def get(self, request, pk=None):
        if pk:
            config = AlgorithmConfig.find_by_id(pk)
            if config:
                return Response(config)
            return Response({'error': 'Config not found'}, status=status.HTTP_404_NOT_FOUND)
        
        configs = AlgorithmConfig.find_all()
        return Response(configs)
    
    def post(self, request):
        data = request.data
        if not AlgorithmConfig.validate(data):
            return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)
        
        config_id = AlgorithmConfig.create(data)
        config = AlgorithmConfig.find_by_id(config_id)
        return Response(config, status=status.HTTP_201_CREATED)
    
    def put(self, request, pk):
        result = AlgorithmConfig.update(pk, request.data)
        if result:
            config = AlgorithmConfig.find_by_id(pk)
            return Response(config)
        return Response({'error': 'Config not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        if AlgorithmConfig.delete(pk):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Config not found'}, status=status.HTTP_404_NOT_FOUND)
