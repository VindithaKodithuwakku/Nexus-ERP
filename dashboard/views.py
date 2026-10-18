from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout 
from .models import Project, Worker, ProjectItem, Attendance, Payment, ProjectIncome, ItemReturn
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa


# ==========================================
# HELPER FUNCTION: Check Supervisor Status
# ==========================================
def check_is_supervisor(user):
    if user.is_authenticated and hasattr(user, 'worker'):
        is_sup = getattr(user.worker, 'is_supervisor', False)
        role = str(user.worker.job_role).strip().lower()
        if is_sup or role in ['manager', 'supervisor']:
            return True
    return False


# ==========================================
# MAIN DASHBOARD VIEW
# ==========================================
def dashboard_view(request):
    projects = Project.objects.all()
    total_income = sum(float(p.income) for p in projects)
    total_expense = 0.0

    # 1. Calculate Project Costs and Profits (After subtracting returns)
    for project in projects:
        gross_cost = sum(float(item.total_cost) for item in project.items.all())
        refunded = sum(float(ret.refund_amount) for item in project.items.all() for ret in item.returns.all())
        project_cost = max(0.0, gross_cost - refunded)
        
        total_expense += project_cost
        project.cost = project_cost
        project.profit_or_loss = float(project.income) - project_cost
        
        exp_rev = float(project.expected_revenue)
        inc = float(project.income)
        
        if exp_rev > inc:
            project.balance_amount = exp_rev - inc
            project.balance_status = 'to_collect'
        elif inc > exp_rev:
            project.balance_amount = inc - exp_rev
            project.balance_status = 'over_target'
        else:
            project.balance_amount = 0.0
            project.balance_status = 'met'

    # Add total salaries to total expense
    total_salaries = sum(float(pay.amount) for pay in Payment.objects.all())
    total_expense += total_salaries

    net_profit = total_income - total_expense

    # 2. Determine Access Levels
    is_supervisor = check_is_supervisor(request.user)
    has_admin_access = request.user.is_staff or is_supervisor

    # 3. ADMIN / SUPERVISOR VIEW: Load all workers
    admin_worker_list = []
    today = timezone.now().date()
    attendance_already_marked = Attendance.objects.filter(date=today).exists()

    if has_admin_access: 
        all_workers = Worker.objects.all()
        for w in all_workers:
            is_present = Attendance.objects.filter(user=w.user, date=today).exists()
            admin_worker_list.append({
                'worker': w,
                'is_present': is_present
            })

    # 4. STAFF VIEW
    staff_stats = {}
    if request.user.is_authenticated and not has_admin_access:
        days_worked = Attendance.objects.filter(user=request.user).count()
        worker_profile = getattr(request.user, 'worker', None)
        daily_wage = float(worker_profile.daily_wage) if worker_profile else 0.0
        total_earned = days_worked * daily_wage
        
        payments = Payment.objects.filter(user=request.user).order_by('-date_paid')
        total_paid = sum(float(p.amount) for p in payments)
        pending_balance = total_earned - total_paid
        all_attendances = Attendance.objects.filter(user=request.user).order_by('-date')

        staff_stats = {
            'days_worked': days_worked,
            'daily_wage': daily_wage,
            'total_earned': total_earned,
            'total_paid': total_paid,
            'pending_balance': pending_balance,
            'payments': payments,
            'all_attendances': all_attendances,
        }

    # ==========================================
    # 5. DAY-BY-DAY CASH FLOW LEDGER
    # ==========================================
    ledger = []
    
    if has_admin_access:
        # 5.1 Salary Expenses
        for pay in Payment.objects.all():
            worker_name = pay.user.username
            if hasattr(pay.user, 'worker'):
                worker_name = pay.user.worker.full_name
                
            ledger.append({
                'date': getattr(pay, 'date_paid', today),
                'description': f"Salary Paid to {worker_name}",
                'category': 'Salary',
                'type': 'Expense',
                'amount': float(pay.amount)
            })
            
        # 5.2 Material Expenses (Net cost after returns OR showing returns in Expense tab)
        for item in ProjectItem.objects.all():
            item_date = getattr(item, 'date_added', today) 
            ledger.append({
                'date': item_date,
                'description': f"{item.item_name} (For: {item.project.name})",
                'category': 'Material',
                'type': 'Expense',
                'amount': float(item.total_cost)
            })

            # Show each return inside Expense records so it is visible when clicking Total Expense
            for ret in item.returns.all():
                ledger.append({
                    'date': ret.date_returned,
                    'description': f"Returned: {ret.return_quantity}x {item.item_name} (For: {item.project.name})",
                    'category': 'Material Return',
                    'type': 'Expense',
                    'amount': -float(ret.refund_amount)
                })
            
        # 5.3 Project Incomes
        for p in projects:
            if p.income > 0:
                ledger.append({
                    'date': p.deadline if p.deadline else today,
                    'description': f"Income from {p.name}",
                    'category': 'Income',
                    'type': 'Income',
                    'amount': float(p.income),
                    'project_id': p.id
                })
                
        ledger.sort(key=lambda x: str(x['date']), reverse=True)

    context = {
        'projects': projects,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_profit': net_profit,
        'admin_worker_list': admin_worker_list,
        'staff_stats': staff_stats,
        'is_supervisor': is_supervisor,
        'has_admin_access': has_admin_access,
        'attendance_already_marked': attendance_already_marked,
        'ledger': ledger, 
    }
    return render(request, 'dashboard/index.html', context)


# ==========================================
# AUTHENTICATION VIEWS
# ==========================================
def admin_login_view(request):
    if request.method == 'POST':
        u_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        user = authenticate(request, username=u_name, password=pass_word)
        
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('dashboard')
        else:
            error = "Invalid Admin credentials or unauthorized access."
            return render(request, 'dashboard/admin_login.html', {'error': error})
    return render(request, 'dashboard/admin_login.html')

def worker_login_view(request):
    if request.method == 'POST':
        u_name = request.POST.get('username')
        passw = request.POST.get('password')
        user = authenticate(request, username=u_name, password=passw)
        
        if user is not None:
            if hasattr(user, 'worker'):
                login(request, user)
                return redirect('dashboard')
            else:
                error_msg = "This account is not a registered worker account."
                return render(request, 'dashboard/worker_login.html', {'error': error_msg})
        else:
            error_msg = "Invalid username or password. Please try again."
            return render(request, 'dashboard/worker_login.html', {'error': error_msg})
    return render(request, 'dashboard/worker_login.html')

def logout_user(request):
    logout(request)
    return redirect('dashboard')

def worker_signup_view(request):
    if request.method == 'POST':
        u_name = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        f_name = request.POST.get('full_name')
        mob = request.POST.get('mobile')
        nic_num = request.POST.get('nic')
        addr = request.POST.get('address')
        role = request.POST.get('job_role')

        user = User.objects.create_user(username=u_name, email=email, password=password)
        Worker.objects.create(
            user=user,
            full_name=f_name,
            mobile=mob,
            nic=nic_num,
            address=addr,
            job_role=role
        )
        return redirect('worker_login') 
    return render(request, 'dashboard/worker_signup.html')


# ==========================================
# PROJECT MANAGEMENT VIEWS
# ==========================================
def project_detail_view(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    if request.method == 'POST':
        is_supervisor = check_is_supervisor(request.user)
        if request.user.is_staff or is_supervisor:
            item_name = request.POST.get('item_name')
            quantity = request.POST.get('quantity')
            unit_price = request.POST.get('unit_price') 
            
            if item_name and quantity and unit_price:
                qty = int(quantity)
                price = float(unit_price)
                calculated_total = qty * price
                
                ProjectItem.objects.create(
                    project=project,
                    item_name=item_name,
                    quantity=qty,
                    total_cost=calculated_total
                )
                return redirect('project_detail', pk=project.pk)

    project_items = project.items.all()
    
    # Calculate remaining quantity and net cost after returns for each item
    for item in project_items:
        returned_qty = sum(int(ret.return_quantity) for ret in item.returns.all())
        refunded_amt = sum(float(ret.refund_amount) for ret in item.returns.all())
        item.net_quantity = max(0, int(item.quantity) - returned_qty)
        item.net_cost = max(0.0, float(item.total_cost) - refunded_amt)

    context = {
        'project': project,
        'items': project_items
    }
    return render(request, 'dashboard/project_detail.html', context)


def add_project_view(request):
    is_supervisor = check_is_supervisor(request.user)
    if not (request.user.is_staff or is_supervisor):
        return redirect('dashboard')

    if request.method == 'POST':
        p_name = request.POST.get('name')
        if Project.objects.filter(name=p_name).exists():
            return render(request, 'dashboard/add_project.html', {
                'error_msg': f'"{p_name}" already exists! Please use a different name.'
            })

        p_status = request.POST.get('status')
        p_deadline = request.POST.get('deadline')
        p_expected = float(request.POST.get('expected_revenue') or 0.0)
        p_income = float(request.POST.get('income') or 0.0)
        
        project = Project.objects.create(
            name=p_name,
            status=p_status,
            deadline=p_deadline,
            expected_revenue=p_expected,
            income=p_income
        )
        
        if p_income > 0:
            ProjectIncome.objects.create(project=project, amount=p_income)
            
        return redirect('dashboard')
    return render(request, 'dashboard/add_project.html')


def delete_project_view(request, pk):
    if request.user.is_staff:
        project = get_object_or_404(Project, pk=pk)
        if project.status == 'Completed':
            project.delete()
    return redirect('dashboard')


def edit_project_view(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    project = get_object_or_404(Project, pk=pk)
    if request.method == 'POST':
        added_income = request.POST.get('added_income')
        new_status = request.POST.get('status')
        
        if added_income:
            income_val = float(added_income)
            ProjectIncome.objects.create(project=project, amount=income_val)
            project.income = float(project.income) + income_val
            
        if new_status:
            project.status = new_status
            
        project.save()
        return redirect('dashboard')
        
    return render(request, 'dashboard/edit_project.html', {'project': project})


def delete_item_view(request, item_id):
    is_supervisor = check_is_supervisor(request.user)
    if request.user.is_staff or is_supervisor:
        item = get_object_or_404(ProjectItem, id=item_id)
        project_id = item.project.id
        item.delete()
        return redirect('project_detail', pk=project_id)
    return redirect('dashboard')


# ==========================================
# STAFF MANAGEMENT VIEWS
# ==========================================
def admin_mark_attendance_view(request):
    is_supervisor = check_is_supervisor(request.user)
    
    if request.method == 'POST' and (request.user.is_staff or is_supervisor):
        today = timezone.now().date()
        present_worker_ids = request.POST.getlist('present_workers')
        Attendance.objects.filter(date=today).delete()
        
        for worker_id in present_worker_ids:
            worker_user = get_object_or_404(User, id=worker_id)
            Attendance.objects.create(user=worker_user, date=today)
            
    return redirect('dashboard')


def edit_worker_wage_view(request, worker_id):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    worker = get_object_or_404(Worker, id=worker_id)
    
    if request.method == 'POST':
        new_wage = request.POST.get('daily_wage')
        if new_wage:
            worker.daily_wage = float(new_wage)
            worker.save()
            return redirect('dashboard')
            
    return render(request, 'dashboard/edit_worker_wage.html', {'worker': worker})


def toggle_worker_attendance_view(request, worker_id):
    is_supervisor = check_is_supervisor(request.user)
    
    if request.method == 'POST' and (request.user.is_staff or is_supervisor):
        worker = get_object_or_404(Worker, id=worker_id)
        today = timezone.now().date()
        attendance = Attendance.objects.filter(user=worker.user, date=today)
        
        if attendance.exists():
            attendance.delete()
            messages.success(request, f"Removed attendance for {worker.full_name}.")
        else:
            Attendance.objects.create(user=worker.user, date=today)
            messages.success(request, f"Marked {worker.full_name} as present.")
            
    return redirect('dashboard')


# ==========================================
# PAYMENT AND PAYSLIP VIEWS
# ==========================================
def worker_payment_view(request, worker_id):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    worker = get_object_or_404(Worker, id=worker_id)
    
    if request.method == 'POST' and 'pay_salary' in request.POST:
        selected_attendance_ids = request.POST.getlist('attendance_ids')
        
        if selected_attendance_ids:
            attendances = Attendance.objects.filter(id__in=selected_attendance_ids, is_paid=False)
            days_count = attendances.count()
            total_amount = float(days_count) * float(worker.daily_wage)
            
            if total_amount > 0:
                payment = Payment.objects.create(
                    user=worker.user,
                    amount=total_amount,
                    description=f"Salary for {days_count} days"
                )
                attendances.update(is_paid=True, payment=payment)
                messages.success(request, f"Successfully paid Rs. {total_amount} for {days_count} days.")
                
        return redirect('worker_payment', worker_id=worker.id)

    unpaid_attendances = Attendance.objects.filter(
        user=worker.user, 
        is_present=True, 
        is_paid=False
    ).order_by('-date')
   
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    past_payments = Payment.objects.filter(user=worker.user).order_by('-date_paid')
    
    total_filtered_paid = 0.0
    if start_date and end_date:
        past_payments = past_payments.filter(date_paid__range=[start_date, end_date])
        total_filtered_paid = sum(float(p.amount) for p in past_payments)
    
    context = {
        'worker': worker,
        'unpaid_attendances': unpaid_attendances,
        'past_payments': past_payments,
        'start_date': start_date,
        'end_date': end_date,
        'total_filtered_paid': total_filtered_paid
    }
    return render(request, 'dashboard/worker_payment.html', context)


def download_payslip_view(request, payment_id):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    payment = get_object_or_404(Payment, id=payment_id)
    template_path = 'dashboard/payslip_pdf.html'
    context = {'payment': payment}
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Payslip_{payment.user.username}_{payment.id}.pdf"'
    
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error occurred while generating PDF <pre>' + html + '</pre>')
    return response


def export_expenses_pdf(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    ledger = []
    
    # 1. Salary Payments
    payments = Payment.objects.all()
    if start_date and end_date:
        payments = payments.filter(date_paid__range=[start_date, end_date])
        
    for pay in payments:
        worker_name = pay.user.username
        if hasattr(pay.user, 'worker'):
            worker_name = pay.user.worker.full_name
        ledger.append({
            'date': getattr(pay, 'date_paid', timezone.now().date()),
            'description': f"Salary Paid to {worker_name}",
            'category': 'Salary',
            'amount': float(pay.amount)
        })
        
    # 2. Project Materials
    items = ProjectItem.objects.all()
    for item in items:
        item_date = getattr(item, 'date_added', timezone.now().date())
        
        if start_date and end_date:
            if not (start_date <= str(item_date) <= end_date):
                continue

        ledger.append({
            'date': item_date,
            'description': f"{item.item_name} (For: {item.project.name})",
            'category': 'Material',
            'amount': float(item.total_cost)
        })

    # 3. Material Returns (Deducted from total expense in PDF)
    returns = ItemReturn.objects.all()
    for ret in returns:
        ret_date = ret.date_returned
        if start_date and end_date:
            if not (start_date <= str(ret_date) <= end_date):
                continue

        ledger.append({
            'date': ret_date,
            'description': f"Returned: {ret.return_quantity}x {ret.item.item_name} (For: {ret.item.project.name})",
            'category': 'Material Return',
            'amount': -float(ret.refund_amount)
        })
    
    ledger.sort(key=lambda x: str(x['date']), reverse=True)
    total_expense = sum(float(item['amount']) for item in ledger)

    context = {
        'ledger': ledger,
        'start_date': start_date,
        'end_date': end_date,
        'total_expense': total_expense
    }
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Expense_Report.pdf"'
    
    template_path = 'dashboard/expense_report_pdf.html'
    template = get_template(template_path)
    html = template.render(context)
    pisa_status = pisa.CreatePDF(html, dest=response)
    
    if pisa_status.err:
        return HttpResponse('Error occurred while generating PDF <pre>' + html + '</pre>')
    return response


# ==========================================
# INCOME BREAKDOWN VIEW
# ==========================================
def project_income_breakdown(request, project_id):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    project = get_object_or_404(Project, id=project_id)
    if project.income > 0 and not project.income_installments.exists():
        ProjectIncome.objects.create(
            project=project, 
            amount=project.income
        )
        
    installments = project.income_installments.all().order_by('-date_received')
    return render(request, 'dashboard/income_breakdown.html', {'project': project, 'installments': installments})


# ==========================================
# RETURN ITEM VIEW
# ==========================================
def return_item_view(request, item_id):
    is_supervisor = check_is_supervisor(request.user)
    if not (request.user.is_staff or is_supervisor):
        return redirect('dashboard')
        
    item = get_object_or_404(ProjectItem, id=item_id)
    if request.method == 'POST':
        r_qty = int(request.POST.get('return_qty') or 0)
        r_amount = float(request.POST.get('refund_amount') or 0.0)
        r_date = request.POST.get('return_date')
        
        if r_qty > 0 and r_amount >= 0:
            ItemReturn.objects.create(
                item=item,
                return_quantity=r_qty,
                refund_amount=r_amount,
                date_returned=r_date if r_date else timezone.now().date()
            )
            messages.success(request, f"Successfully returned {r_qty}x {item.item_name}!")
            
    return redirect('project_detail', pk=item.project.id)