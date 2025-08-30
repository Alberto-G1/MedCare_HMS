from django.db import models

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., Cardiology, Orthopedics")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)


    def __str__(self):
        return self.name


class Room(models.Model):
    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied'),
        ('MAINTENANCE', 'Under Maintenance'),
    )

    room_number = models.CharField(max_length=20)
    room_type = models.CharField(max_length=20, choices=(('GENERAL', 'General Ward'), ('ICU', 'ICU'), ('PRIVATE', 'Private Room')))
    department = models.ForeignKey(Department, on_delete=models.PROTECT)
    
    capacity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    is_active = models.BooleanField(default=True) # For soft delete

    class Meta:
        # Ensures a room number is unique only within a specific department
        unique_together = ('room_number', 'department')

    def __str__(self):
        activity = "Active" if self.is_active else "Inactive"
        return f"Room {self.room_number} ({self.department.name}) - {self.get_status_display()} [{activity}]"