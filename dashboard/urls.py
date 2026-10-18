from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Auth
    path('', views.dashboard_view, name='dashboard'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('worker-login/', views.worker_login_view, name='worker_login'),
    path('logout/', views.logout_user, name='logout'),
    path('signup/', views.worker_signup_view, name='worker_signup'),
    
    # Project Management
    path('add-project/', views.add_project_view, name='add_project'),
    path('project/<int:pk>/', views.project_detail_view, name='project_detail'),
    path('project/<int:pk>/edit/', views.edit_project_view, name='edit_project'),
    path('project/<int:pk>/delete/', views.delete_project_view, name='delete_project'),
    path('project/<int:project_id>/income-breakdown/', views.project_income_breakdown, name='income_breakdown'),
    
    # Item Management
    path('item/<int:item_id>/delete/', views.delete_item_view, name='delete_item'),
    path('item/<int:item_id>/return/', views.return_item_view, name='return_item'),
    
    
    # Attendance Management
    path('admin-mark-attendance/<int:worker_user_id>/', views.admin_mark_attendance_view, name='admin_mark_attendance'),
    path('admin-mark-attendance/', views.admin_mark_attendance_view, name='admin_mark_attendance'),
    path('worker/<int:worker_id>/edit-wage/', views.edit_worker_wage_view, name='edit_worker_wage'),
    path('worker/<int:worker_id>/payment/', views.worker_payment_view, name='worker_payment'),
    path('worker/<int:worker_id>/toggle-attendance/', views.toggle_worker_attendance_view, name='toggle_attendance'),

    #Payment Management
    path('payment/<int:payment_id>/pdf/', views.download_payslip_view, name='download_payslip'),
    path('export-expenses-pdf/', views.export_expenses_pdf, name='export_expenses_pdf'),
]