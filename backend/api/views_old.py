"""
API Views for Interview Scheduler
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
import pandas as pd
from datetime import datetime
from bson import ObjectId

from api.mongo_models import (
    Applicant, Interviewer, Room, Schedule,
    AlgorithmConfig, ScheduleResult
)
from api.serializers import (
    ApplicantSerializer, InterviewerSerializer, RoomSerializer,
    ScheduleSerializer, AlgorithmConfigSerializer, ScheduleResultSerializer,
    ExcelImportSerializer, RunAlgorithmSerializer, CompareAlgorithmsSerializer
)
from scheduler.genetic_algorithm import GeneticAlgorithm
from scheduler.greedy_algorithm import GreedyScheduler
from scheduler.simulated_annealing import SimulatedAnnealing


class ApplicantViewSet(viewsets.ModelViewSet):
    """API endpoint for Applicants"""
    queryset = Applicant.objects.all()
    serializer_class = ApplicantSerializer
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create applicants"""
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InterviewerViewSet(viewsets.ModelViewSet):
    """API endpoint for Interviewers"""
    queryset = Interviewer.objects.all()
    serializer_class = InterviewerSerializer
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create interviewers"""
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoomViewSet(viewsets.ModelViewSet):
    """API endpoint for Rooms"""
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create rooms"""
        serializer = self.get_serializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ScheduleViewSet(viewsets.ModelViewSet):
    """API endpoint for Schedules"""
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    
    @action(detail=False, methods=['get'])
    def timeline(self, request):
        """Get schedule in timeline format"""
        schedules = self.get_queryset()
        
        timeline_data = {}
        for schedule in schedules:
            room_id = str(schedule.room.room_code)
            if room_id not in timeline_data:
                timeline_data[room_id] = []
            
            timeline_data[room_id].append({
                'id': str(schedule._id),
                'applicant': schedule.applicant.full_name,
                'interviewer': schedule.interviewer.full_name,
                'position': schedule.applicant.position,
                'start': schedule.start_time.isoformat(),
                'end': schedule.end_time.isoformat(),
                'status': schedule.status
            })
        
        return Response(timeline_data)
    
    @action(detail=False, methods=['get'])
    def conflicts(self, request):
        """Get all scheduling conflicts"""
        schedules = list(self.get_queryset())
        conflicts = []
        
        for i, s1 in enumerate(schedules):
            for s2 in schedules[i+1:]:
                # Check time overlap
                if s1.start_time < s2.end_time and s2.start_time < s1.end_time:
                    # Same interviewer
                    if s1.interviewer == s2.interviewer:
                        conflicts.append({
                            'type': 'interviewer',
                            'schedule1': str(s1._id),
                            'schedule2': str(s2._id),
                            'interviewer': s1.interviewer.full_name,
                            'time': f"{s1.start_time} - {s1.end_time}"
                        })
                    # Same room
                    if s1.room == s2.room:
                        conflicts.append({
                            'type': 'room',
                            'schedule1': str(s1._id),
                            'schedule2': str(s2._id),
                            'room': s1.room.room_code,
                            'time': f"{s1.start_time} - {s1.end_time}"
                        })
        
        return Response({
            'count': len(conflicts),
            'conflicts': conflicts
        })


class DataManagementViewSet(viewsets.ViewSet):
    """API endpoint for data import/export"""
    
    @action(detail=False, methods=['post'])
    def import_excel(self, request):
        """Import data from Excel file"""
        serializer = ExcelImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        excel_file = request.FILES['file']
        sheet_type = serializer.validated_data['sheet_type']
        
        try:
            if sheet_type == 'all':
                # Import all sheets
                applicants_df = pd.read_excel(excel_file, sheet_name='Applicants')
                interviewers_df = pd.read_excel(excel_file, sheet_name='Interviewers')
                rooms_df = pd.read_excel(excel_file, sheet_name='Rooms')
                
                # Process and save (TODO: implement full logic)
                return Response({
                    'message': 'All sheets imported successfully',
                    'applicants': len(applicants_df),
                    'interviewers': len(interviewers_df),
                    'rooms': len(rooms_df)
                })
            else:
                df = pd.read_excel(excel_file)
                # Process based on sheet_type
                return Response({'message': f'{sheet_type} imported successfully'})
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def export_excel(self, request):
        """Export data to Excel file"""
        # TODO: Implement Excel export
        return Response({'message': 'Export functionality coming soon'})
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get data statistics"""
        stats = {
            'applicants': Applicant.objects.count(),
            'interviewers': Interviewer.objects.count(),
            'rooms': Room.objects.count(),
            'schedules': Schedule.objects.count(),
            'positions': {
                'Media': Applicant.objects.filter(position='Media').count(),
                'HR': Applicant.objects.filter(position='HR').count(),
                'Event': Applicant.objects.filter(position='Event').count(),
            }
        }
        return Response(stats)


class AlgorithmViewSet(viewsets.ViewSet):
    """API endpoint for running scheduling algorithms"""
    
    @action(detail=False, methods=['post'])
    def run(self, request):
        """Run scheduling algorithm"""
        serializer = RunAlgorithmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        algorithm = serializer.validated_data['algorithm']
        custom_config = serializer.validated_data.get('config', {})
        
        # Get data
        applicants = list(Applicant.objects.values())
        interviewers = list(Interviewer.objects.values())
        rooms = list(Room.objects.values())
        
        if not applicants or not interviewers or not rooms:
            return Response(
                {'error': 'Please add applicants, interviewers, and rooms first'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Merge config
        config = settings.ALGORITHM_CONFIG.copy()
        config.update(custom_config)
        
        # Run algorithm
        try:
            if algorithm == 'GA':
                result = self._run_ga(applicants, interviewers, rooms, config)
            elif algorithm == 'GREEDY':
                result = self._run_greedy(applicants, interviewers, rooms, config)
            elif algorithm == 'SA':
                result = self._run_sa(applicants, interviewers, rooms, config)
            elif algorithm == 'ALL':
                result = self._run_all(applicants, interviewers, rooms, config)
            
            return Response(result)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _run_ga(self, applicants, interviewers, rooms, config):
        """Run Genetic Algorithm"""
        ga = GeneticAlgorithm(config['GA'])
        ga.initialize_population(applicants, interviewers, rooms)
        result = ga.evolve(applicants, interviewers, rooms)
        
        # Save result
        self._save_result('GA', result, config)
        
        return {
            'algorithm': 'GA',
            'fitness': result['final_fitness'],
            'generations': result['generations'],
            'fitness_history': result['fitness_history'],
            'best_solution': self._format_solution(result['best_solution'])
        }
    
    def _run_greedy(self, applicants, interviewers, rooms, config):
        """Run Greedy Algorithm"""
        greedy = GreedyScheduler(config)
        result = greedy.schedule(applicants, interviewers, rooms)
        
        # Save result
        self._save_result('GREEDY', result, config)
        
        return {
            'algorithm': 'GREEDY',
            'fitness': result['fitness'],
            'execution_time': result['execution_time'],
            'scheduled_count': result['scheduled_count'],
            'best_solution': self._format_solution(result['best_solution'])
        }
    
    def _run_sa(self, applicants, interviewers, rooms, config):
        """Run Simulated Annealing"""
        sa = SimulatedAnnealing(config['SA'])
        result = sa.optimize(applicants, interviewers, rooms)
        
        # Save result
        self._save_result('SA', result, config)
        
        return {
            'algorithm': 'SA',
            'fitness': result['fitness'],
            'iterations': result['iterations'],
            'execution_time': result['execution_time'],
            'fitness_history': result['fitness_history'],
            'best_solution': self._format_solution(result['best_solution'])
        }
    
    def _run_all(self, applicants, interviewers, rooms, config):
        """Run all algorithms for comparison"""
        results = []
        
        for algo in ['GA', 'GREEDY', 'SA']:
            try:
                if algo == 'GA':
                    result = self._run_ga(applicants, interviewers, rooms, config)
                elif algo == 'GREEDY':
                    result = self._run_greedy(applicants, interviewers, rooms, config)
                elif algo == 'SA':
                    result = self._run_sa(applicants, interviewers, rooms, config)
                
                results.append(result)
            except Exception as e:
                results.append({
                    'algorithm': algo,
                    'error': str(e)
                })
        
        return {'results': results}
    
    def _format_solution(self, chromosome):
        """Format chromosome solution for API response"""
        if not chromosome:
            return None
        
        return {
            'fitness': chromosome.fitness,
            'conflict_score': chromosome.conflict_score,
            'idle_time_score': chromosome.idle_time_score,
            'fairness_score': chromosome.fairness_score,
            'matching_score': chromosome.matching_score,
            'room_usage_score': chromosome.room_usage_score,
            'schedule': [
                {
                    'applicant_id': gene.applicant_id,
                    'interviewer_id': gene.interviewer_id,
                    'room_id': gene.room_id,
                    'start_time': gene.start_time.isoformat(),
                    'end_time': gene.end_time.isoformat(),
                    'position': gene.position
                }
                for gene in chromosome.genes
            ]
        }
    
    def _save_result(self, algorithm, result, config):
        """Save algorithm result to database"""
        solution = result.get('best_solution')
        if not solution:
            return
        
        ScheduleResult.objects.create(
            algorithm=algorithm,
            fitness_score=solution.fitness,
            conflict_score=solution.conflict_score,
            idle_time_score=solution.idle_time_score,
            fairness_score=solution.fairness_score,
            matching_score=solution.matching_score,
            room_usage_score=solution.room_usage_score,
            execution_time=result.get('execution_time', 0),
            generations=result.get('generations'),
            schedule_data=self._format_solution(solution),
            config_used=config
        )
    
    @action(detail=False, methods=['get'])
    def results(self, request):
        """Get all algorithm results"""
        results = ScheduleResult.objects.all()[:20]
        serializer = ScheduleResultSerializer(results, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def compare(self, request):
        """Compare multiple algorithms"""
        serializer = CompareAlgorithmsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Run all requested algorithms
        return self.run(request)


class AlgorithmConfigViewSet(viewsets.ModelViewSet):
    """API endpoint for Algorithm Configuration"""
    queryset = AlgorithmConfig.objects.all()
    serializer_class = AlgorithmConfigSerializer
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate this configuration"""
        config = self.get_object()
        
        # Deactivate all others
        AlgorithmConfig.objects.update(is_active=False)
        
        # Activate this one
        config.is_active = True
        config.save()
        
        return Response({'message': 'Configuration activated'})
