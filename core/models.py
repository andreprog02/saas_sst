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
# 2. CADASTROS BÁSICOS (NORMAS, RISCOS, VACINAS)
# ==============================================================================

# MOVIDO PARA CIMA (Correção de Erro de Referência)
class NormaRegulamentadora(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self): return f"{self.codigo} - {self.titulo}"

# MOVIDO PARA CIMA (Correção de Erro de Referência)
class RiscoOcupacional(models.Model):
    TIPO_RISCO = [
        ('FISICO', 'Físico'),
        ('QUIMICO', 'Químico'),
        ('BIOLOGICO', 'Biológico'),
        ('ERGONOMICO', 'Ergonômico'),
        ('ACIDENTE', 'Acidente/Mecânico'),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_RISCO)
    nome = models.CharField(max_length=100) # Ex: Ruído, Calor, Poeira
    descricao = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.nome}"

class Vacina(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome da Vacina")
    descricao = models.TextField(blank=True, verbose_name="Descrição")
    meses_reforco = models.IntegerField(default=0, verbose_name="Reforço em (meses)", help_text="0 para dose única ou sem reforço automático")

    def __str__(self): return self.nome

# ==============================================================================
# 3. SETOR E FUNCIONÁRIO
# ==============================================================================

class TipoEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome do Tipo")
    def __str__(self): return self.nome

class Setor(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    descricao = models.TextField(null=True, blank=True)
    responsavel = models.CharField(max_length=100, null=True, blank=True)
    
    # Agora funciona porque as classes estão definidas acima
    normas = models.ManyToManyField(NormaRegulamentadora, blank=True)
    riscos = models.ManyToManyField(RiscoOcupacional, blank=True)

    def __str__(self):
        return self.nome

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
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=14)
    
    # Contato e Documentos
    rg = models.CharField(max_length=20, null=True, blank=True, verbose_name="RG")
    matricula = models.CharField(max_length=20, null=True, blank=True, verbose_name="Matrícula")
    telefone = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    
    data_nascimento = models.DateField(null=True, blank=True)
    cargo = models.CharField(max_length=100)
    setor = models.ForeignKey(Setor, on_delete=models.SET_NULL, null=True)
    data_admissao = models.DateField()
    foto = models.ImageField(upload_to='funcionarios/', null=True, blank=True)
    
    # Status
    situacao = models.CharField(max_length=20, choices=SITUACAO_CHOICES, default='ATIVO')
    motivo_afastamento = models.CharField(max_length=255, null=True, blank=True)
    ativo = models.BooleanField(default=True)

    def __str__(self): return self.nome
        
    @property
    def cor_status(self):
        if self.situacao == 'ATIVO': return 'success'
        if self.situacao == 'FERIAS': return 'info'
        if self.situacao == 'AFASTADO': return 'warning'
        if self.situacao == 'LICENCA': return 'primary'
        if self.situacao == 'SUSPENSO': return 'danger'
        if self.situacao == 'DESLIGADO': return 'dark'
        return 'secondary'

# ==============================================================================
# 4. ESTOQUE DE EPIs
# ==============================================================================

class Localizacao(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome do Local")
    def __str__(self): return self.nome

class CategoriaEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Categoria")
    def __str__(self): return self.nome

class MarcaEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Marca")
    def __str__(self): return self.nome

class TamanhoEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tamanho = models.CharField(max_length=20, verbose_name="Tamanho")
    def __str__(self): return self.tamanho

class EPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    categoria = models.ForeignKey(CategoriaEPI, on_delete=models.PROTECT, null=True, blank=True)
    marca = models.ForeignKey(MarcaEPI, on_delete=models.PROTECT, null=True, blank=True)
    tamanho = models.ForeignKey(TamanhoEPI, on_delete=models.PROTECT, null=True, blank=True)
    
    modelo = models.CharField(max_length=150, null=True, blank=True)
    ca = models.PositiveIntegerField(default=0)
    quantidade = models.PositiveIntegerField(default=0)
    quantidade_minima = models.PositiveIntegerField(default=5)
    data_validade = models.DateField(null=True, blank=True)
    local = models.ForeignKey(Localizacao, on_delete=models.PROTECT, null=True, blank=True)
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

class MovimentacaoEstoque(models.Model):
    TIPO_MOVIMENTO = [('ENTRADA', '➕ Entrada'), ('SAIDA', '➖ Saída')]
    epi = models.ForeignKey(EPI, on_delete=models.CASCADE, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMENTO)
    quantidade = models.PositiveIntegerField()
    data_movimento = models.DateField(default=timezone.now)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.SET_NULL, null=True, blank=True)
    observacao = models.CharField(max_length=255, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.tipo == 'ENTRADA': self.epi.quantidade += self.quantidade
            elif self.tipo == 'SAIDA': self.epi.quantidade -= self.quantidade
            self.epi.save()
        super().save(*args, **kwargs)

# ==============================================================================
# 5. ADVERTÊNCIAS
# ==============================================================================
class TipoAdvertencia(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    descricao_padrao = models.TextField(blank=True)
    def __str__(self): return self.titulo

class Advertencia(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='advertencias')
    tipo = models.ForeignKey(TipoAdvertencia, on_delete=models.PROTECT)
    data_incidente = models.DateField()
    detalhes = models.TextField(blank=True)
    reincidente = models.BooleanField(default=False)
    criado_em = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            if Advertencia.objects.filter(funcionario=self.funcionario, tipo=self.tipo).exists():
                self.reincidente = True
        super().save(*args, **kwargs)

# ==============================================================================
# 6. PRONTUÁRIO
# ==============================================================================
class ControleVacina(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='vacinas')
    vacina = models.ForeignKey(Vacina, on_delete=models.PROTECT)
    data_aplicacao = models.DateField()
    data_proximo_reforco = models.DateField(null=True, blank=True)
    comprovante = models.FileField(upload_to='vacinas_comprovantes/', blank=True, null=True)
    
    def save(self, *args, **kwargs):
        if not self.data_proximo_reforco and self.vacina.meses_reforco > 0:
            self.data_proximo_reforco = self.data_aplicacao + timedelta(days=self.vacina.meses_reforco * 30)
        super().save(*args, **kwargs)

class EntregaEPI(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='epis_entregues')
    epi = models.ForeignKey(EPI, on_delete=models.PROTECT)
    data_entrega = models.DateField(default=timezone.now)
    quantidade = models.IntegerField(default=1)
    ca_registrado = models.CharField(max_length=50)
    validade_ca = models.DateField()
    data_devolucao = models.DateField(null=True, blank=True)
    termo_assinado = models.FileField(upload_to='epis_termos/', blank=True, null=True)

    def save(self, *args, **kwargs):
        is_new = not self.pk
        if is_new:
            self.ca_registrado = str(self.epi.ca)
            if self.epi.data_validade: self.validade_ca = self.epi.data_validade
        super().save(*args, **kwargs)
        if is_new:
             MovimentacaoEstoque.objects.create(
                epi=self.epi, tipo='SAIDA', quantidade=self.quantidade,
                data_movimento=self.data_entrega, funcionario=self.funcionario,
                observacao="Entrega ao funcionário"
            )

class TreinamentoFuncionario(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='treinamentos')
    nome_treinamento = models.CharField(max_length=200)
    data_realizacao = models.DateField()
    data_validade = models.DateField(null=True, blank=True)
    certificado = models.FileField(upload_to='treinamentos_certificados/', blank=True, null=True)
    
    @property
    def vencido(self):
        if not self.data_validade: return False
        return self.data_validade < date.today()

# ==============================================================================
# 7. EXTINTORES E EQUIPAMENTOS
# ==============================================================================
class Extintor(models.Model):
    CLASSES = [('A', 'Classe A'), ('BC', 'Classes B/C'), ('ABC', 'Classes A/B/C')]
    AGENTES = [('AGUA', 'Água'), ('PQS', 'Pó Químico'), ('CO2', 'CO2')]
    SITUACAO = [('ATIVO', 'Ativo'), ('MANUTENCAO', 'Manutenção')]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    codigo_patrimonial = models.CharField(max_length=50)
    numero_serie = models.CharField(max_length=100)
    classe = models.CharField(max_length=5, choices=CLASSES)
    agente = models.CharField(max_length=20, choices=AGENTES)
    capacidade = models.IntegerField()
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT)
    classe_risco = models.CharField(max_length=100)
    data_ultima_manutencao = models.DateField()
    data_proxima_manutencao = models.DateField()
    data_teste_hidrostatico = models.DateField()
    
    # Campo que faltava em alguns forms
    altura_instalacao = models.DecimalField(max_digits=4, decimal_places=2, default=1.50) 
    sinalizacao_ok = models.BooleanField(default=True)
    acesso_livre = models.BooleanField(default=True)
    
    situacao = models.CharField(max_length=20, choices=SITUACAO, default='ATIVO')
    qrcode_imagem = models.ImageField(upload_to='qrcodes_extintores/', blank=True, null=True)

    def __str__(self): return self.codigo_patrimonial

class InspecaoExtintor(models.Model):
    extintor = models.ForeignKey(Extintor, on_delete=models.CASCADE, related_name='inspecoes')
    data_inspecao = models.DateField(default=timezone.now)
    responsavel = models.CharField(max_length=150)
    
    # Campos booleanos de check-list
    lacre_intacto = models.BooleanField(default=True)
    manometro_pressao_ok = models.BooleanField(default=True)
    mangueira_integra = models.BooleanField(default=True)
    
    observacoes = models.TextField(blank=True)

class FotoInspecao(models.Model):
    inspecao = models.ForeignKey(InspecaoExtintor, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='inspecoes_extintores/')

class Equipamento(models.Model):
    TIPOS = [('HIDRANTE', 'Hidrante'), ('ALARME', 'Alarme'), ('LUZ', 'Luz Emergência')]
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    nome = models.CharField(max_length=100)
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT)
    data_validade = models.DateField(null=True, blank=True)
    qrcode_data = models.CharField(max_length=255, blank=True, null=True)

class InspecaoEquipamento(models.Model):
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE, related_name='inspecoes')
    data_inspecao = models.DateField(default=timezone.now)
    responsavel = models.CharField(max_length=150)
    status = models.CharField(max_length=20, default='OK')
    observacoes = models.TextField(blank=True)

class ArquivoInspecao(models.Model):
    inspecao = models.ForeignKey(InspecaoEquipamento, on_delete=models.CASCADE, related_name='arquivos')
    arquivo = models.FileField(upload_to='inspecoes_equipamentos/')

# ==============================================================================
# 8. OUTROS
# ==============================================================================
class Afastamento(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='afastamentos')
    data_inicio = models.DateField()
    data_retorno = models.DateField(null=True, blank=True)
    motivo = models.TextField()
    laudo = models.FileField(upload_to='afastamentos_laudos/', blank=True, null=True)

class AcidenteTrabalho(models.Model):
    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='acidentes')
    data_acidente = models.DateField(verbose_name="Data do Acidente")
    hora_acidente = models.TimeField(verbose_name="Hora", null=True, blank=True)
    local = models.CharField(max_length=255, verbose_name="Local do Acidente", null=True, blank=True)
    arquivo_evidencia = models.FileField(upload_to='acidentes_arquivos/', blank=True, null=True, verbose_name="Arquivo/Evidência")
    descricao_motivo = models.TextField(verbose_name="Descrição do Ocorrido")
    cat_emitida = models.BooleanField(default=False, verbose_name="CAT Emitida?")
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self): return f"Acidente - {self.funcionario.nome}"

class ProdutoQuimico(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    fabricante = models.CharField(max_length=200)
    classificacao = models.CharField(max_length=100, default='Geral')
    data_validade = models.DateField()
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT)
    fispq = models.FileField(upload_to='produtos_quimicos_fispq/', blank=True, null=True)

class TipoEspecialidade(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    def __str__(self): return self.nome

class Hospital(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=50)
    endereco = models.CharField(max_length=255)
    horario_atendimento = models.CharField(max_length=100)
    especialidades = models.ManyToManyField(TipoEspecialidade)
    mapa_link = models.URLField(blank=True, null=True)