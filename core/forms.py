# core/forms.py
from django import forms
from django.contrib.auth.models import User
from .models import Empresa, Funcionario, Setor, NormaRegulamentadora



class CadastroSaaSForm(forms.Form):
    # Dados do Usuário (Login)
    username = forms.CharField(label="Seu Nome", max_length=150)
    email_login = forms.EmailField(label="E-mail de Login")
    password = forms.CharField(widget=forms.PasswordInput, label="Senha")
    
    # Dados da Empresa (Tenant)
    nome_empresa = forms.CharField(label="Nome da Empresa")
    cnpj = forms.CharField(label="CNPJ")
    telefone = forms.CharField(label="Telefone")
    email_empresa = forms.EmailField(label="E-mail da Empresa")
    endereco = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label="Endereço Completo")

    def save(self):
        # Lógica Transacional: Salva tudo ou nada
        from django.db import transaction
        
        with transaction.atomic():
            # 1. Cria a Empresa
            empresa = Empresa.objects.create(
                nome_fantasia=self.cleaned_data['nome_empresa'],
                razao_social=self.cleaned_data['nome_empresa'], # Simplificado
                cnpj=self.cleaned_data['cnpj'],
                telefone=self.cleaned_data['telefone'],
                email_contato=self.cleaned_data['email_empresa'],
                endereco=self.cleaned_data['endereco']
            )
            
            # 2. Cria o Usuário de Login
            user = User.objects.create_user(
                username=self.cleaned_data['email_login'], # Usando email como username
                email=self.cleaned_data['email_login'],
                password=self.cleaned_data['password']
            )
            
            # 3. Cria o Vínculo (Perfil)
            from .models import PerfilUsuario
            PerfilUsuario.objects.create(
                usuario=user,
                empresa=empresa,
                is_admin=True
            )
            return user
        
class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        # Escolhemos quais campos o usuário preenche.
        # A 'empresa' NÃO entra aqui, pois vamos preencher automaticamente no código (segurança).
        fields = ['nome', 'cpf', 'cargo', 'setor', 'data_admissao']
        
        # Dica: Isso faz aparecer um calendáriozinho no navegador
        widgets = {
            'data_admissao': forms.DateInput(attrs={'type': 'date'}),
        }


class SetorForm(forms.ModelForm):
    class Meta:
        model = Setor
        fields = ['nome', 'epis_obrigatorios', 'nrs_obrigatorias', 'vacinas_necessarias', 'treinamentos']
        widgets = {
            'epis_obrigatorios': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ex: Bota, Capacete'}),
            'nrs_obrigatorias': forms.Textarea(attrs={'rows': 2}),
            'vacinas_necessarias': forms.Textarea(attrs={'rows': 2}),
            'treinamentos': forms.Textarea(attrs={'rows': 2}),
        }

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['nome', 'cpf', 'cargo', 'setor', 'data_admissao'] # 'setor' agora é um dropdown
        widgets = {
            'data_admissao': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FILTRO DE SEGURANÇA: Só mostra setores da MINHA empresa
        if empresa_id:
            self.fields['setor'].queryset = Setor.objects.filter(empresa_id=empresa_id)

class SetorForm(forms.ModelForm):
    # CheckboxSelectMultiple faz aparecer várias caixinhas para marcar
    nrs_obrigatorias = forms.ModelMultipleChoiceField(
        queryset=NormaRegulamentadora.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Normas Regulamentadoras Aplicáveis"
    )

    class Meta:
        model = Setor
        fields = ['nome', 'nrs_obrigatorias', 'epis_obrigatorios', 'vacinas_necessarias', 'treinamentos']
        widgets = {
            'epis_obrigatorios': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ex: Bota, Capacete'}),
            'vacinas_necessarias': forms.Textarea(attrs={'rows': 2}),
            'treinamentos': forms.Textarea(attrs={'rows': 2}),
        }

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['nome', 'cpf', 'cargo', 'setor', 'data_admissao'] # 'setor' agora é um dropdown
        widgets = {
            'data_admissao': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FILTRO DE SEGURANÇA: Só mostra setores da MINHA empresa
        if empresa_id:
            self.fields['setor'].queryset = Setor.objects.filter(empresa_id=empresa_id)