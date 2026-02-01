from django import forms
from django.contrib.auth.models import User
from django.db import transaction
# Importamos os novos modelos aqui
from .models import Empresa, Funcionario, Setor, NormaRegulamentadora, EPI, TipoEPI, Localizacao

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

class SetorForm(forms.ModelForm):
    nrs_obrigatorias = forms.ModelMultipleChoiceField(
        queryset=NormaRegulamentadora.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="NRs Aplicáveis"
    )
    class Meta:
        model = Setor
        fields = ['nome', 'nrs_obrigatorias', 'epis_obrigatorios', 'vacinas_necessarias', 'treinamentos']
        widgets = {
            'epis_obrigatorios': forms.Textarea(attrs={'rows': 2}),
            'vacinas_necessarias': forms.Textarea(attrs={'rows': 2}),
            'treinamentos': forms.Textarea(attrs={'rows': 2}),
        }

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['nome', 'cpf', 'cargo', 'setor', 'data_admissao']
        widgets = {'data_admissao': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['setor'].queryset = Setor.objects.filter(empresa_id=empresa_id)

# --- AQUI ESTÁ A CORREÇÃO PRINCIPAL ---
class TipoEPIForm(forms.ModelForm):
    class Meta:
        model = TipoEPI
        fields = ['nome']

class LocalizacaoForm(forms.ModelForm):
    class Meta:
        model = Localizacao
        fields = ['nome']

class EPIForm(forms.ModelForm):
    class Meta:
        model = EPI
        # AGORA USAMOS OS CAMPOS CERTOS: 'tipo' e 'local'
        fields = ['tipo', 'local', 'codigo_unico', 'tamanho', 'ca', 'quantidade', 'data_validade']
        widgets = {'data_validade': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['tipo'].queryset = TipoEPI.objects.filter(empresa_id=empresa_id)
            self.fields['local'].queryset = Localizacao.objects.filter(empresa_id=empresa_id)