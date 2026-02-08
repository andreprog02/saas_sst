from django import forms
from django.contrib.auth.models import User
from django.http import JsonResponse

from django.db import transaction
from .models import (
    Empresa, Funcionario, Setor, NormaRegulamentadora, 
    EPI, TipoEPI, Localizacao, Vacina, 
    Advertencia, TipoAdvertencia,
    Extintor, InspecaoExtintor,
    Equipamento, InspecaoEquipamento,
    ControleVacina, EntregaEPI, TreinamentoFuncionario,
    Afastamento, AcidenteTrabalho, ProdutoQuimico,
    TipoEspecialidade, Hospital,
    CategoriaEPI, MarcaEPI, TamanhoEPI, MovimentacaoEstoque
)

# --- WIDGETS ---
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

class MultipleFileField(forms.FileField):
    def to_python(self, data):
        if not data: return None
        if not isinstance(data, list):
            if hasattr(data, 'chunks'): return [data]
            return None
        return data

    def clean(self, data, initial=None):
        if not data and self.required:
            raise forms.ValidationError(self.error_messages['required'], code='required')
        return data

# 1. EMPRESA
class CadastroSaaSForm(forms.Form):
    username = forms.CharField(label="Seu Nome", max_length=150)
    email_login = forms.EmailField(label="E-mail de Login")
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")
    nome_empresa = forms.CharField(label="Nome da Empresa")
    cnpj = forms.CharField(label="CNPJ")
    telefone = forms.CharField(label="Telefone")
    email_empresa = forms.EmailField(label="E-mail da Empresa")
    endereco = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label="Endereço Completo")

    def save(self):
        with transaction.atomic():
            empresa = Empresa.objects.create(
                nome_fantasia=self.cleaned_data['nome_empresa'],
                razao_social=self.cleaned_data['nome_empresa'],
                cnpj=self.cleaned_data['cnpj'],
                telefone=self.cleaned_data['telefone'],
                email_contato=self.cleaned_data['email_empresa'],
                endereco=self.cleaned_data['endereco']
            )
            user = User.objects.create_user(
                username=self.cleaned_data['email_login'],
                email=self.cleaned_data['email_login'],
                password=self.cleaned_data['password']
            )
            from .models import PerfilUsuario
            PerfilUsuario.objects.create(usuario=user, empresa=empresa, is_admin=True)
            return user

# 2. SETORES E VACINAS
class VacinaForm(forms.ModelForm):
    class Meta:
        model = Vacina
        fields = ['nome', 'descricao', 'meses_reforco']
        widgets = {'descricao': forms.Textarea(attrs={'rows': 2})}

class SetorForm(forms.ModelForm):
    nrs_obrigatorias = forms.ModelMultipleChoiceField(
        queryset=NormaRegulamentadora.objects.all(), widget=forms.CheckboxSelectMultiple, required=False, label="NRs Aplicáveis"
    )
    vacinas_padrao = forms.ModelMultipleChoiceField(
        queryset=Vacina.objects.none(), widget=forms.CheckboxSelectMultiple, required=False, label="Vacinas Exigidas"
    )
    # Mantido para compatibilidade, mas idealmente usaria o novo modelo de EPI se necessário
    epis_obrigatorios = forms.ModelMultipleChoiceField(
        queryset=TipoEPI.objects.none(), widget=forms.CheckboxSelectMultiple, required=False, label="EPIs Obrigatórios (Tipos)"
    )

    class Meta:
        model = Setor
        fields = ['nome', 'nrs_obrigatorias', 'vacinas_padrao', 'epis_obrigatorios', 'treinamentos']
        widgets = {'treinamentos': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, user_empresa=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user_empresa:
            self.fields['vacinas_padrao'].queryset = Vacina.objects.filter(empresa=user_empresa)
            self.fields['epis_obrigatorios'].queryset = TipoEPI.objects.filter(empresa=user_empresa)

# 3. FUNCIONÁRIOS
class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['nome', 'cpf', 'cargo', 'setor', 'data_admissao', 'situacao', 'motivo_afastamento', 'ativo']
        widgets = {
            'data_admissao': forms.DateInput(attrs={'type': 'date'}),
            'motivo_afastamento': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Detalhes...'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['setor'].queryset = Setor.objects.filter(empresa_id=empresa_id)

# 4. EPIs (ANTIGOS E NOVOS)

# -- Forms de Compatibilidade (Restaurados para corrigir o erro) --
class TipoEPIForm(forms.ModelForm):
    class Meta:
        model = TipoEPI
        fields = ['nome']

class LocalizacaoForm(forms.ModelForm):
    class Meta:
        model = Localizacao
        fields = ['nome']
# -------------------------------------------------------------

# -- Novos Forms do Estoque Avançado --
class CategoriaEPIForm(forms.ModelForm):
    class Meta:
        model = CategoriaEPI
        fields = ['nome']

class MarcaEPIForm(forms.ModelForm):
    class Meta:
        model = MarcaEPI
        fields = ['nome']

class TamanhoEPIForm(forms.ModelForm):
    class Meta:
        model = TamanhoEPI
        fields = ['tamanho']

class EPIForm(forms.ModelForm):
    class Meta:
        model = EPI
        fields = [
            'categoria', 'marca', 'modelo', 'tamanho', 
            'ca', 'quantidade_minima', 'data_validade', 'local'
        ]
        widgets = {
            'data_validade': forms.DateInput(attrs={'type': 'date'}),
            'ca': forms.NumberInput(attrs={'min': 0}),
            'quantidade_minima': forms.NumberInput(attrs={'min': 0}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['categoria'].queryset = CategoriaEPI.objects.filter(empresa_id=empresa_id)
            self.fields['marca'].queryset = MarcaEPI.objects.filter(empresa_id=empresa_id)
            self.fields['tamanho'].queryset = TamanhoEPI.objects.filter(empresa_id=empresa_id)
            self.fields['local'].queryset = Localizacao.objects.filter(empresa_id=empresa_id)

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['categoria'].queryset = CategoriaEPI.objects.filter(empresa_id=empresa_id)
            self.fields['marca'].queryset = MarcaEPI.objects.filter(empresa_id=empresa_id)
            self.fields['tamanho'].queryset = TamanhoEPI.objects.filter(empresa_id=empresa_id)
            self.fields['local'].queryset = Localizacao.objects.filter(empresa_id=empresa_id)

class EstoqueEntradaForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ['quantidade', 'data_movimento', 'observacao']
        widgets = {
            'data_movimento': forms.DateInput(attrs={'type': 'date'}),
            'observacao': forms.TextInput(attrs={'placeholder': 'Ex: Compra Nota Fiscal 123'}),
            'quantidade': forms.NumberInput(attrs={'min': 1}),
        }

# 5. ADVERTÊNCIAS
class TipoAdvertenciaForm(forms.ModelForm):
    class Meta:
        model = TipoAdvertencia
        fields = ['titulo', 'descricao_padrao']
        widgets = {'descricao_padrao': forms.Textarea(attrs={'rows': 4})}

class AdvertenciaForm(forms.ModelForm):
    class Meta:
        model = Advertencia
        fields = ['funcionario', 'tipo', 'data_incidente', 'detalhes']
        widgets = {
            'data_incidente': forms.DateInput(attrs={'type': 'date'}),
            'detalhes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['funcionario'].queryset = Funcionario.objects.filter(empresa_id=empresa_id, ativo=True)
            self.fields['tipo'].queryset = TipoAdvertencia.objects.filter(empresa_id=empresa_id)

class AdvertenciaFuncionarioForm(forms.ModelForm):
    class Meta:
        model = Advertencia
        exclude = ['empresa', 'funcionario', 'reincidente', 'criado_em']
        widgets = {
            'data_incidente': forms.DateInput(attrs={'type': 'date'}),
            'detalhes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['tipo'].queryset = TipoAdvertencia.objects.filter(empresa_id=empresa_id)

# 6. EXTINTORES
class ExtintorForm(forms.ModelForm):
    class Meta:
        model = Extintor
        exclude = ['empresa']
        widgets = {
            'data_ultima_manutencao': forms.DateInput(attrs={'type': 'date'}),
            'data_proxima_manutencao': forms.DateInput(attrs={'type': 'date'}),
            'data_teste_hidrostatico': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['localizacao'].queryset = Localizacao.objects.filter(empresa_id=empresa_id)

class InspecaoExtintorForm(forms.ModelForm):
    fotos = MultipleFileField(
        widget=MultipleFileInput(attrs={'multiple': True}), label="Evidências Fotográficas", required=False
    )
    class Meta:
        model = InspecaoExtintor
        fields = ['data_inspecao', 'responsavel', 'lacre_intacto', 'manometro_pressao_ok', 'sinalizacao_visivel', 'acesso_livre', 'mangueira_integra', 'observacoes', 'fotos']
        widgets = {'data_inspecao': forms.DateInput(attrs={'type': 'date'}), 'observacoes': forms.Textarea(attrs={'rows': 2})}

# 7. OUTROS EQUIPAMENTOS
class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = ['tipo', 'nome', 'localizacao', 'data_instalacao', 'data_validade', 'especificacao', 'imagem']
        widgets = {'data_instalacao': forms.DateInput(attrs={'type': 'date'}), 'data_validade': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['localizacao'].queryset = Localizacao.objects.filter(empresa_id=empresa_id)

class InspecaoEquipamentoForm(forms.ModelForm):
    arquivos = MultipleFileField(
        widget=MultipleFileInput(attrs={'multiple': True}), label="Evidências", required=False
    )
    class Meta:
        model = InspecaoEquipamento
        fields = ['data_inspecao', 'responsavel', 'item_integro', 'acesso_livre', 'sinalizacao_ok', 'teste_funcional', 'observacoes', 'arquivos']
        widgets = {'data_inspecao': forms.DateInput(attrs={'type': 'date'}), 'observacoes': forms.Textarea(attrs={'rows': 2})}

# 8. PRONTUÁRIO (VACINAS, EPIs, TREINAMENTOS)
class ControleVacinaForm(forms.ModelForm):
    class Meta:
        model = ControleVacina
        fields = ['vacina', 'data_aplicacao', 'comprovante']
        widgets = {'data_aplicacao': forms.DateInput(attrs={'type': 'date'})}
    
    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['vacina'].queryset = Vacina.objects.filter(empresa_id=empresa_id)

class EntregaEPIForm(forms.ModelForm):
    class Meta:
        model = EntregaEPI
        fields = ['epi', 'data_entrega', 'quantidade', 'termo_assinado']
        widgets = {'data_entrega': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['epi'].queryset = EPI.objects.filter(empresa_id=empresa_id, quantidade__gt=0)

class TreinamentoFuncionarioForm(forms.ModelForm):
    class Meta:
        model = TreinamentoFuncionario
        fields = ['nome_treinamento', 'data_realizacao', 'data_validade', 'certificado']
        widgets = {
            'data_realizacao': forms.DateInput(attrs={'type': 'date'}),
            'data_validade': forms.DateInput(attrs={'type': 'date'}),
        }

# 9. NOVOS FORMS (AFASTAMENTO E ACIDENTE)
class AfastamentoForm(forms.ModelForm):
    class Meta:
        model = Afastamento
        fields = ['data_inicio', 'data_retorno', 'motivo', 'laudo']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_retorno': forms.DateInput(attrs={'type': 'date'}),
            'motivo': forms.Textarea(attrs={'rows': 3}),
        }

class AcidenteTrabalhoForm(forms.ModelForm):
    class Meta:
        model = AcidenteTrabalho
        fields = ['data_acidente', 'hora_acidente', 'local', 'descricao_motivo', 'arquivo_evidencia']
        widgets = {
            'data_acidente': forms.DateInput(attrs={'type': 'date'}),
            'hora_acidente': forms.TimeInput(attrs={'type': 'time'}),
            'descricao_motivo': forms.Textarea(attrs={'rows': 3}),
        }

class ProdutoQuimicoForm(forms.ModelForm):
    class Meta:
        model = ProdutoQuimico
        exclude = ['empresa', 'criado_em']
        widgets = {
            'data_fabricacao': forms.DateInput(attrs={'type': 'date'}),
            'data_validade': forms.DateInput(attrs={'type': 'date'}),
            'riscos': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descreva os riscos conforme rótulo ou FISPQ...'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['localizacao'].queryset = Localizacao.objects.filter(empresa_id=empresa_id)

class TipoEspecialidadeForm(forms.ModelForm):
    class Meta:
        model = TipoEspecialidade
        fields = ['nome']

class HospitalForm(forms.ModelForm):
    especialidades = forms.ModelMultipleChoiceField(
        queryset=TipoEspecialidade.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    class Meta:
        model = Hospital
        exclude = ['empresa', 'criado_em']
        widgets = {'endereco': forms.Textarea(attrs={'rows': 2})}
    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['especialidades'].queryset = TipoEspecialidade.objects.filter(empresa_id=empresa_id)

def api_criar_categoria_epi(request):
    if request.method == "POST":
        form = CategoriaEPIForm(request.POST)
        if form.is_valid():
            cat = form.save(commit=False)
            cat.empresa = request.user.perfil.empresa
            cat.save()
            return JsonResponse({'success': True, 'id': cat.id, 'nome': cat.nome})
    return JsonResponse({'success': False, 'error': 'Erro ao salvar'})

def api_criar_marca_epi(request):
    if request.method == "POST":
        form = MarcaEPIForm(request.POST)
        if form.is_valid():
            marca = form.save(commit=False)
            marca.empresa = request.user.perfil.empresa
            marca.save()
            return JsonResponse({'success': True, 'id': marca.id, 'nome': marca.nome})
    return JsonResponse({'success': False, 'error': 'Erro ao salvar'})

def api_criar_tamanho_epi(request):
    if request.method == "POST":
        form = TamanhoEPIForm(request.POST)
        if form.is_valid():
            tam = form.save(commit=False)
            tam.empresa = request.user.perfil.empresa
            tam.save()
            return JsonResponse({'success': True, 'id': tam.id, 'nome': tam.tamanho})
    return JsonResponse({'success': False, 'error': 'Erro ao salvar'})