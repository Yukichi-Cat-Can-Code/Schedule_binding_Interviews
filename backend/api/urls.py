from django.urls import path
from api import views

urlpatterns = [
    # Positions
    path('positions/', views.PositionAPIView.as_view(), name='position-list'),
    path('positions/<str:pk>/', views.PositionAPIView.as_view(), name='position-detail'),
    
    # Interview Sessions
    path('sessions/', views.InterviewSessionAPIView.as_view(), name='session-list'),
    path('sessions/active/', views.get_active_session, name='session-active'),  
    path('sessions/<str:pk>/', views.InterviewSessionAPIView.as_view(), name='session-detail'),
    path('sessions/<str:pk>/activate/', views.set_active_session, name='session-activate'),
    
    # Applicants
    path('applicants/', views.ApplicantAPIView.as_view(), name='applicant-list'),
    path('applicants/<str:pk>/', views.ApplicantAPIView.as_view(), name='applicant-detail'),
    
    # Interviewers
    path('interviewers/', views.InterviewerAPIView.as_view(), name='interviewer-list'),
    path('interviewers/<str:pk>/', views.InterviewerAPIView.as_view(), name='interviewer-detail'),
    
    # Rooms
    path('rooms/', views.RoomAPIView.as_view(), name='room-list'),
    path('rooms/<str:pk>/', views.RoomAPIView.as_view(), name='room-detail'),
    
    # Schedules
    path('schedules/', views.ScheduleAPIView.as_view(), name='schedule-list'),
    path('schedules/conflicts/', views.get_schedule_conflicts, name='schedule-conflicts'),  
    path('schedules/timeline/', views.get_schedule_timeline, name='schedule-timeline'), 
    path('schedules/<str:pk>/', views.ScheduleAPIView.as_view(), name='schedule-detail'),
    
    # Algorithm Config
    path('configs/', views.AlgorithmConfigAPIView.as_view(), name='config-list'),
    path('configs/<str:pk>/', views.AlgorithmConfigAPIView.as_view(), name='config-detail'),
    
    # Data Management
    path('data/import/', views.import_excel, name='import-excel'),
    path('data/export/', views.export_schedules, name='export-schedules'),
    path('data/statistics/', views.dashboard_stats, name='dashboard-stats'),
    
    # Algorithms
    path('algorithm/genetic/', views.run_genetic_algorithm, name='run-genetic'),
    path('algorithm/genetic-variant/', views.run_genetic_algorithm_variant, name='run-genetic-variant'),
    path('algorithm/genetic-variant2/', views.run_genetic_algorithm_variant2, name='run-genetic-variant2'),
    path('algorithm/genetic-variant3/', views.run_genetic_algorithm_variant3, name='run-genetic-variant3'),
    # Deprecated: Greedy and SA removed in favor of GA variants
    path('algorithm/compare/', views.compare_algorithms, name='compare-algorithms'),
    path('algorithm/topk/', views.generate_top_schedules, name='generate-topk'),
    path('algorithm/select/', views.choose_schedule_result, name='choose-schedule-result'),
    path('algorithm/results/', views.algorithm_results, name='algorithm-results'),
]
