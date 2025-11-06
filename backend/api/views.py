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
    Position, InterviewSession,
    Applicant, Interviewer, Room, Schedule,
    AlgorithmConfig, ScheduleResult
)
from scheduler.genetic_algorithm import GeneticAlgorithm
from scheduler.greedy_algorithm import GreedyScheduler
from scheduler.simulated_annealing import SimulatedAnnealing

# Utilities
def to_json_safe(value):
    """Recursively convert ObjectId and datetime to JSON-safe primitives."""
    from bson import ObjectId
    from datetime import datetime as _dt

    if isinstance(value, dict):
        return {k: to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return tuple(to_json_safe(v) for v in value)
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, _dt):
        return value.isoformat()
    return value


def normalize_data(items):
    """Add 'id' alias for '_id' to make data compatible with schedulers"""
    for item in items:
        if '_id' in item:
            item['id'] = item['_id']
    return items


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
        
        # Enrich schedules with related details for frontend table view
        schedules = Schedule.find_all()
        if not schedules:
            return Response([])
        
        # Build lookup maps
        applicants = {a.get('_id'): a for a in Applicant.find_all()}
        interviewers = {i.get('_id'): i for i in Interviewer.find_all()}
        rooms = {r.get('_id'): r for r in Room.find_all()}
        
        for s in schedules:
            aid = s.get('applicant_id')
            iid = s.get('interviewer_id')
            rid = s.get('room_id')
            s['applicant_detail'] = applicants.get(aid)
            s['interviewer_detail'] = interviewers.get(iid)
            s['room_detail'] = rooms.get(rid)
            # default status if missing
            if 'status' not in s:
                s['status'] = 'scheduled'
        
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


@api_view(['GET'])
def get_schedule_timeline(request):
    """Get schedules formatted for timeline view"""
    try:
        schedules = Schedule.find_all()
        if not schedules:
            return Response({})
        
        # Preload lookups
        applicants = {a.get('_id'): a for a in Applicant.find_all()}
        interviewers = {i.get('_id'): i for i in Interviewer.find_all()}
        rooms = {r.get('_id'): r for r in Room.find_all()}
        
        # Group by room (use room code/name if available)
        timeline_grouped = {}
        for s in schedules:
            rid = s.get('room_id')
            room = rooms.get(rid) or {}
            room_key = room.get('room_code') or room.get('room_name') or rid
            if room_key not in timeline_grouped:
                timeline_grouped[room_key] = []
            
            aid = s.get('applicant_id')
            iid = s.get('interviewer_id')
            applicant = applicants.get(aid) or {}
            interviewer = interviewers.get(iid) or {}
            
            timeline_grouped[room_key].append({
                'id': s.get('_id'),
                'applicant': applicant.get('full_name', 'Applicant'),
                'interviewer': interviewer.get('full_name', 'Interviewer'),
                'position': applicant.get('position') or s.get('position'),
                'start': s.get('start_time'),
                'end': s.get('end_time'),
                'status': s.get('status', 'scheduled'),
            })
        
        return Response(timeline_grouped)
    except Exception as e:
        print(f"Error in get_schedule_timeline: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


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
def export_schedules(request):
    """Export schedules to Excel file"""
    try:
        from django.http import HttpResponse
        import io
        
        # Get all schedules
        schedules = Schedule.find_all()
        
        if not schedules:
            return Response({'error': 'No schedules to export'}, status=status.HTTP_404_NOT_FOUND)
        
        # Convert to DataFrame
        df = pd.DataFrame(schedules)
        
        # Remove MongoDB _id if present
        if '_id' in df.columns:
            df = df.drop(columns=['_id'])
        
        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Schedules', index=False)
        
        output.seek(0)
        
        # Create HTTP response
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="schedules_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
        
        return response
    
    except Exception as e:
        print(f"❌ Export error: {e}")
        import traceback
        traceback.print_exc()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def dashboard_stats(request):
    """Get dashboard statistics"""
    try:
        from interview_scheduler.settings import mongodb
        
        if mongodb is None:
            return Response(
                {'error': 'MongoDB not connected'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
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
        import traceback
        print(f"Error in dashboard_stats: {str(e)}")
        print(traceback.format_exc())
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def run_genetic_algorithm(request):
    """Run Genetic Algorithm for scheduling"""
    try:
        config = request.data.get('config', {})
        
        # Get data from MongoDB
        applicants = normalize_data(Applicant.find_all())
        interviewers = normalize_data(Interviewer.find_all())
        rooms = normalize_data(Room.find_all())
        
        if not applicants or not interviewers or not rooms:
            return Response({
                'error': 'Insufficient data. Need applicants, interviewers, and rooms.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Run GA
        start_time = time.time()
        ga = GeneticAlgorithm(config=config)
        result = ga.evolve(applicants, interviewers, rooms)
        
        # Extract results
        best_chromosome = result.get('best_solution')
        best_fitness = result.get('final_fitness', 0)
        generations = result.get('generations', 0)
        execution_time = time.time() - start_time
        
        print(f"📊 Views: best_chromosome = {best_chromosome}")
        print(f"📊 Views: has genes attr = {hasattr(best_chromosome, 'genes') if best_chromosome else False}")
        if best_chromosome and hasattr(best_chromosome, 'genes'):
            print(f"📊 Views: genes count = {len(best_chromosome.genes)}")
        
        # Convert Chromosome genes to schedule data
        schedule_data = []
        if best_chromosome and hasattr(best_chromosome, 'genes'):
            print(f"📊 Views: Starting conversion loop...")
            for i, gene in enumerate(best_chromosome.genes):
                try:
                    entry = {
                        'applicant_id': gene.applicant_id,
                        'interviewer_id': gene.interviewer_id,
                        'room_id': gene.room_id,
                        'start_time': gene.start_time.isoformat() if hasattr(gene.start_time, 'isoformat') else str(gene.start_time),
                        'end_time': gene.end_time.isoformat() if hasattr(gene.end_time, 'isoformat') else str(gene.end_time),
                        'position': gene.position
                    }
                    schedule_data.append(entry)
                    if i == 0:
                        print(f"📊 Views: First gene converted: {entry}")
                except Exception as e:
                    print(f"📊 Views: Error converting gene {i}: {e}")
            print(f"📊 Views: Conversion complete. schedule_data length = {len(schedule_data)}")
        
        # Save schedules to Schedule collection (only if best solution exists)
        schedule_ids = []
        if schedule_data:
            print(f"💾 Saving {len(schedule_data)} schedules to database...")
            # Clear old schedules
            Schedule.delete_all()
            
            for schedule_entry in schedule_data:
                schedule_id = Schedule.create(schedule_entry)
                schedule_ids.append(str(schedule_id))
            print(f"✅ Saved {len(schedule_ids)} schedules")
        
        # Save result
        result_data = {
            'algorithm': 'GA',
            'fitness_score': best_fitness,
            'conflict_score': best_chromosome.conflict_score if best_chromosome else 0,
            'idle_time_score': best_chromosome.idle_time_score if best_chromosome else 0,
            'fairness_score': best_chromosome.fairness_score if best_chromosome else 0,
            'matching_score': best_chromosome.matching_score if best_chromosome else 0,
            'room_usage_score': best_chromosome.room_usage_score if best_chromosome else 0,
            'execution_time': execution_time,
            'generations': generations,
            'schedule_data': schedule_data,
            'schedule_ids': schedule_ids,
            'config_used': config,
            'created_at': datetime.now()
        }
        
        result_id = ScheduleResult.create(result_data)
        # Return JSON-safe payload without nested ObjectId by avoiding re-fetch
        safe_result = {
            'id': result_id,
            **result_data
        }
        
        return Response(to_json_safe(safe_result))
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def run_greedy_algorithm(request):
    """Run Greedy Algorithm for scheduling"""
    try:
        # Get data from MongoDB
        applicants = normalize_data(Applicant.find_all())
        interviewers = normalize_data(Interviewer.find_all())
        rooms = normalize_data(Room.find_all())
        
        if not applicants or not interviewers or not rooms:
            return Response({
                'error': 'Insufficient data. Need applicants, interviewers, and rooms.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Run Greedy
        config = request.data.get('config', {})
        greedy = GreedyScheduler(config=config)
        result = greedy.schedule(applicants, interviewers, rooms)
        
        # Extract results
        best_chromosome = result.get('best_solution')
        fitness_score = result.get('fitness', 0)
        execution_time = result.get('execution_time', 0)
        
        # Convert Chromosome genes to schedule data
        schedule_data = []
        if best_chromosome and hasattr(best_chromosome, 'genes'):
            for gene in best_chromosome.genes:
                schedule_data.append({
                    'applicant_id': gene.applicant_id,
                    'interviewer_id': gene.interviewer_id,
                    'room_id': gene.room_id,
                    'start_time': gene.start_time.isoformat() if hasattr(gene.start_time, 'isoformat') else str(gene.start_time),
                    'end_time': gene.end_time.isoformat() if hasattr(gene.end_time, 'isoformat') else str(gene.end_time),
                    'position': gene.position
                })
        
        # Save schedules to Schedule collection
        schedule_ids = []
        if schedule_data:
            print(f"💾 [GREEDY] Saving {len(schedule_data)} schedules to database...")
            Schedule.delete_all()
            for schedule_entry in schedule_data:
                schedule_id = Schedule.create(schedule_entry)
                schedule_ids.append(str(schedule_id))
            print(f"✅ [GREEDY] Saved {len(schedule_ids)} schedules")
        
        # Save result
        result_data = {
            'algorithm': 'GREEDY',
            'fitness_score': fitness_score,
            'conflict_score': best_chromosome.conflict_score if best_chromosome else 0,
            'idle_time_score': best_chromosome.idle_time_score if best_chromosome else 0,
            'fairness_score': best_chromosome.fairness_score if best_chromosome else 0,
            'matching_score': best_chromosome.matching_score if best_chromosome else 0,
            'room_usage_score': best_chromosome.room_usage_score if best_chromosome else 0,
            'execution_time': execution_time,
            'generations': None,
            'schedule_data': schedule_data,
            'schedule_ids': schedule_ids,
            'config_used': config,
            'created_at': datetime.now()
        }
        
        result_id = ScheduleResult.create(result_data)
        safe_result = {
            'id': result_id,
            **result_data
        }
        
        return Response(to_json_safe(safe_result))
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def run_simulated_annealing(request):
    """Run Simulated Annealing for scheduling"""
    try:
        config = request.data.get('config', {})
        
        # Get data from MongoDB
        applicants = normalize_data(Applicant.find_all())
        interviewers = normalize_data(Interviewer.find_all())
        rooms = normalize_data(Room.find_all())
        
        if not applicants or not interviewers or not rooms:
            return Response({
                'error': 'Insufficient data. Need applicants, interviewers, and rooms.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Run SA
        sa = SimulatedAnnealing(config=config)
        result = sa.optimize(applicants, interviewers, rooms)
        
        # Extract results
        best_chromosome = result.get('best_solution')
        fitness_score = result.get('fitness', 0)
        execution_time = result.get('execution_time', 0)
        iterations = result.get('iterations', 0)
        
        # Convert Chromosome genes to schedule data
        schedule_data = []
        if best_chromosome and hasattr(best_chromosome, 'genes'):
            for gene in best_chromosome.genes:
                schedule_data.append({
                    'applicant_id': gene.applicant_id,
                    'interviewer_id': gene.interviewer_id,
                    'room_id': gene.room_id,
                    'start_time': gene.start_time.isoformat() if hasattr(gene.start_time, 'isoformat') else str(gene.start_time),
                    'end_time': gene.end_time.isoformat() if hasattr(gene.end_time, 'isoformat') else str(gene.end_time),
                    'position': gene.position
                })
        
        # Save schedules to Schedule collection
        schedule_ids = []
        if schedule_data:
            print(f"💾 [SA] Saving {len(schedule_data)} schedules to database...")
            Schedule.delete_all()
            for schedule_entry in schedule_data:
                schedule_id = Schedule.create(schedule_entry)
                schedule_ids.append(str(schedule_id))
            print(f"✅ [SA] Saved {len(schedule_ids)} schedules")
        
        # Save result
        result_data = {
            'algorithm': 'SA',
            'fitness_score': fitness_score,
            'conflict_score': best_chromosome.conflict_score if best_chromosome else 0,
            'idle_time_score': best_chromosome.idle_time_score if best_chromosome else 0,
            'fairness_score': best_chromosome.fairness_score if best_chromosome else 0,
            'matching_score': best_chromosome.matching_score if best_chromosome else 0,
            'room_usage_score': best_chromosome.room_usage_score if best_chromosome else 0,
            'execution_time': execution_time,
            'generations': iterations,  # Using iterations for SA
            'schedule_data': schedule_data,
            'schedule_ids': schedule_ids,
            'config_used': config,
            'created_at': datetime.now()
        }
        
        result_id = ScheduleResult.create(result_data)
        safe_result = {
            'id': result_id,
            **result_data
        }
        
        return Response(to_json_safe(safe_result))
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def algorithm_results(request):
    """Get recent algorithm results"""
    try:
        # Get last 20 results sorted by creation time (most recent first)
        results = ScheduleResult.find_all(
            limit=20,
            sort=[("created_at", -1)]  # -1 for descending order
        )
        return Response(results)
    except Exception as e:
        print(f"❌ Error in algorithm_results: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def compare_algorithms(request):
    """Run all three algorithms and compare results"""
    try:
        config = request.data.get('config', {})
        
        # Get data from MongoDB
        applicants = normalize_data(Applicant.find_all())
        interviewers = normalize_data(Interviewer.find_all())
        rooms = normalize_data(Room.find_all())
        
        if not applicants or not interviewers or not rooms:
            return Response({
                'error': 'Insufficient data. Need applicants, interviewers, and rooms.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        comparison_results = []
        
        # 1. Run Genetic Algorithm
        print("🔄 Running Genetic Algorithm...")
        ga_start = time.time()
        ga_config = config.get('GA', {
            'POPULATION_SIZE': 100,
            'GENERATIONS': 200,
            'CROSSOVER_RATE': 0.8,
            'MUTATION_RATE': 0.15,
            'WEIGHTS': {
                'conflict': 0.4,
                'idle_time': 0.2,
                'fairness': 0.2,
                'matching': 0.1,
                'room_usage': 0.1
            }
        })
        ga = GeneticAlgorithm(config=ga_config)
        ga_result = ga.evolve(applicants, interviewers, rooms)
        ga_time = time.time() - ga_start
        
        ga_chromosome = ga_result.get('best_solution')
        comparison_results.append({
            'algorithm': 'GA',
            'fitness_score': ga_result.get('final_fitness', 0),
            'execution_time': ga_time,
            'schedules_count': len(ga_chromosome.genes) if ga_chromosome else 0,
            'conflict_score': ga_chromosome.conflict_score if ga_chromosome else 0,
            'idle_time_score': ga_chromosome.idle_time_score if ga_chromosome else 0,
            'fairness_score': ga_chromosome.fairness_score if ga_chromosome else 0,
            'matching_score': ga_chromosome.matching_score if ga_chromosome else 0,
            'room_usage_score': ga_chromosome.room_usage_score if ga_chromosome else 0,
        })
        
        # 2. Run Greedy Algorithm
        print("🔄 Running Greedy Algorithm...")
        greedy_start = time.time()
        greedy_config = config.get('GREEDY', {})
        greedy = GreedyScheduler(config=greedy_config)
        greedy_result = greedy.schedule(applicants, interviewers, rooms)
        greedy_time = time.time() - greedy_start
        
        greedy_chromosome = greedy_result.get('best_solution')
        comparison_results.append({
            'algorithm': 'GREEDY',
            'fitness_score': greedy_result.get('final_fitness', 0),
            'execution_time': greedy_time,
            'schedules_count': len(greedy_chromosome.genes) if greedy_chromosome else 0,
            'conflict_score': greedy_chromosome.conflict_score if greedy_chromosome else 0,
            'idle_time_score': greedy_chromosome.idle_time_score if greedy_chromosome else 0,
            'fairness_score': greedy_chromosome.fairness_score if greedy_chromosome else 0,
            'matching_score': greedy_chromosome.matching_score if greedy_chromosome else 0,
            'room_usage_score': greedy_chromosome.room_usage_score if greedy_chromosome else 0,
        })
        
        # 3. Run Simulated Annealing
        print("🔄 Running Simulated Annealing...")
        sa_start = time.time()
        sa_config = config.get('SA', {
            'INITIAL_TEMP': 1000,
            'COOLING_RATE': 0.95,
            'MIN_TEMP': 1,
            'MAX_ITERATIONS': 1000
        })
        sa = SimulatedAnnealing(config=sa_config)
        sa_result = sa.optimize(applicants, interviewers, rooms)
        sa_time = time.time() - sa_start
        
        sa_chromosome = sa_result.get('best_solution')
        comparison_results.append({
            'algorithm': 'SA',
            'fitness_score': sa_result.get('final_fitness', 0),
            'execution_time': sa_time,
            'schedules_count': len(sa_chromosome.genes) if sa_chromosome else 0,
            'conflict_score': sa_chromosome.conflict_score if sa_chromosome else 0,
            'idle_time_score': sa_chromosome.idle_time_score if sa_chromosome else 0,
            'fairness_score': sa_chromosome.fairness_score if sa_chromosome else 0,
            'matching_score': sa_chromosome.matching_score if sa_chromosome else 0,
            'room_usage_score': sa_chromosome.room_usage_score if sa_chromosome else 0,
        })
        
        print(f"✅ Comparison complete!")
        return Response({
            'results': comparison_results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error in compare_algorithms: {e}")
        import traceback
        traceback.print_exc()
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


@api_view(['GET'])
def get_schedule_conflicts(request):
    """Get schedule conflicts"""
    try:
        from interview_scheduler.settings import mongodb
        
        if mongodb is None:
            return Response(
                {'error': 'MongoDB not connected'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        schedules = list(mongodb['schedules'].find({}))
        conflicts = []
        
        # Check for time conflicts
        for i, schedule1 in enumerate(schedules):
            for schedule2 in schedules[i+1:]:
                # Same interviewer, overlapping time
                if (schedule1.get('interviewer_id') == schedule2.get('interviewer_id') and
                    schedule1.get('start_time') == schedule2.get('start_time')):
                    conflicts.append({
                        'type': 'interviewer_conflict',
                        'schedule1_id': str(schedule1['_id']),
                        'schedule2_id': str(schedule2['_id']),
                        'interviewer_id': schedule1.get('interviewer_id'),
                        'time': schedule1.get('start_time')
                    })
                
                # Same room, overlapping time
                if (schedule1.get('room_id') == schedule2.get('room_id') and
                    schedule1.get('start_time') == schedule2.get('start_time')):
                    conflicts.append({
                        'type': 'room_conflict',
                        'schedule1_id': str(schedule1['_id']),
                        'schedule2_id': str(schedule2['_id']),
                        'room_id': schedule1.get('room_id'),
                        'time': schedule1.get('start_time')
                    })
                
                # Same applicant, overlapping time
                if (schedule1.get('applicant_id') == schedule2.get('applicant_id') and
                    schedule1.get('start_time') == schedule2.get('start_time')):
                    conflicts.append({
                        'type': 'applicant_conflict',
                        'schedule1_id': str(schedule1['_id']),
                        'schedule2_id': str(schedule2['_id']),
                        'applicant_id': schedule1.get('applicant_id'),
                        'time': schedule1.get('start_time')
                    })
        
        return Response({
            'total_conflicts': len(conflicts),
            'conflicts': conflicts
        })
        
    except Exception as e:
        print(f"Error in get_schedule_conflicts: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class PositionAPIView(APIView):
    """API endpoint for Positions"""
    
    def get(self, request, pk=None):
        if pk:
            position = Position.find_by_id(pk)
            if position:
                return Response(position)
            return Response({'error': 'Position not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Get only active positions by default
        is_active = request.query_params.get('is_active', 'true').lower() == 'true'
        filter_dict = {'is_active': is_active} if request.query_params.get('is_active') else {}
        positions = Position.find_all(filter_dict)
        return Response(positions)
    
    def post(self, request):
        data = request.data
        is_valid, error_msg = Position.validate(data)
        if not is_valid:
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set defaults
        data['is_active'] = data.get('is_active', True)
        data['created_at'] = datetime.now()
        
        position_id = Position.create(data)
        position = Position.find_by_id(position_id)
        return Response(position, status=status.HTTP_201_CREATED)
    
    def put(self, request, pk):
        result = Position.update(pk, request.data)
        if result:
            position = Position.find_by_id(pk)
            return Response(position)
        return Response({'error': 'Position not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        if Position.delete(pk):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Position not found'}, status=status.HTTP_404_NOT_FOUND)


class InterviewSessionAPIView(APIView):
    """API endpoint for Interview Sessions"""
    
    def get(self, request, pk=None):
        if pk:
            session = InterviewSession.find_by_id(pk)
            if session:
                return Response(session)
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
        
        sessions = InterviewSession.find_all(sort=[("created_at", -1)])
        return Response(sessions)
    
    def post(self, request):
        data = request.data
        is_valid, error_msg = InterviewSession.validate(data)
        if not is_valid:
            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set defaults
        data['is_active'] = data.get('is_active', False)
        data['created_at'] = datetime.now()
        
        session_id = InterviewSession.create(data)
        session = InterviewSession.find_by_id(session_id)
        return Response(session, status=status.HTTP_201_CREATED)
    
    def put(self, request, pk):
        result = InterviewSession.update(pk, request.data)
        if result:
            session = InterviewSession.find_by_id(pk)
            return Response(session)
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        if InterviewSession.delete(pk):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_active_session(request):
    """Get the currently active interview session"""
    try:
        session = InterviewSession.get_active_session()
        if session:
            return Response(session)
        return Response({'error': 'No active session found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def set_active_session(request, pk):
    """Set a session as active (deactivates all others)"""
    try:
        # Deactivate all sessions
        InterviewSession.get_collection().update_many(
            {},
            {'$set': {'is_active': False}}
        )
        
        # Activate the specified session
        result = InterviewSession.update(pk, {'is_active': True})
        if result:
            session = InterviewSession.find_by_id(pk)
            return Response(session)
        return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

