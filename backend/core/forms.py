from django import forms
from django.contrib.auth.models import User
from .models import EPI, CategoriaEPI, TipoEPI, MarcaEPI, TamanhoEPI, Localizacao
# --- IMPORTAÇÃO DOS MODELOS (CORRIGIDA: CARGO ADICIONADO) ---
from .models import (
    Empresa, Funcionario, Setor, Cargo, NormaRegulamentadora, RiscoOcupacional,
    EPI, TipoEPI, CategoriaEPI, MarcaEPI, TamanhoEPI, Localizacao,
    Vacina, ControleVacina, EntregaEPI, TreinamentoFuncionario,
    Advertencia, TipoAdvertencia, Afastamento, AcidenteTrabalho,
    Extintor, InspecaoExtintor, Equipamento, InspecaoEquipamento,
    ProdutoQuimico, Hospital, TipoEspecialidade, Exame, MatrizRiscoEPI, TipoExame,
    ArCondicionado, EquipamentoNR13
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

# --- FUNCIONÁRIO ---

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = [
            'nome', 'cpf', 'rg', 'data_nascimento', 'email', 'telefone',
            'cep', 'endereco', 'numero', 'bairro', 'cidade', 'estado', 'complemento',
            'matricula', 'setor', 'cargo', 'funcao', 'data_admissao', 'turno', 'supervisor',
            'tipo_sanguineo', 'alergias', 'medicamentos', 'observacoes_saude',
            'situacao', 'motivo_afastamento', 'foto'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_admissao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'setor': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.Select(attrs={'class': 'form-select'}), 
            'turno': forms.Select(attrs={'class': 'form-select'}),
            'situacao': forms.Select(attrs={'class': 'form-select'}),
            'foto': forms.FileInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'data-mask': '000.000.000-00'}),
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'cep': forms.TextInput(attrs={'class': 'form-control', 'id': 'cep'}),
            'endereco': forms.TextInput(attrs={'class': 'form-control', 'id': 'logradouro'}),
            'numero': forms.TextInput(attrs={'class': 'form-control', 'id': 'numero'}),
            'bairro': forms.TextInput(attrs={'class': 'form-control', 'id': 'bairro'}),
            'cidade': forms.TextInput(attrs={'class': 'form-control', 'id': 'cidade'}),
            'estado': forms.TextInput(attrs={'class': 'form-control', 'id': 'uf'}),
            'complemento': forms.TextInput(attrs={'class': 'form-control'}),
            'matricula': forms.TextInput(attrs={'class': 'form-control'}),
            'funcao': forms.TextInput(attrs={'class': 'form-control'}),
            'supervisor': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_sanguineo': forms.TextInput(attrs={'class': 'form-control'}),
            'alergias': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'medicamentos': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'observacoes_saude': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'motivo_afastamento': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['setor'].queryset = Setor.objects.filter(empresa_id=empresa_id)
            self.fields['cargo'].queryset = Cargo.objects.filter(empresa_id=empresa_id)

# --- SETORES ---

class SetorForm(forms.ModelForm):
    # Campos M2M manuais para o formulário
    riscos = forms.ModelMultipleChoiceField(
        queryset=RiscoOcupacional.objects.none(), 
        widget=forms.CheckboxSelectMultiple, 
        required=False,
        label="Riscos Globais (Todo o Setor)"
    )
    normas = forms.ModelMultipleChoiceField(
        queryset=NormaRegulamentadora.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Normas Regulamentadoras"
    )
    vacinas = forms.ModelMultipleChoiceField(
        queryset=Vacina.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Vacinas Padrão"
    )
    exames = forms.ModelMultipleChoiceField(
        queryset=TipoExame.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Exames Padrão"
    )
    epis = forms.ModelMultipleChoiceField(
        queryset=TipoEPI.objects.none(), # Começa vazio
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="EPIs Básicos (Tipos)"
    )

    class Meta:
        model = Setor
        fields = ['nome', 'descricao', 'responsavel', 'riscos', 'normas', 'vacinas', 'exames', 'epis']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'responsavel': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        # Captura 'empresa' dos kwargs antes de chamar o super
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        # Se for edição e não passou empresa, tenta pegar da instância
        if not self.empresa and self.instance.pk:
            self.empresa = self.instance.empresa

        if self.empresa:
            # Filtra os campos M2M pela empresa
            self.fields['riscos'].queryset = RiscoOcupacional.objects.filter(empresa=self.empresa)
            
            # --- CORREÇÃO AQUI ---
            # Antes estava EPI.objects.filter (Estoque). Mudamos para TipoEPI.objects.filter (Tipos)
            self.fields['epis'].queryset = TipoEPI.objects.filter(empresa=self.empresa).order_by('nome')
            # ---------------------

            self.fields['vacinas'].queryset = Vacina.objects.filter(empresa=self.empresa)
            self.fields['exames'].queryset = TipoExame.objects.filter(empresa=self.empresa)
            # NRs são globais
            self.fields['normas'].queryset = NormaRegulamentadora.objects.all()
            
            # Se for edição, preenche os campos iniciais
            if self.instance.pk:
                self.fields['riscos'].initial = self.instance.riscos.all()
                self.fields['normas'].initial = self.instance.normas.all()
                self.fields['vacinas'].initial = self.instance.vacinas.all()
                self.fields['exames'].initial = self.instance.exames.all()
                self.fields['epis'].initial = self.instance.epis.all()

    def save(self, commit=True):
        # Salva o setor primeiro
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # Salva os relacionamentos M2M manualmente
            self.save_m2m() 
        return instance

    def save_m2m(self):
        # Método auxiliar para salvar os M2M definidos no Form
        self.instance.riscos.set(self.cleaned_data['riscos'])
        self.instance.normas.set(self.cleaned_data['normas'])
        self.instance.vacinas.set(self.cleaned_data['vacinas'])
        self.instance.exames.set(self.cleaned_data['exames'])
        self.instance.epis.set(self.cleaned_data['epis'])

# --- CARGOS ---

class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = ['nome', 'cbo', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cbo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

# --- EPIs E ESTOQUE ---

class EPIForm(forms.ModelForm):
    # Campo auxiliar (Dropdown de Categorias)
    categoria_filtro = forms.ModelChoiceField(
        queryset=CategoriaEPI.objects.none(), # Começa vazio para não pesar
        label="Categoria (Filtro)",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_categoria_filtro'})
    )

    class Meta:
        model = EPI
        # Note que usamos 'fabricante' aqui, pois é o nome no seu model
        fields = ['tipo', 'fabricante', 'tamanho', 'ca', 'data_validade', 'quantidade', 'local']
        
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select', 'id': 'id_tipo'}),
            'fabricante': forms.Select(attrs={'class': 'form-select', 'id': 'id_fabricante'}),
            'tamanho': forms.Select(attrs={'class': 'form-select', 'id': 'id_tamanho'}),
            'local': forms.Select(attrs={'class': 'form-select', 'id': 'id_local'}),
            'ca': forms.TextInput(attrs={'class': 'form-control'}),
            'data_validade': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        empresa_id = kwargs.pop('empresa_id', None)
        super().__init__(*args, **kwargs)

        if empresa_id:
            # --- AQUI ESTÁ A MÁGICA ---
            # Preenche o dropdown de categorias com as que criamos no script
            self.fields['categoria_filtro'].queryset = CategoriaEPI.objects.filter(empresa_id=empresa_id)
            
            # Preenche os outros campos
            self.fields['fabricante'].queryset = MarcaEPI.objects.filter(empresa_id=empresa_id).order_by('nome')
            self.fields['tamanho'].queryset = TamanhoEPI.objects.filter(empresa_id=empresa_id).order_by('tamanho')
            self.fields['local'].queryset = Localizacao.objects.filter(empresa_id=empresa_id).order_by('nome')

            # Lógica para carregar os Tipos (se categoria foi selecionada ou é edição)
            self.fields['tipo'].queryset = TipoEPI.objects.none()

            # 1. Se o usuário enviou o formulário (POST) e escolheu uma categoria
            if 'categoria_filtro' in self.data:
                try:
                    cat_id = int(self.data.get('categoria_filtro'))
                    self.fields['tipo'].queryset = TipoEPI.objects.filter(categoria_id=cat_id).order_by('nome')
                except (ValueError, TypeError):
                    pass
            
            # 2. Se é edição de um EPI já existente
            elif self.instance.pk and self.instance.tipo:
                # Carrega a categoria original e os tipos dela
                if self.instance.tipo.categoria:
                    self.fields['categoria_filtro'].initial = self.instance.tipo.categoria
                    self.fields['tipo'].queryset = self.instance.tipo.categoria.tipos.all().order_by('nome')


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

# --- FORMS RÁPIDOS (AJAX) ---

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
        fields = [
            'codigo_patrimonial', 'numero_serie', 'classe', 'agente', 'capacidade',
            'fabricante', 'data_fabricacao',
            'empresa', 'localizacao', 'classe_risco', 'andar', 'setor', 'altura_instalacao',
            'sinalizacao_ok', 'acesso_livre',
            'data_instalacao', 'data_ultima_manutencao', 'data_proxima_manutencao', 
            'data_teste_hidrostatico', 'data_ultima_inspecao', 'observacoes',
            'situacao', 'qrcode_imagem'
        ]
        widgets = {
            'codigo_patrimonial': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: EXT-001'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nº do Cilindro'}),
            'classe': forms.Select(attrs={'class': 'form-select'}),
            'agente': forms.Select(attrs={'class': 'form-select'}),
            'capacidade': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 6'}),
            'fabricante': forms.TextInput(attrs={'class': 'form-control'}),
            'data_fabricacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),

            'empresa': forms.Select(attrs={'class': 'form-select'}),
            'localizacao': forms.Select(attrs={'class': 'form-select'}),
            'classe_risco': forms.TextInput(attrs={'class': 'form-control'}),
            'andar': forms.TextInput(attrs={'class': 'form-control'}),
            'setor': forms.TextInput(attrs={'class': 'form-control'}),
            'altura_instalacao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            
            'sinalizacao_ok': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'acesso_livre': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),

            'data_instalacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_ultima_manutencao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_proxima_manutencao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_teste_hidrostatico': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_ultima_inspecao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'situacao': forms.Select(attrs={'class': 'form-select'}),
            'qrcode_imagem': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['localizacao'].queryset = Localizacao.objects.filter(empresa_id=empresa_id)
            self.fields['empresa'].queryset = Empresa.objects.filter(id=empresa_id)
            self.fields['empresa'].initial = empresa_id

class InspecaoExtintorForm(forms.ModelForm):
    class Meta:
        model = InspecaoExtintor
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
        fields = [
            'codigo', 'nome', 'tipo', 'fabricante', 'capacidade',
            'localizacao', 'pavimento',
            'data_instalacao', 'data_ultima_manutencao', 'data_proxima_manutencao',
            'observacoes', 'situacao', 'imagem'
        ]
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: HID-001'}),
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Hidrante Principal'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'fabricante': forms.TextInput(attrs={'class': 'form-control'}),
            'capacidade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 2000L, 30m...'}),
            'localizacao': forms.Select(attrs={'class': 'form-select'}),
            'pavimento': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 1º Andar'}),
            'data_instalacao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_ultima_manutencao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_proxima_manutencao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'situacao': forms.Select(attrs={'class': 'form-select'}),
            'imagem': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['localizacao'].queryset = Localizacao.objects.filter(empresa_id=empresa_id)

class InspecaoEquipamentoForm(forms.ModelForm):
    class Meta:
        model = InspecaoEquipamento
        fields = ['data_inspecao', 'responsavel', 'status', 'observacoes']
        widgets = {
            'data_inspecao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'responsavel': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.TextInput(attrs={'class': 'form-control'}),
        }

# --- QUÍMICOS, HOSPITAIS, CONFIG ---

class ProdutoQuimicoForm(forms.ModelForm):
    class Meta:
        model = ProdutoQuimico
        fields = ['nome', 'cas_number', 'concentracao', 'quantidade', 'unidade', 'setor', 'localizacao', 'classificacao_ghs', 'data_validade_fispq', 'fispq', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cas_number': forms.TextInput(attrs={'class': 'form-control'}),
            'concentracao': forms.TextInput(attrs={'class': 'form-control'}),
            'quantidade': forms.NumberInput(attrs={'class': 'form-control'}),
            'unidade': forms.Select(attrs={'class': 'form-select'}),
            'setor': forms.Select(attrs={'class': 'form-select'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-control'}),
            'classificacao_ghs': forms.TextInput(attrs={'class': 'form-control'}),
            'data_validade_fispq': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['setor'].queryset = Setor.objects.filter(empresa_id=empresa_id)

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
            'agente': forms.TextInput(attrs={'class': 'form-control'}),
            'fonte_geradora': forms.TextInput(attrs={'class': 'form-control'}),
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
            'tipo': forms.TextInput(attrs={'class': 'form-control'}),
            'data_realizacao': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'data_vencimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'arquivo': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ArCondicionadoForm(forms.ModelForm):
    class Meta:
        model = ArCondicionado
        fields = '__all__'
        exclude = ['empresa']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'modelo': forms.TextInput(attrs={'class': 'form-control'}),
            'capacidade_btu': forms.TextInput(attrs={'class': 'form-control'}),
            'gas_refrigerante': forms.TextInput(attrs={'class': 'form-control'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-control'}),
            'setor': forms.TextInput(attrs={'class': 'form-control'}),
            'responsavel_tecnico': forms.TextInput(attrs={'class': 'form-control'}),
            'data_ultima_manutencao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_proxima_manutencao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_ultima_inspecao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_proxima_inspecao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'laudo_tecnico': forms.FileInput(attrs={'class': 'form-control'}),
        }

class EquipamentoNR13Form(forms.ModelForm):
    class Meta:
        model = EquipamentoNR13
        fields = '__all__'
        exclude = ['empresa']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'fabricante': forms.TextInput(attrs={'class': 'form-control'}),
            'numero_serie': forms.TextInput(attrs={'class': 'form-control'}),
            'ano_fabricacao': forms.NumberInput(attrs={'class': 'form-control'}),
            'pressao_trabalho': forms.TextInput(attrs={'class': 'form-control'}),
            'temperatura_trabalho': forms.TextInput(attrs={'class': 'form-control'}),
            'capacidade': forms.TextInput(attrs={'class': 'form-control'}),
            'localizacao': forms.TextInput(attrs={'class': 'form-control'}),
            'setor': forms.TextInput(attrs={'class': 'form-control'}),
            'data_ultima_manutencao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_proxima_manutencao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_ultima_inspecao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'data_proxima_inspecao': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'laudo_tecnico': forms.FileInput(attrs={'class': 'form-control'}),
        }

class TipoExameForm(forms.ModelForm):
    class Meta:
        model = TipoExame
        fields = ['nome', 'codigo_tuss', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_tuss': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class MatrizRiscoEPIForm(forms.ModelForm):
    class Meta:
        model = MatrizRiscoEPI
        fields = ['setor', 'cargo', 'riscos', 'epis_obrigatorios', 'nrs', 'vacinas', 'exames']
        widgets = {
            'setor': forms.Select(attrs={'class': 'form-select'}),
            'cargo': forms.Select(attrs={'class': 'form-select'}),
            'riscos': forms.CheckboxSelectMultiple(),
            'epis_obrigatorios': forms.CheckboxSelectMultiple(),
            'nrs': forms.CheckboxSelectMultiple(),
            'vacinas': forms.CheckboxSelectMultiple(),
            'exames': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, empresa_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if empresa_id:
            self.fields['setor'].queryset = Setor.objects.filter(empresa_id=empresa_id)
            self.fields['cargo'].queryset = Cargo.objects.filter(empresa_id=empresa_id)
            self.fields['epis_obrigatorios'].queryset = TipoEPI.objects.filter(empresa_id=empresa_id)
            self.fields['vacinas'].queryset = Vacina.objects.filter(empresa_id=empresa_id)
        
        self.fields['nrs'].queryset = NormaRegulamentadora.objects.all().order_by('codigo')
        self.fields['riscos'].queryset = RiscoOcupacional.objects.all().order_by('tipo', 'agente')
        self.fields['exames'].queryset = TipoExame.objects.all().order_by('nome')