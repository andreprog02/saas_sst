from django import forms
from django.contrib.auth.models import User
from django.forms import inlineformset_factory

# Importação única e completa de todos os modelos
from .models import (
    Empresa, Funcionario, Setor, NormaRegulamentadora, RiscoOcupacional,
    EPI, TipoEPI, CategoriaEPI, MarcaEPI, TamanhoEPI, Localizacao,
    Vacina, ControleVacina, EntregaEPI, TreinamentoFuncionario,
    Advertencia, TipoAdvertencia, Afastamento, AcidenteTrabalho,
    Extintor, InspecaoExtintor, Equipamento, InspecaoEquipamento,
    ProdutoQuimico, Hospital, TipoEspecialidade, Exame
)


# --- CADASTRO E LOGIN ---

class CadastroSaaSForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirmar Senha")
    nome_fantasia = forms.CharField(max_length=100, label="Nome da Empresa")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("As senhas não conferem.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            empresa = Empresa.objects.create(
                nome_fantasia=self.cleaned_data["nome_fantasia"],
                email_contato=self.cleaned_data["email"]
            )
            from .models import PerfilUsuario
            PerfilUsuario.objects.create(user=user, empresa=empresa)
        return user

# --- FUNCIONÁRIOS ---

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = [
            'foto',
            'nome', 'cpf', 'rg', 'matricula',           
            'data_nascimento', 'email', 'telefone',     
            'cargo', 'setor', 'data_admissao',          
            'situacao'                                  
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_admissao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'setor': forms.Select(attrs={'class': 'form-select'}),
            'situacao': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['setor'].queryset = Setor.objects.filter(empresa_id=empresa_id)

# --- SETORES ---

class SetorForm(forms.ModelForm):
    normas = forms.ModelMultipleChoiceField(
        queryset=NormaRegulamentadora.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Normas Regulamentadoras (NRs)"
    )
    riscos = forms.ModelMultipleChoiceField(
        queryset=RiscoOcupacional.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Riscos Ocupacionais"
    )

    class Meta:
        model = Setor
        fields = ['nome', 'descricao', 'responsavel']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'responsavel': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, empresa, *args, **kwargs):
        self.empresa = empresa
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['normas'].initial = self.instance.normas.all()
            self.fields['riscos'].initial = self.instance.riscos.all()

    def save_m2m(self):
        self.instance.normas.set(self.cleaned_data['normas'])
        self.instance.riscos.set(self.cleaned_data['riscos'])

# --- EPIs E ESTOQUE ---

class EPIForm(forms.ModelForm):
    class Meta:
        model = EPI
        fields = [
            'categoria', 'marca', 'modelo', 'tamanho', 
            'ca', 'data_validade', 'local',
            'quantidade', 'quantidade_minima'
        ]
        widgets = {
            'data_validade': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'quantidade_minima': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.Select(attrs={'class': 'form-select'}),
            'tamanho': forms.Select(attrs={'class': 'form-select'}),
            'local': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['categoria'].queryset = CategoriaEPI.objects.filter(empresa_id=empresa_id)
            self.fields['marca'].queryset = MarcaEPI.objects.filter(empresa_id=empresa_id)
            self.fields['tamanho'].queryset = TamanhoEPI.objects.filter(empresa_id=empresa_id)
            self.fields['local'].queryset = Localizacao.objects.filter(empresa_id=empresa_id)

class EntregaEPIForm(forms.ModelForm):
    class Meta:
        model = EntregaEPI
        fields = ['epi', 'quantidade', 'data_entrega', 'termo_assinado']
        widgets = {
            'data_entrega': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'epi': forms.Select(attrs={'class': 'form-select'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'termo_assinado': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['epi'].queryset = EPI.objects.filter(empresa_id=empresa_id, quantidade__gt=0, ativo=True)

# --- FORMS RÁPIDOS ---

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

class TipoEspecialidadeForm(forms.ModelForm):
    class Meta:
        model = TipoEspecialidade
        fields = ['nome']
# --- PRONTUÁRIO ---

class ControleVacinaForm(forms.ModelForm):
    class Meta:
        model = ControleVacina
        fields = ['vacina', 'data_aplicacao', 'comprovante']
        widgets = {
            'data_aplicacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'vacina': forms.Select(attrs={'class': 'form-select'}),
            'comprovante': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['vacina'].queryset = Vacina.objects.filter(empresa_id=empresa_id)

class TreinamentoFuncionarioForm(forms.ModelForm):
    class Meta:
        model = TreinamentoFuncionario
        fields = ['nome_treinamento', 'data_realizacao', 'data_validade', 'certificado']
        widgets = {
            'data_realizacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_validade': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nome_treinamento': forms.TextInput(attrs={'class': 'form-control'}),
            'certificado': forms.FileInput(attrs={'class': 'form-control'}),
        }

class AfastamentoForm(forms.ModelForm):
    class Meta:
        model = Afastamento
        # Corrigido: usa os nomes 'motivo' e 'laudo' do model
        fields = ['motivo', 'data_inicio', 'data_retorno', 'laudo'] 
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_retorno': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'laudo': forms.FileInput(attrs={'class': 'form-control'}),
        }

class AcidenteTrabalhoForm(forms.ModelForm):
    class Meta:
        model = AcidenteTrabalho
        fields = ['data_acidente', 'hora_acidente', 'local', 'descricao_motivo', 'arquivo_evidencia']
        widgets = {
            'data_acidente': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_acidente': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'local': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao_motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'arquivo_evidencia': forms.FileInput(attrs={'class': 'form-control'}),
        }

class AdvertenciaFuncionarioForm(forms.ModelForm):
    class Meta:
        model = Advertencia
        # Corrigido: usa 'detalhes' do model
        fields = ['tipo', 'data_incidente', 'detalhes']
        widgets = {
            'data_incidente': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'detalhes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['tipo'].queryset = TipoAdvertencia.objects.filter(empresa_id=empresa_id)

class AdvertenciaForm(forms.ModelForm):
    class Meta:
        model = Advertencia
        fields = ['funcionario', 'tipo', 'data_incidente', 'detalhes']
        widgets = {
            'data_incidente': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'funcionario': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'detalhes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['funcionario'].queryset = Funcionario.objects.filter(empresa_id=empresa_id)
            self.fields['tipo'].queryset = TipoAdvertencia.objects.filter(empresa_id=empresa_id)

# --- EXTINTORES E EQUIPAMENTOS ---

class ExtintorForm(forms.ModelForm):
    class Meta:
        model = Extintor
        # Corrigido: usa 'codigo_patrimonial', 'data_teste_hidrostatico' etc
        fields = [
            'codigo_patrimonial', 'numero_serie', 'classe', 'agente', 'capacidade', 
            'localizacao', 'classe_risco', 'altura_instalacao',
            'data_teste_hidrostatico', 'data_proxima_manutencao', 'data_ultima_manutencao'
        ]
        widgets = {
            'data_teste_hidrostatico': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_proxima_manutencao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_ultima_manutencao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            
            'codigo_patrimonial': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'classe_risco': forms.TextInput(attrs={'class': 'form-control'}),
            'altura_instalacao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'classe': forms.Select(attrs={'class': 'form-select'}),
            'agente': forms.Select(attrs={'class': 'form-select'}),
            'capacidade': forms.TextInput(attrs={'class': 'form-control'}),
            'localizacao': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['localizacao'].queryset = Localizacao.objects.filter(empresa_id=empresa_id)

class InspecaoExtintorForm(forms.ModelForm):
    class Meta:
        model = InspecaoExtintor
        # Corrigido: removemos 'foto', 'pintura' e 'sinalizacao' que não existem no model
        fields = ['data_inspecao', 'responsavel', 'lacre_intacto', 'manometro_pressao_ok', 'mangueira_integra', 'observacoes']
        widgets = {
            'data_inspecao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'responsavel': forms.TextInput(attrs={'class': 'form-control'}),
            'lacre_intacto': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'manometro_pressao_ok': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'mangueira_integra': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EquipamentoForm(forms.ModelForm):
    class Meta:
        model = Equipamento
        fields = ['nome', 'tipo', 'localizacao', 'data_validade', 'qrcode_data']
        widgets = {
            'data_validade': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'localizacao': forms.Select(attrs={'class': 'form-select'}),
            'qrcode_data': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['localizacao'].queryset = Localizacao.objects.filter(empresa_id=empresa_id)

class InspecaoEquipamentoForm(forms.ModelForm):
    class Meta:
        model = InspecaoEquipamento
        # Corrigido: removemos 'foto' (tabela separada)
        fields = ['data_inspecao', 'responsavel', 'status', 'observacoes']
        widgets = {
            'data_inspecao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'responsavel': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.TextInput(attrs={'class': 'form-control'}),
        }

# --- PRODUTOS QUÍMICOS ---

class ProdutoQuimicoForm(forms.ModelForm):
    class Meta:
        model = ProdutoQuimico
        fields = ['nome', 'cas_number', 'concentracao', 'quantidade', 'unidade', 'setor', 'localizacao', 'classificacao_ghs', 'data_validade_fispq', 'fispq', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Ácido Sulfúrico'}),
            'cas_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 7664-93-9'}),
            'concentracao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 98%'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'unidade': forms.Select(attrs={'class': 'form-select'}),
            'setor': forms.Select(attrs={'class': 'form-select'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Armário A1'}),
            'classificacao_ghs': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Corrosivo, Tóxico'}),
            'data_validade_fispq': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['setor'].queryset = Setor.objects.filter(empresa_id=empresa_id)

# --- HOSPITAIS ---

class HospitalForm(forms.ModelForm):
    especialidades = forms.ModelMultipleChoiceField(
        queryset=TipoEspecialidade.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Hospital
        fields = ['nome', 'telefone', 'endereco', 'horario_atendimento', 'mapa_link']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control'}),
            'horario_atendimento': forms.TextInput(attrs={'class': 'form-control'}),
            'mapa_link': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['especialidades'].queryset = TipoEspecialidade.objects.filter(empresa_id=empresa_id)
        
        if self.instance.pk:
            self.fields['especialidades'].initial = self.instance.especialidades.all()

    def save_m2m(self):
        self.instance.especialidades.set(self.cleaned_data['especialidades'])

# --- CONFIGURAÇÕES GERAIS ---

class LocalizacaoForm(forms.ModelForm):
    class Meta:
        model = Localizacao
        fields = ['nome']
        widgets = {'nome': forms.TextInput(attrs={'class': 'form-control'})}

class TipoEPIForm(forms.ModelForm):
    class Meta:
        model = TipoEPI
        fields = ['nome']
        widgets = {'nome': forms.TextInput(attrs={'class': 'form-control'})}

class VacinaForm(forms.ModelForm):
    class Meta:
        model = Vacina
        # CORRIGIDO: mudado de 'validade_meses' para 'meses_reforco'
        fields = ['nome', 'descricao', 'meses_reforco']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'meses_reforco': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class TipoAdvertenciaForm(forms.ModelForm):
    class Meta:
        model = TipoAdvertencia
        fields = ['titulo', 'descricao_padrao']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao_padrao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class RiscoOcupacionalForm(forms.ModelForm):
    class Meta:
        model = RiscoOcupacional
        fields = ['tipo', 'agente', 'fonte_geradora', 'intensidade', 'possiveis_danos']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'agente': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Ruído Contínuo'}),
            'fonte_geradora': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Compressor'}),
            'intensidade': forms.Select(attrs={'class': 'form-select'}),
            'possiveis_danos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)

class ExameForm(forms.ModelForm):
    class Meta:
        model = Exame
        fields = ['tipo', 'data_realizacao', 'data_vencimento', 'observacoes', 'arquivo']
        widgets = {
            'tipo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: ASO Admissional, Audiometria...'}),
            'data_realizacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_vencimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'arquivo': forms.FileInput(attrs={'class': 'form-control'}),
        }