from rest_framework import serializers
from django.utils import timezone
from ..models import Lead, Showing, RentalApplication, LeadFollowUp

class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
        read_only_fields = ['organization', 'created_at', 'updated_at']

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'active_organization'):
            validated_data['organization'] = request.active_organization
        return super().create(validated_data)

class ShowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Showing
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def update(self, instance, validated_data):
        status_value = validated_data.get('status')
        if status_value == Showing.Status.COMPLETED and not instance.completed_at:
            validated_data['completed_at'] = timezone.now()
        return super().update(instance, validated_data)

class RentalApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalApplication
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'submission_date']


class LeadFollowUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadFollowUp
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'completed_at']

    def update(self, instance, validated_data):
        status_value = validated_data.get('status')
        if status_value == LeadFollowUp.Status.DONE and not instance.completed_at:
            validated_data['completed_at'] = timezone.now()
        return super().update(instance, validated_data)
