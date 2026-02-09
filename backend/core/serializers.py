from rest_framework import serializers
from .models import ProdutoQuimico, Localizacao

from rest_framework import serializers
from .models import ProdutoQuimico, Localizacao

class LocalizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Localizacao
        fields = ['id', 'nome']

class ProdutoQuimicoSerializer(serializers.ModelSerializer):
    # Traz o objeto localizacao completo (nome/id) ao invés de só o ID
    localizacao = LocalizacaoSerializer(read_only=True)
    
    # Campos calculados que adicionamos no Model
    status_validade = serializers.ReadOnlyField()
    ghs_riscos = serializers.SerializerMethodField()

    class Meta:
        model = ProdutoQuimico
        fields = [
            'id', 'nome', 'cas_number', 'concentracao', 
            'quantidade', 'unidade', 'localizacao', 
            'data_validade', 'status_validade', 
            'fispq', 'ghs_riscos'
        ]

    def get_ghs_riscos(self, obj):
        # Retorna a lista de riscos (Ex: ['Inflamável', 'Tóxico'])
        return obj.get_ghs_list()

class LocalizacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Localizacao
        fields = ['id', 'nome', 'empresa']

class ProdutoQuimicoSerializer(serializers.ModelSerializer):
    # Para mostrar o nome da localização em vez de apenas o ID
    localizacao = LocalizacaoSerializer(read_only=True) 
    
    # Campo calculado (como fizemos no model)
    status_validade = serializers.ReadOnlyField()

    class Meta:
        model = ProdutoQuimico
        fields = '__all__' # Ou liste os campos: ['id', 'nome', 'cas_number', 'quantidade', 'status_validade', ...]