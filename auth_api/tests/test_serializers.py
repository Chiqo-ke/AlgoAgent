from rest_framework import serializers
from auth_api.models import YourModel

class YourModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = YourModel
        fields = '__all__'

def test_your_model_serializer():
    instance = YourModel(field1='value1', field2='value2')
    serializer = YourModelSerializer(instance)
    assert serializer.data == {'field1': 'value1', 'field2': 'value2'}