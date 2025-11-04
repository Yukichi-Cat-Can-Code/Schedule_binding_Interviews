"""
URL routing for API endpoints
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api import views

router = DefaultRouter()
router.register(r'applicants', views.ApplicantViewSet, basename='applicant')
router.register(r'interviewers', views.InterviewerViewSet, basename='interviewer')
router.register(r'rooms', views.RoomViewSet, basename='room')
router.register(r'schedules', views.ScheduleViewSet, basename='schedule')
router.register(r'configs', views.AlgorithmConfigViewSet, basename='config')

urlpatterns = [
    path('', include(router.urls)),
    path('data/', views.DataManagementViewSet.as_view({'post': 'import_excel', 'get': 'export_excel'})),
    path('data/statistics/', views.DataManagementViewSet.as_view({'get': 'statistics'})),
    path('algorithm/run/', views.AlgorithmViewSet.as_view({'post': 'run'})),
    path('algorithm/results/', views.AlgorithmViewSet.as_view({'get': 'results'})),
    path('algorithm/compare/', views.AlgorithmViewSet.as_view({'post': 'compare'})),
]
