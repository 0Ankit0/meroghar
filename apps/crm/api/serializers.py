from rest_framework import serializers
from ..models import Lead, Showing, RentalApplication

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

class RentalApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentalApplication
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'submission_date']
