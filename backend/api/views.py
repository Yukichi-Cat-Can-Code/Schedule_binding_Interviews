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
from scheduler.genetic_algorithm_variant import GeneticAlgorithmVariant
from scheduler.genetic_algorithm_variant2 import GeneticAlgorithmVariant2
from scheduler.genetic_algorithm_variant3 import GeneticAlgorithmVariant3
import random  # Needed for top-k selection and variant cycling

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


def _get_active_session_or_none():
    try:
        return InterviewSession.get_active_session()
    except Exception:
        return None


def _parse_iso(dt_str):
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


def _overlaps(a_start, a_end, b_start, b_end) -> bool:
    return a_start < b_end and b_start < a_end


def _filter_by_session_constraints(schedule_data, current_session):
    """Apply session constraints before saving:
    - No overlap with schedules of other sessions that time-overlap current session window
    - Interviewer cannot work more than 8h continuously per day in current session
    Returns filtered list and stats.
    """
    if not current_session:
        return schedule_data, {'skipped_conflicts': 0, 'skipped_overtime': 0}

    # Load all schedules to check cross-session conflicts
    existing = Schedule.find_all()
    cur_id = current_session.get('_id')
    start_win = _parse_iso(current_session.get('start_date'))
    end_win = _parse_iso(current_session.get('end_date'))

    other = []
    for s in existing:
        if s.get('session_id') == cur_id:
            continue
        s_start = _parse_iso(s.get('start_time'))
        s_end = _parse_iso(s.get('end_time'))
        if not s_start or not s_end:
            continue
        # keep only those that overlap window
        if start_win and end_win and _overlaps(s_start, s_end, start_win, end_win):
            other.append(s)

    # track per-interviewer continuous minutes per day
    from collections import defaultdict
    work_minutes = defaultdict(lambda: defaultdict(int))  # interviewer_id -> date -> minutes

    filtered = []
    skipped_conflicts = 0
    skipped_overtime = 0

    for entry in schedule_data:
        ns = _parse_iso(entry.get('start_time'))
        ne = _parse_iso(entry.get('end_time'))
        if not ns or not ne:
            continue

        # Cross-session conflicts (interviewer/room)
        conflict = False
        for s in other:
            if (s.get('interviewer_id') == entry.get('interviewer_id') or
                s.get('room_id') == entry.get('room_id')):
                os = _parse_iso(s.get('start_time'))
                oe = _parse_iso(s.get('end_time'))
                if os and oe and _overlaps(ns, ne, os, oe):
                    conflict = True
                    break
        if conflict:
            skipped_conflicts += 1
            continue

        # 8-hour/day interviewer rule inside current session
        key_day = ns.date().isoformat()
        iv = entry.get('interviewer_id')
        minutes = int((ne - ns).total_seconds() // 60)
        if work_minutes[iv][key_day] + minutes > 8 * 60:
            skipped_overtime += 1
            continue
        work_minutes[iv][key_day] += minutes
        filtered.append(entry)

    return filtered, {'skipped_conflicts': skipped_conflicts, 'skipped_overtime': skipped_overtime}


def run_genetic_algorithm_variant2(request):
    """Run GA3 (Variant2)"""
    try:
        config = request.data.get('config', {})
        dry_run = request.data.get('dry_run', False)
        applicants = normalize_data(Applicant.find_all())
        interviewers = normalize_data(Interviewer.find_all())
        rooms = normalize_data(Room.find_all())
        if not applicants or not interviewers or not rooms:
            return Response({'error': 'Insufficient data.'}, status=status.HTTP_400_BAD_REQUEST)
        start = time.time()
        ga3 = GeneticAlgorithmVariant2(config=config)
        result = ga3.evolve(applicants, interviewers, rooms)
        chrom = result.get('best_solution')
        schedule_data = []
        if chrom and hasattr(chrom, 'genes'):
            for gene in chrom.genes:
                schedule_data.append({
                    'applicant_id': gene.applicant_id,
                    'interviewer_id': gene.interviewer_id,
                    'room_id': gene.room_id,
                    'start_time': gene.start_time.isoformat(),
                    'end_time': gene.end_time.isoformat(),
                    'position': gene.position,
                    'interview_date': gene.start_time.date().isoformat()
                })
        # session constraints only if we persist
        schedule_ids = []
        active_session = _get_active_session_or_none()
        if schedule_data and active_session and not dry_run:
            for e in schedule_data:
                e['session_id'] = active_session.get('_id')
            schedule_data, _stats = _filter_by_session_constraints(schedule_data, active_session)
            Schedule.delete_all({'session_id': active_session.get('_id')})
            for entry in schedule_data:
                sid = Schedule.create(entry)
                schedule_ids.append(str(sid))
        result_doc = {
            'algorithm': 'GA3',
            'fitness_score': result.get('final_fitness', 0),
            'conflict_score': chrom.conflict_score if chrom else 0,
            'idle_time_score': chrom.idle_time_score if chrom else 0,
            'fairness_score': chrom.fairness_score if chrom else 0,
            'matching_score': chrom.matching_score if chrom else 0,
            'room_usage_score': chrom.room_usage_score if chrom else 0,
            'execution_time': time.time() - start,
            'generations': result.get('generations'),
            'fitness_history': result.get('fitness_history', []),
            'schedule_data': schedule_data,
            'schedule_ids': schedule_ids,
            'config_used': config,
            'dry_run': dry_run,
            'created_at': datetime.now()
        }
        rid = ScheduleResult.create(result_doc)
        return Response(to_json_safe({'id': rid, **result_doc}))
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def run_genetic_algorithm_variant3(request):
    """Run GA4 (Variant3) with local search"""
    try:
        config = request.data.get('config', {})
        dry_run = request.data.get('dry_run', False)
        applicants = normalize_data(Applicant.find_all())
        interviewers = normalize_data(Interviewer.find_all())
        rooms = normalize_data(Room.find_all())
        if not applicants or not interviewers or not rooms:
            return Response({'error': 'Insufficient data.'}, status=status.HTTP_400_BAD_REQUEST)
        start = time.time()
        ga4 = GeneticAlgorithmVariant3(config=config)
        result = ga4.evolve(applicants, interviewers, rooms)
        chrom = result.get('best_solution')
        schedule_data = []
        if chrom and hasattr(chrom, 'genes'):
            for gene in chrom.genes:
                schedule_data.append({
                    'applicant_id': gene.applicant_id,
                    'interviewer_id': gene.interviewer_id,
                    'room_id': gene.room_id,
                    'start_time': gene.start_time.isoformat(),
                    'end_time': gene.end_time.isoformat(),
                    'position': gene.position,
                    'interview_date': gene.start_time.date().isoformat()
                })
        schedule_ids = []
        active_session = _get_active_session_or_none()
        if schedule_data and active_session and not dry_run:
            for e in schedule_data:
                e['session_id'] = active_session.get('_id')
            schedule_data, _stats = _filter_by_session_constraints(schedule_data, active_session)
            Schedule.delete_all({'session_id': active_session.get('_id')})
            for entry in schedule_data:
                sid = Schedule.create(entry)
                schedule_ids.append(str(sid))
        result_doc = {
            'algorithm': 'GA4',
            'fitness_score': result.get('final_fitness', 0),
            'conflict_score': chrom.conflict_score if chrom else 0,
            'idle_time_score': chrom.idle_time_score if chrom else 0,
            'fairness_score': chrom.fairness_score if chrom else 0,
            'matching_score': chrom.matching_score if chrom else 0,
            'room_usage_score': chrom.room_usage_score if chrom else 0,
            'execution_time': time.time() - start,
            'generations': result.get('generations'),
            'fitness_history': result.get('fitness_history', []),
            'schedule_data': schedule_data,
            'schedule_ids': schedule_ids,
            'config_used': config,
            'dry_run': dry_run,
            'created_at': datetime.now()
        }
        rid = ScheduleResult.create(result_doc)
        return Response(to_json_safe({'id': rid, **result_doc}))
    except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def import_excel(request):
    """Import data from Excel file"""
    try:
        file = request.FILES.get('file')
        data_type = request.data.get('type')  # 'applicants', 'interviewers', 'rooms', 'all'
        session_id = request.data.get('session_id')
        
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        created_ids = { 'applicants': [], 'interviewers': [], 'rooms': [] }
        total_counts = { 'applicants': 0, 'interviewers': 0, 'rooms': 0 }

        if data_type == 'all':
            # Expect sheets named Applicants, Interviewers, Rooms
            xls = pd.ExcelFile(file)
            sheets = {name.lower(): name for name in xls.sheet_names}

            if 'applicants' in sheets:
                df = pd.read_excel(xls, sheets['applicants'])
                records = df.to_dict('records')
                created_ids['applicants'] = Applicant.bulk_create(records)
                total_counts['applicants'] = len(records)
            if 'interviewers' in sheets:
                df = pd.read_excel(xls, sheets['interviewers'])
                records = df.to_dict('records')
                created_ids['interviewers'] = Interviewer.bulk_create(records)
                total_counts['interviewers'] = len(records)
            if 'rooms' in sheets:
                df = pd.read_excel(xls, sheets['rooms'])
                records = df.to_dict('records')
                created_ids['rooms'] = Room.bulk_create(records)
                total_counts['rooms'] = len(records)
        elif data_type in ('applicants','interviewers','rooms'):
            df = pd.read_excel(file)
            records = df.to_dict('records')
            if data_type == 'applicants':
                created_ids['applicants'] = Applicant.bulk_create(records)
                total_counts['applicants'] = len(records)
            elif data_type == 'interviewers':
                created_ids['interviewers'] = Interviewer.bulk_create(records)
                total_counts['interviewers'] = len(records)
            elif data_type == 'rooms':
                created_ids['rooms'] = Room.bulk_create(records)
                total_counts['rooms'] = len(records)
        else:
            return Response({'error': 'Invalid data type'}, status=status.HTTP_400_BAD_REQUEST)

        # If session_id provided, associate created IDs with the session
        if session_id:
            coll = InterviewSession.get_collection()
            update = {}
            if created_ids['applicants']:
                update.setdefault('$addToSet', {}).setdefault('applicant_ids', {'$each': created_ids['applicants']})
            if created_ids['interviewers']:
                update.setdefault('$addToSet', {}).setdefault('interviewer_ids', {'$each': created_ids['interviewers']})
            if created_ids['rooms']:
                update.setdefault('$addToSet', {}).setdefault('room_ids', {'$each': created_ids['rooms']})
            if update:
                coll.update_one({'_id': ObjectId(session_id)}, update)

        return Response({
            'message': 'Import completed',
            'counts': total_counts,
            'session_updated': bool(session_id)
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
        session_id = request.query_params.get('session_id')
        filter_dict = {'session_id': session_id} if session_id else None
        schedules = Schedule.find_all(filter_dict)
        
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
        # Dynamic positions-based stats
        positions = Position.find_all({'is_active': True})
        pos_counts_app = {}
        pos_counts_int = {}
        for p in positions:
            code = p.get('code')
            name = p.get('name')
            pos_counts_app[name or code] = Applicant.count({'position': code})
            pos_counts_int[name or code] = Interviewer.count({'position': code})

        stats = {
            'applicants': {
                'total': Applicant.count(),
                'by_position': pos_counts_app,
            },
            'interviewers': {
                'total': Interviewer.count(),
                'by_position': pos_counts_int,
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
                        'position': gene.position,
                        'interview_date': gene.start_time.date().isoformat() if hasattr(gene.start_time, 'date') else None
                    }
                    schedule_data.append(entry)
                    if i == 0:
                        print(f"📊 Views: First gene converted: {entry}")
                except Exception as e:
                    print(f"📊 Views: Error converting gene {i}: {e}")
            print(f"📊 Views: Conversion complete. schedule_data length = {len(schedule_data)}")
        
        # Apply session-aware constraints and save schedules
        schedule_ids = []
        if schedule_data:
            active_session = _get_active_session_or_none()
            if active_session:
                for e in schedule_data:
                    e['session_id'] = active_session.get('_id')
            filtered_data, stats = _filter_by_session_constraints(schedule_data, active_session)
            print(f"🧹 [GA] Filtered schedules: kept={len(filtered_data)}, skipped_conflicts={stats['skipped_conflicts']}, skipped_overtime={stats['skipped_overtime']}")
            schedule_data = filtered_data

        if schedule_data:
            print(f"💾 Saving {len(schedule_data)} schedules to database...")
            # Clear old schedules in current session only (if any)
            if 'active_session' in locals() and active_session:
                Schedule.delete_all({'session_id': active_session.get('_id')})
            else:
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
def run_genetic_algorithm_variant(request):
    """Run Genetic Algorithm Variant (GA2) for scheduling"""
    try:
        config = request.data.get('config', {})
        applicants = normalize_data(Applicant.find_all())
        interviewers = normalize_data(Interviewer.find_all())
        rooms = normalize_data(Room.find_all())

        if not applicants or not interviewers or not rooms:
            return Response({'error': 'Insufficient data. Need applicants, interviewers, and rooms.'}, status=status.HTTP_400_BAD_REQUEST)

        start_time = time.time()
        ga2 = GeneticAlgorithmVariant(config=config)
        result = ga2.evolve(applicants, interviewers, rooms)

        best_chromosome = result.get('best_solution')
        best_fitness = result.get('final_fitness', 0)
        generations = result.get('generations', 0)
        execution_time = time.time() - start_time

        schedule_data = []
        if best_chromosome and hasattr(best_chromosome, 'genes'):
            for gene in best_chromosome.genes:
                schedule_data.append({
                    'applicant_id': gene.applicant_id,
                    'interviewer_id': gene.interviewer_id,
                    'room_id': gene.room_id,
                    'start_time': gene.start_time.isoformat() if hasattr(gene.start_time, 'isoformat') else str(gene.start_time),
                    'end_time': gene.end_time.isoformat() if hasattr(gene.end_time, 'isoformat') else str(gene.end_time),
                    'position': gene.position,
                    'interview_date': gene.start_time.date().isoformat() if hasattr(gene.start_time, 'date') else None
                })

        # Apply session-aware constraints and save
        schedule_ids = []
        if schedule_data:
            active_session = _get_active_session_or_none()
            if active_session:
                for e in schedule_data:
                    e['session_id'] = active_session.get('_id')
            filtered_data, stats = _filter_by_session_constraints(schedule_data, active_session)
            print(f"🧹 [GA2] Filtered schedules: kept={len(filtered_data)}, skipped_conflicts={stats['skipped_conflicts']}, skipped_overtime={stats['skipped_overtime']}")
            schedule_data = filtered_data

        if schedule_data:
            print(f"💾 [GA2] Saving {len(schedule_data)} schedules to database...")
            if 'active_session' in locals() and active_session:
                Schedule.delete_all({'session_id': active_session.get('_id')})
            else:
                Schedule.delete_all()
            for schedule_entry in schedule_data:
                schedule_id = Schedule.create(schedule_entry)
                schedule_ids.append(str(schedule_id))
            print(f"✅ [GA2] Saved {len(schedule_ids)} schedules")

        result_data = {
            'algorithm': 'GA2',
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
        safe_result = {'id': result_id, **result_data}
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
    """Compare GA family variants (GA, GA2, GA3, GA4)"""
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

        # 1b. Run Genetic Algorithm Variant (GA2)
        print("🔄 Running Genetic Algorithm Variant (GA2)...")
        ga2_start = time.time()
        ga2_config = config.get('GA2', {
            'POPULATION_SIZE': 100,
            'GENERATIONS': 200,
            'CROSSOVER_RATE': 0.9,
            'MUTATION_RATE': 0.2,
            'ELITISM_RATE': 0.05,
        })
        ga2 = GeneticAlgorithmVariant(config=ga2_config)
        ga2_result = ga2.evolve(applicants, interviewers, rooms)
        ga2_time = time.time() - ga2_start

        ga2_chromosome = ga2_result.get('best_solution')
        comparison_results.append({
            'algorithm': 'GA2',
            'fitness_score': ga2_result.get('final_fitness', 0),
            'execution_time': ga2_time,
            'schedules_count': len(ga2_chromosome.genes) if ga2_chromosome else 0,
            'conflict_score': ga2_chromosome.conflict_score if ga2_chromosome else 0,
            'idle_time_score': ga2_chromosome.idle_time_score if ga2_chromosome else 0,
            'fairness_score': ga2_chromosome.fairness_score if ga2_chromosome else 0,
            'matching_score': ga2_chromosome.matching_score if ga2_chromosome else 0,
            'room_usage_score': ga2_chromosome.room_usage_score if ga2_chromosome else 0,
        })
        
        # 2. Run GA3
        print("🔄 Running Genetic Algorithm Variant 2 (GA3)...")
        ga3_start = time.time()
        ga3_config = config.get('GA3', {
            'POPULATION_SIZE': 120,
            'GENERATIONS': 250,
            'CROSSOVER_RATE': 0.85,
            'MUTATION_RATE': 0.12
        })
        ga3 = GeneticAlgorithmVariant2(config=ga3_config)
        ga3_result = ga3.evolve(applicants, interviewers, rooms)
        ga3_time = time.time() - ga3_start
        ga3_chromosome = ga3_result.get('best_solution')
        comparison_results.append({
            'algorithm': 'GA3',
            'fitness_score': ga3_result.get('final_fitness', 0),
            'execution_time': ga3_time,
            'schedules_count': len(ga3_chromosome.genes) if ga3_chromosome else 0,
            'conflict_score': ga3_chromosome.conflict_score if ga3_chromosome else 0,
            'idle_time_score': ga3_chromosome.idle_time_score if ga3_chromosome else 0,
            'fairness_score': ga3_chromosome.fairness_score if ga3_chromosome else 0,
            'matching_score': ga3_chromosome.matching_score if ga3_chromosome else 0,
            'room_usage_score': ga3_chromosome.room_usage_score if ga3_chromosome else 0,
        })

        # 3. Run GA4
        print("🔄 Running Genetic Algorithm Variant 3 (GA4)...")
        ga4_start = time.time()
        ga4_config = config.get('GA4', {
            'POPULATION_SIZE': 120,
            'GENERATIONS': 250,
            'CROSSOVER_RATE': 0.9,
            'MUTATION_RATE': 0.18,
            'LOCAL_SEARCH_RATE': 0.3
        })
        ga4 = GeneticAlgorithmVariant3(config=ga4_config)
        ga4_result = ga4.evolve(applicants, interviewers, rooms)
        ga4_time = time.time() - ga4_start
        ga4_chromosome = ga4_result.get('best_solution')
        comparison_results.append({
            'algorithm': 'GA4',
            'fitness_score': ga4_result.get('final_fitness', 0),
            'execution_time': ga4_time,
            'schedules_count': len(ga4_chromosome.genes) if ga4_chromosome else 0,
            'conflict_score': ga4_chromosome.conflict_score if ga4_chromosome else 0,
            'idle_time_score': ga4_chromosome.idle_time_score if ga4_chromosome else 0,
            'fairness_score': ga4_chromosome.fairness_score if ga4_chromosome else 0,
            'matching_score': ga4_chromosome.matching_score if ga4_chromosome else 0,
            'room_usage_score': ga4_chromosome.room_usage_score if ga4_chromosome else 0,
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


@api_view(['POST'])
def generate_top_schedules(request):
    """Generate multiple GA family runs and return top-K without persisting schedules."""
    try:
        k = int(request.data.get('k', 5))
        runs = int(request.data.get('runs', 8))
        config = request.data.get('config', {})
        applicants = normalize_data(Applicant.find_all())
        interviewers = normalize_data(Interviewer.find_all())
        rooms = normalize_data(Room.find_all())
        if not applicants or not interviewers or not rooms:
            return Response({'error': 'Insufficient data.'}, status=status.HTTP_400_BAD_REQUEST)
        variants = [
            ('GA', GeneticAlgorithm, config.get('GA', {})),
            ('GA2', GeneticAlgorithmVariant, config.get('GA2', {})),
            ('GA3', GeneticAlgorithmVariant2, config.get('GA3', {})),
            ('GA4', GeneticAlgorithmVariant3, config.get('GA4', {})),
        ]
        candidate_results = []
        for i in range(runs):
            name, cls, cfg = random.choice(variants)
            alg = cls(cfg)
            res = alg.evolve(applicants, interviewers, rooms)
            chrom = res.get('best_solution')
            schedule_data = []
            if chrom and hasattr(chrom, 'genes'):
                for gene in chrom.genes:
                    schedule_data.append({
                        'applicant_id': gene.applicant_id,
                        'interviewer_id': gene.interviewer_id,
                        'room_id': gene.room_id,
                        'start_time': gene.start_time.isoformat(),
                        'end_time': gene.end_time.isoformat(),
                        'position': gene.position,
                        'interview_date': gene.start_time.date().isoformat()
                    })
            doc = {
                'algorithm': name,
                'fitness_score': res.get('final_fitness', 0),
                'conflict_score': chrom.conflict_score if chrom else 0,
                'idle_time_score': chrom.idle_time_score if chrom else 0,
                'fairness_score': chrom.fairness_score if chrom else 0,
                'matching_score': chrom.matching_score if chrom else 0,
                'room_usage_score': chrom.room_usage_score if chrom else 0,
                'generations': res.get('generations'),
                'schedule_data': schedule_data,
                'fitness_history': res.get('fitness_history', []),
                'created_at': datetime.now(),
                'candidate_set': True,
                'is_selected': False
            }
            rid = ScheduleResult.create(doc)
            candidate_results.append({'id': rid, **doc})
        # pick top k by fitness
        candidate_results.sort(key=lambda x: x['fitness_score'], reverse=True)
        top_k = candidate_results[:k]
        return Response(to_json_safe({'top_k': top_k, 'total_generated': len(candidate_results)}))
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def choose_schedule_result(request):
    """Select one candidate schedule result and persist its schedule_data as official schedules."""
    try:
        result_id = request.data.get('result_id')
        if not result_id:
            return Response({'error': 'result_id required'}, status=status.HTTP_400_BAD_REQUEST)
        result = ScheduleResult.find_by_id(result_id)
        if not result:
            return Response({'error': 'Result not found'}, status=status.HTTP_404_NOT_FOUND)
        schedule_data = result.get('schedule_data', [])
        active_session = _get_active_session_or_none()
        if not active_session:
            return Response({'error': 'No active session'}, status=status.HTTP_400_BAD_REQUEST)
        # Clear existing schedules for session
        Schedule.delete_all({'session_id': active_session.get('_id')})
        saved_ids = []
        for entry in schedule_data:
            entry['session_id'] = active_session.get('_id')
            # ensure interview_date present
            if 'interview_date' not in entry and 'start_time' in entry:
                try:
                    entry['interview_date'] = datetime.fromisoformat(entry['start_time']).date().isoformat()
                except Exception:
                    entry['interview_date'] = active_session.get('start_date')
            sid = Schedule.create(entry)
            saved_ids.append(str(sid))
        ScheduleResult.update(result_id, {'is_selected': True})
        return Response({'selected_result_id': result_id, 'persisted_count': len(saved_ids)})
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


class ApplicantAPIView(APIView):
    """API endpoint for Applicants"""

    def get(self, request, pk=None):
        if pk:
            item = Applicant.find_by_id(pk)
            if item:
                return Response(item)
            return Response({'error': 'Applicant not found'}, status=status.HTTP_404_NOT_FOUND)
        # Optional filters
        position = request.query_params.get('position')
        filter_dict = {'position': position} if position else {}
        items = Applicant.find_all(filter_dict)
        return Response(items)

    def post(self, request):
        data = request.data
        is_valid, err = Applicant.validate(data)
        if not is_valid:
            return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
        item_id = Applicant.create(data)
        item = Applicant.find_by_id(item_id)
        return Response(item, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        if Applicant.update(pk, request.data):
            return Response(Applicant.find_by_id(pk))
        return Response({'error': 'Applicant not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if Applicant.delete(pk):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Applicant not found'}, status=status.HTTP_404_NOT_FOUND)


class InterviewerAPIView(APIView):
    """API endpoint for Interviewers"""

    def get(self, request, pk=None):
        if pk:
            item = Interviewer.find_by_id(pk)
            if item:
                return Response(item)
            return Response({'error': 'Interviewer not found'}, status=status.HTTP_404_NOT_FOUND)
        position = request.query_params.get('position')
        filter_dict = {'position': position} if position else {}
        items = Interviewer.find_all(filter_dict)
        return Response(items)

    def post(self, request):
        data = request.data
        is_valid, err = Interviewer.validate(data)
        if not is_valid:
            return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
        item_id = Interviewer.create(data)
        item = Interviewer.find_by_id(item_id)
        return Response(item, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        if Interviewer.update(pk, request.data):
            return Response(Interviewer.find_by_id(pk))
        return Response({'error': 'Interviewer not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if Interviewer.delete(pk):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Interviewer not found'}, status=status.HTTP_404_NOT_FOUND)


class RoomAPIView(APIView):
    """API endpoint for Rooms"""

    def get(self, request, pk=None):
        if pk:
            item = Room.find_by_id(pk)
            if item:
                return Response(item)
            return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)
        items = Room.find_all()
        return Response(items)

    def post(self, request):
        data = request.data
        is_valid, err = Room.validate(data)
        if not is_valid:
            return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
        item_id = Room.create(data)
        item = Room.find_by_id(item_id)
        return Response(item, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        if Room.update(pk, request.data):
            return Response(Room.find_by_id(pk))
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if Room.delete(pk):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Room not found'}, status=status.HTTP_404_NOT_FOUND)


class ScheduleAPIView(APIView):
    """API endpoint for Schedules"""

    def get(self, request, pk=None):
        if pk:
            item = Schedule.find_by_id(pk)
            if item:
                return Response(item)
            return Response({'error': 'Schedule not found'}, status=status.HTTP_404_NOT_FOUND)
        session_id = request.query_params.get('session_id')
        filter_dict = {'session_id': session_id} if session_id else {}
        items = Schedule.find_all(filter_dict)
        return Response(items)

    def post(self, request):
        data = request.data
        is_valid, err = Schedule.validate(data)
        if not is_valid:
            return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
        item_id = Schedule.create(data)
        item = Schedule.find_by_id(item_id)
        return Response(item, status=status.HTTP_201_CREATED)

    def put(self, request, pk):
        if Schedule.update(pk, request.data):
            return Response(Schedule.find_by_id(pk))
        return Response({'error': 'Schedule not found'}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, pk):
        if Schedule.delete(pk):
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Schedule not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_schedule_timeline(request):
    """Return schedules grouped by room for timeline view."""
    try:
        session_id = request.query_params.get('session_id')
        filter_dict = {'session_id': session_id} if session_id else None
        schedules = Schedule.find_all(filter_dict)

        # Build lookup maps
        applicants = {a.get('_id'): a for a in Applicant.find_all()}
        interviewers = {i.get('_id'): i for i in Interviewer.find_all()}
        rooms = {r.get('_id'): r for r in Room.find_all()}

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
                'position': s.get('position') or applicant.get('position'),
                'start': s.get('start_time'),
                'end': s.get('end_time'),
                'interview_date': s.get('interview_date'),
                'status': s.get('status', 'scheduled'),
            })

        return Response(timeline_grouped)
    except Exception as e:
        print(f"Error in get_schedule_timeline: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

