from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# 1. Project Model 
class Project(models.Model):
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=50, default='Ongoing')
    expected_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0.00) # Money coming in from the client
    income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    deadline = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name

# 2. Items provided to the project
class ProjectItem(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2) # Cost for these items
    date_added = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.quantity} x {self.item_name} for {self.project.name}"

# 3. Worker Model (Cleaned up and combined)
class Worker(models.Model):
    # Links the standard Django authentication user to this HR profile
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    mobile = models.CharField(max_length=15)
    nic = models.CharField(max_length=15)
    address = models.TextField()

    is_supervisor = models.BooleanField(default=False)
    
    # New fields for daily salary calculation
    daily_wage = models.FloatField(default=0.0)
    
    ROLE_CHOICES = (
        ('Manager', 'Manager'),
        ('Engineer', 'Engineer'),
        ('Supervisor', 'Supervisor'),
        ('Technician', 'Technician'),
        ('Laborer', 'Laborer'), 
    )
    job_role = models.CharField(max_length=50, choices=ROLE_CHOICES)

    def __str__(self):
        return self.full_name

# 4. Project Registration Model
class ProjectRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return f"{self.user.username} registered for {self.project.name}"

# 5. Attendance Model (Updated for Admin Daily Marking)
class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Made project optional since admin marks overall daily presence
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    is_present = models.BooleanField(default=True)
    time_in = models.TimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, null=True, blank=True, related_name='covered_attendances')

    class Meta:
        # Prevents marking the same worker twice on the same day
        unique_together = ('user', 'date')

    def __str__(self):
        return f"{self.user.username} present on {self.date}"

# 6. Payment Model (New - For tracking salary payments to staff)
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.FloatField()
    date_paid = models.DateField(default=timezone.now)
    description = models.CharField(max_length=200, default="Salary Payment")

    def __str__(self):
        return f"{self.user.username} received Rs. {self.amount}"

class ProjectIncome(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='income_installments')
    amount = models.FloatField(default=0.0)
    date_received = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.project.name} - Rs. {self.amount}"

class ItemReturn(models.Model):
    item = models.ForeignKey(ProjectItem, on_delete=models.CASCADE, related_name='returns')
    return_quantity = models.IntegerField(default=1)
    refund_amount = models.FloatField(default=0.0)
    date_returned = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Returned {self.return_quantity} of {self.item.item_name}"