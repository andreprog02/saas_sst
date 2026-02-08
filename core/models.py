import os
from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.utils import timezone
from django.core.validators import MinValueValidator

# ==============================================================================
# 1. EMPRESA E PERFIL
# ==============================================================================
class Empresa(models.Model):
    nome_fantasia = models.CharField(max_length=255)
    razao_social = models.CharField(max_length=255)
    cnpj = models.CharField(max_length=18, unique=True, verbose_name="CNPJ")
    telefone = models.CharField(max_length=20)
    email_contato = models.EmailField()
    endereco = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self): return self.nome_fantasia

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='usuarios')
    is_admin = models.BooleanField(default=False)

    def __str__(self): return f"{self.usuario.username} - {self.empresa.nome_fantasia}"

# ==============================================================================
# 2. CADASTROS BÁSICOS (NORMAS, VACINAS)
# ==============================================================================
class NormaRegulamentadora(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self): return f"{self.codigo} - {self.titulo}"

class Vacina(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome da Vacina")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    meses_reforco = models.IntegerField(default=0, verbose_name="Reforço em (meses)", help_text="0 para dose única ou sem reforço automático")

    def __str__(self): return self.nome

# ==============================================================================
# 3. SETOR E FUNCIONÁRIO
# ==============================================================================

# Mantemos TipoEPI aqui para compatibilidade com o modelo Setor (que usa epis_obrigatorios)
class TipoEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome do Tipo")
    def __str__(self): return self.nome

class Setor(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    
    nrs_obrigatorias = models.ManyToManyField(NormaRegulamentadora, blank=True, verbose_name="NRs Aplicáveis")
    vacinas_padrao = models.ManyToManyField(Vacina, blank=True, verbose_name="Vacinas Obrigatórias")
    epis_obrigatorios = models.ManyToManyField(TipoEPI, blank=True, verbose_name="EPIs Obrigatórios por Tipo")
    
    treinamentos = models.TextField(verbose_name="Treinamentos", blank=True)

    def __str__(self): return self.nome

class Funcionario(models.Model):
    SITUACAO_CHOICES = [
        ('ATIVO', '✅ Em Exercício'),
        ('FERIAS', '🏖️ Férias'),
        ('AFASTADO', '🏥 Afastado (INSS/Médico)'),
        ('LICENCA', '👶 Licença Maternidade/Paternidade'),
        ('SUSPENSO', '⚠️ Suspenso'),
        ('DESLIGADO', '❌ Desligado'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14)
    cargo = models.CharField(max_length=100)
    setor = models.ForeignKey(Setor, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Setor de Trabalho")
    data_admissao = models.DateField(verbose_name="Data de Admissão")
    
    situacao = models.CharField(max_length=20, choices=SITUACAO_CHOICES, default='ATIVO', verbose_name="Situação Atual")
    motivo_afastamento = models.TextField(blank=True, verbose_name="Detalhes do Afastamento/Desligamento")
    ativo = models.BooleanField(default=True, verbose_name="Cadastro Ativo no Sistema?")

    def __str__(self): return f"{self.nome} - {self.cargo}"
    
    @property
    def cor_status(self):
        mapping = {
            'ATIVO': 'success', 'FERIAS': 'info', 'AFASTADO': 'warning',
            'LICENCA': 'primary', 'SUSPENSO': 'dark', 'DESLIGADO': 'danger'
        }
        return mapping.get(self.situacao, 'secondary')

# ==============================================================================
# 4. ESTOQUE DE EPIs (REFATORADO COM RASTREABILIDADE)
# ==============================================================================

class Localizacao(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome do Local")
    def __str__(self): return self.nome

# Tabelas Auxiliares para Combobox
class CategoriaEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Categoria", help_text="Ex: Capacete, Luva, Bota")
    def __str__(self): return self.nome

class MarcaEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Marca")
    def __str__(self): return self.nome

class TamanhoEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tamanho = models.CharField(max_length=20, verbose_name="Tamanho", help_text="Ex: P, M, G, 40, 42")
    def __str__(self): return self.tamanho

# Modelo Principal do EPI
class EPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    # Comboboxes (Novos)
    categoria = models.ForeignKey(CategoriaEPI, on_delete=models.PROTECT, verbose_name="Categoria", null=True, blank=True)
    marca = models.ForeignKey(MarcaEPI, on_delete=models.PROTECT, verbose_name="Marca", null=True, blank=True)
    tamanho = models.ForeignKey(TamanhoEPI, on_delete=models.PROTECT, verbose_name="Tamanho", null=True, blank=True)
    
    # Texto e Inteiros
    modelo = models.CharField(max_length=150, verbose_name="Modelo", help_text="Ex: Raspa, Vaqueta, PVC", null=True, blank=True)
    ca = models.PositiveIntegerField(verbose_name="C.A.", help_text="Somente números", default=0)
    
    # Estoque
    quantidade = models.PositiveIntegerField(default=0, verbose_name="Qtd Atual")
    quantidade_minima = models.PositiveIntegerField(default=5, verbose_name="Qtd Mínima")
    data_validade = models.DateField(verbose_name="Validade do CA", null=True, blank=True)
    
    local = models.ForeignKey(Localizacao, on_delete=models.PROTECT, verbose_name="Localização Física", null=True, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self): 
        cat = self.categoria.nome if self.categoria else "Indefinido"
        return f"{cat} {self.modelo} (CA: {self.ca})"
    
    @property
    def status_estoque(self):
        if self.quantidade <= self.quantidade_minima:
            return {'cor': 'danger', 'texto': 'Crítico', 'icon': '⚠️'}
        elif self.quantidade <= (self.quantidade_minima * 1.2):
            return {'cor': 'warning', 'texto': 'Baixo', 'icon': '⚡'}
        return {'cor': 'success', 'texto': 'OK', 'icon': '✅'}
    
    
    @property
    def status_estoque(self):
        if self.quantidade <= self.quantidade_minima:
            return {'cor': 'danger', 'texto': 'Estoque Crítico', 'icon': '⚠️'}
        elif self.quantidade <= (self.quantidade_minima * 1.2):
            return {'cor': 'warning', 'texto': 'Estoque Baixo', 'icon': '⚡'}
        else:
            return {'cor': 'success', 'texto': 'Estoque OK', 'icon': '✅'}

# Rastreabilidade (Histórico)
class MovimentacaoEstoque(models.Model):
    TIPO_MOVIMENTO = [
        ('ENTRADA', '➕ Entrada (Compra/Devolução)'),
        ('SAIDA', '➖ Saída (Entrega/Descarte)'),
    ]

    epi = models.ForeignKey(EPI, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMENTO)
    quantidade = models.PositiveIntegerField()
    data_movimento = models.DateField(default=timezone.now)
    
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Funcionário")
    observacao = models.CharField(max_length=255, blank=True, verbose_name="Motivo/Detalhes")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"{self.get_tipo_display()} - {self.quantidade} un."

    def save(self, *args, **kwargs):
        # Atualiza o saldo do EPI ao salvar o histórico (apenas se for novo registro)
        if not self.pk:
            if self.tipo == 'ENTRADA':
                self.epi.quantidade += self.quantidade
            elif self.tipo == 'SAIDA':
                self.epi.quantidade -= self.quantidade
            self.epi.save()
        super().save(*args, **kwargs)

# ==============================================================================
# 5. ADVERTÊNCIAS
# ==============================================================================
class TipoAdvertencia(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100, verbose_name="Motivo da Falta")
    descricao_padrao = models.TextField(verbose_name="Texto Padrão", blank=True)
    def __str__(self): return self.titulo

class Advertencia(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='advertencias')
    tipo = models.ForeignKey(TipoAdvertencia, on_delete=models.PROTECT, verbose_name="Motivo")
    data_incidente = models.DateField(verbose_name="Data do Ocorrido")
    detalhes = models.TextField(verbose_name="Observações", blank=True)
    reincidente = models.BooleanField(default=False, verbose_name="É reincidente?")
    criado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            if Advertencia.objects.filter(funcionario=self.funcionario, tipo=self.tipo).exists():
                self.reincidente = True
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.funcionario.nome} - {self.tipo.titulo}"

# ==============================================================================
# 6. PRONTUÁRIO (VACINAS, ENTREGA EPIs, TREINAMENTOS)
# ==============================================================================
class ControleVacina(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='vacinas')
    vacina = models.ForeignKey(Vacina, on_delete=models.PROTECT)
    data_aplicacao = models.DateField(verbose_name="Data da Aplicação")
    data_proximo_reforco = models.DateField(null=True, blank=True, verbose_name="Próximo Reforço")
    comprovante = models.FileField(upload_to='vacinas_comprovantes/', blank=True, null=True, verbose_name="Comprovante")
    
    def save(self, *args, **kwargs):
        if not self.data_proximo_reforco and self.vacina.meses_reforco > 0:
            self.data_proximo_reforco = self.data_aplicacao + timedelta(days=self.vacina.meses_reforco * 30)
        super().save(*args, **kwargs)

    @property
    def status(self):
        if not self.data_proximo_reforco: return "Dia"
        hj = date.today()
        if self.data_proximo_reforco < hj: return "Vencida"
        if (self.data_proximo_reforco - hj).days <= 30: return "A vencer"
        return "Em dia"

class EntregaEPI(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='epis_entregues')
    epi = models.ForeignKey(EPI, on_delete=models.PROTECT, verbose_name="Item do Estoque")
    data_entrega = models.DateField(default=timezone.now)
    quantidade = models.IntegerField(default=1)
    
    ca_registrado = models.CharField(max_length=50, verbose_name="CA na Entrega")
    validade_ca = models.DateField(verbose_name="Validade do CA")
    data_devolucao = models.DateField(null=True, blank=True, verbose_name="Data de Devolução/Troca")
    termo_assinado = models.FileField(upload_to='epis_termos/', blank=True, null=True, verbose_name="Ficha Assinada")

    def save(self, *args, **kwargs):
        is_new = not self.pk
        if is_new:
            self.ca_registrado = str(self.epi.ca)
            if self.epi.data_validade:
                self.validade_ca = self.epi.data_validade
        
        super().save(*args, **kwargs)
        
        # Gera movimentação de SAÍDA automaticamente
        if is_new:
             MovimentacaoEstoque.objects.create(
                epi=self.epi,
                tipo='SAIDA',
                quantidade=self.quantidade,
                data_movimento=self.data_entrega,
                funcionario=self.funcionario,
                observacao="Entrega ao funcionário (Automático)"
            )

class TreinamentoFuncionario(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='treinamentos')
    nome_treinamento = models.CharField(max_length=200, verbose_name="Nome do Curso/Treinamento")
    data_realizacao = models.DateField(verbose_name="Data Realização")
    data_validade = models.DateField(null=True, blank=True, verbose_name="Validade")
    certificado = models.FileField(upload_to='treinamentos_certificados/', blank=True, null=True)
    
    def __str__(self): return self.nome_treinamento

    @property
    def vencido(self):
        if not self.data_validade: return False
        return self.data_validade < date.today()

# ==============================================================================
# 7. GESTÃO DE EXTINTORES E EQUIPAMENTOS
# ==============================================================================
class Extintor(models.Model):
    CLASSES_INCENDIO = [('A', 'Classe A'), ('B', 'Classe B'), ('C', 'Classe C'), ('D', 'Classe D'), ('K', 'Classe K'), ('BC', 'Classes B/C'), ('ABC', 'Classes A/B/C')]
    AGENTES = [('AGUA', 'Água'), ('PQS', 'Pó Químico'), ('CO2', 'CO2'), ('ESPUMA', 'Espuma'), ('ACETATO', 'Acetato')]
    SITUACAO = [('ATIVO', 'Ativo'), ('MANUTENCAO', 'Em Manutenção'), ('RESERVA', 'Reserva'), ('CONDENADO', 'Condenado')]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    codigo_patrimonial = models.CharField(max_length=50, verbose_name="Cód. Patrimonial")
    numero_serie = models.CharField(max_length=100, verbose_name="Nº Série")
    classe = models.CharField(max_length=5, choices=CLASSES_INCENDIO)
    agente = models.CharField(max_length=20, choices=AGENTES)
    capacidade = models.IntegerField(verbose_name="Capacidade (kg/L)")
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT)
    classe_risco = models.CharField(max_length=100, verbose_name="Risco do Local")
    data_ultima_manutencao = models.DateField(verbose_name="Última Recarga")
    data_proxima_manutencao = models.DateField(verbose_name="Vencimento Recarga")
    data_teste_hidrostatico = models.DateField(verbose_name="Vencimento Teste Hidrostático")
    empresa_mantenedora = models.CharField(max_length=200, blank=True)
    numero_lacre = models.CharField(max_length=50, blank=True)
    situacao = models.CharField(max_length=20, choices=SITUACAO, default='ATIVO')
    altura_instalacao = models.DecimalField(max_digits=4, decimal_places=2)
    sinalizacao_ok = models.BooleanField(default=True)
    acesso_livre = models.BooleanField(default=True)
    qrcode_imagem = models.ImageField(upload_to='qrcodes_extintores/', blank=True, null=True)

    def __str__(self): return f"{self.codigo_patrimonial} ({self.get_agente_display()})"
    
    @property
    def alerta_manutencao(self):
        if not self.data_proxima_manutencao: return False
        return (self.data_proxima_manutencao - date.today()).days <= 30

class InspecaoExtintor(models.Model):
    extintor = models.ForeignKey(Extintor, on_delete=models.CASCADE, related_name='inspecoes')
    data_inspecao = models.DateField(default=timezone.now)
    responsavel = models.CharField(max_length=150)
    lacre_intacto = models.BooleanField(default=True)
    manometro_pressao_ok = models.BooleanField(default=True)
    sinalizacao_visivel = models.BooleanField(default=True)
    acesso_livre = models.BooleanField(default=True)
    mangueira_integra = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)
    
    def __str__(self): return f"Inspeção {self.extintor.codigo_patrimonial} em {self.data_inspecao}"
    
class FotoInspecao(models.Model):
    inspecao = models.ForeignKey(InspecaoExtintor, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='inspecoes_extintores/')
    data_upload = models.DateTimeField(auto_now_add=True)

class Equipamento(models.Model):
    TIPOS = [('HIDRANTE', 'Hidrante'), ('MANGUEIRA', 'Mangueira'), ('ALARME', 'Alarme'), ('LUZ', 'Luz Emergência'), ('PLACA', 'Placa'), ('PORTA', 'Porta Corta-Fogo'), ('OUTRO', 'Outros')]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    nome = models.CharField(max_length=100)
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT)
    data_instalacao = models.DateField(null=True, blank=True)
    data_validade = models.DateField(null=True, blank=True)
    especificacao = models.CharField(max_length=255, blank=True)
    ativo = models.BooleanField(default=True)
    imagem = models.ImageField(upload_to='outros_equipamentos/', blank=True, null=True)

    def __str__(self): return f"{self.get_tipo_display()} - {self.nome}"
    
    @property
    def status_validade(self):
        if not self.data_validade: return "ok"
        dias = (self.data_validade - date.today()).days
        if dias < 0: return "vencido"
        if dias <= 30: return "alerta"
        return "ok"

class InspecaoEquipamento(models.Model):
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE, related_name='inspecoes')
    data_inspecao = models.DateField(default=timezone.now)
    responsavel = models.CharField(max_length=150)
    item_integro = models.BooleanField(default=True)
    acesso_livre = models.BooleanField(default=True)
    sinalizacao_ok = models.BooleanField(default=True)
    teste_funcional = models.BooleanField(default=True)
    observacoes = models.TextField(blank=True)

class ArquivoInspecao(models.Model):
    inspecao = models.ForeignKey(InspecaoEquipamento, on_delete=models.CASCADE, related_name='arquivos')
    arquivo = models.FileField(upload_to='inspecoes_equipamentos/')
    data_upload = models.DateTimeField(auto_now_add=True)
    
    @property
    def eh_imagem(self):
        ext = os.path.splitext(self.arquivo.name)[1].lower()
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']

# ==============================================================================
# 8. OUTROS (AFASTAMENTO, ACIDENTE, QUÍMICOS, HOSPITAIS)
# ==============================================================================
class Afastamento(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='afastamentos')
    data_inicio = models.DateField(verbose_name="Data de Início")
    data_retorno = models.DateField(null=True, blank=True)
    motivo = models.TextField(verbose_name="Motivo / CID")
    laudo = models.FileField(upload_to='afastamentos_laudos/', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    @property
    def dias_afastado(self):
        if self.data_retorno: return (self.data_retorno - self.data_inicio).days
        return (date.today() - self.data_inicio).days

class AcidenteTrabalho(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='acidentes')
    data_acidente = models.DateField(verbose_name="Data do Acidente")
    hora_acidente = models.TimeField(verbose_name="Hora")
    local = models.CharField(max_length=255, verbose_name="Local do Acidente")
    descricao_motivo = models.TextField(verbose_name="Descrição")
    arquivo_evidencia = models.FileField(upload_to='acidentes_arquivos/', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

class ProdutoQuimico(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200, verbose_name="Nome do Produto")
    fabricante = models.CharField(max_length=200, verbose_name="Fabricante")
    riscos = models.TextField(verbose_name="Riscos")
    telefone_emergencia = models.CharField(max_length=50)
    lote = models.CharField(max_length=50, blank=True)
    data_fabricacao = models.DateField(null=True, blank=True)
    data_validade = models.DateField()
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT)
    quantidade = models.CharField(max_length=50)
    fispq = models.FileField(upload_to='produtos_quimicos_fispq/', blank=True, null=True)
    foto_rotulo = models.ImageField(upload_to='produtos_quimicos_fotos/', blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.nome
    
    @property
    def status_validade(self):
        dias = (self.data_validade - date.today()).days
        if dias < 0: return "vencido"
        if dias <= 30: return "alerta"
        return "ok"

class TipoEspecialidade(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class Hospital(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=50)
    endereco = models.CharField(max_length=255)
    horario_atendimento = models.CharField(max_length=100, default="24 Horas")
    especialidades = models.ManyToManyField(TipoEspecialidade)
    mapa_link = models.URLField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.nome