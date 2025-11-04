"""
URL routing for API endpoints
"""
from django.urls import path
from api import views

urlpatterns = [
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
    path('schedules/<str:pk>/', views.ScheduleAPIView.as_view(), name='schedule-detail'),
    
    # Algorithm Config
    path('configs/', views.AlgorithmConfigAPIView.as_view(), name='config-list'),
    path('configs/<str:pk>/', views.AlgorithmConfigAPIView.as_view(), name='config-detail'),
    
    # Data Management
    path('data/import/', views.import_excel, name='import-excel'),
    path('data/statistics/', views.dashboard_stats, name='dashboard-stats'),
    
    # Algorithms
    path('algorithm/genetic/', views.run_genetic_algorithm, name='run-genetic'),
    path('algorithm/greedy/', views.run_greedy_algorithm, name='run-greedy'),
    path('algorithm/simulated-annealing/', views.run_simulated_annealing, name='run-sa'),
    path('algorithm/results/', views.algorithm_results, name='algorithm-results'),
]
