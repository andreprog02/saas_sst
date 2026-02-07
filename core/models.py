from django.db import models
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.utils import timezone



# 1. EMPRESA
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

# 2. PERFIL DE USUÁRIO
class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='usuarios')
    is_admin = models.BooleanField(default=False)

    def __str__(self): return f"{self.usuario.username} - {self.empresa.nome_fantasia}"

# 3. NORMAS E VACINAS (Cadastros Básicos)
class NormaRegulamentadora(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    titulo = models.CharField(max_length=255)
    descricao = models.TextField(blank=True, null=True)

    def __str__(self): return f"{self.codigo} - {self.titulo}"

class Vacina(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome da Vacina")
    descricao = models.TextField(blank=True, verbose_name="Descrição/Periodicidade")

    def __str__(self): return self.nome

# 4. SETOR (Ambiente de Trabalho)
class Setor(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100) # O ERRO ESTAVA AQUI (Se faltar essa linha, quebra)
    
    # Relacionamentos M2M (Muitos para Muitos)
    nrs_obrigatorias = models.ManyToManyField(NormaRegulamentadora, blank=True, verbose_name="NRs Aplicáveis")
    vacinas_padrao = models.ManyToManyField(Vacina, blank=True, verbose_name="Vacinas Obrigatórias")
    
    # Campos de Texto Livre
    epis_obrigatorios = models.TextField(verbose_name="EPIs Obrigatórios", blank=True)
    treinamentos = models.TextField(verbose_name="Treinamentos", blank=True)

    def __str__(self): return self.nome

# 5. FUNCIONÁRIO
class Funcionario(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14)
    cargo = models.CharField(max_length=100)
    setor = models.ForeignKey(Setor, on_delete=models.PROTECT, null=True, blank=True, verbose_name="Setor de Trabalho")
    data_admissao = models.DateField(verbose_name="Data de Admissão")
    ativo = models.BooleanField(default=True)

    def __str__(self): return f"{self.nome} - {self.cargo}"

# 6. ESTOQUE DE EPIs
class TipoEPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome do Tipo")
    def __str__(self): return self.nome

class Localizacao(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100, verbose_name="Nome do Local")
    def __str__(self): return self.nome

class EPI(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    tipo = models.ForeignKey(TipoEPI, on_delete=models.PROTECT, verbose_name="Tipo de EPI")
    local = models.ForeignKey(Localizacao, on_delete=models.PROTECT, verbose_name="Localização")
    codigo_unico = models.CharField(max_length=50, verbose_name="Código Interno")
    tamanho = models.CharField(max_length=20, verbose_name="Tamanho")
    ca = models.CharField(max_length=50, verbose_name="C.A.")
    quantidade = models.IntegerField(default=0)
    data_validade = models.DateField(null=True, blank=True, verbose_name="Validade")

    def __str__(self): return f"{self.tipo.nome} - {self.tamanho}"

# 7. ADVERTÊNCIAS
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
            historico = Advertencia.objects.filter(funcionario=self.funcionario, tipo=self.tipo).exists()
            if historico: self.reincidente = True
        super().save(*args, **kwargs)

    def __str__(self): return f"{self.funcionario.nome} - {self.tipo.titulo}"



# 10. GESTÃO DE EXTINTORES
class Extintor(models.Model):
    CLASSES_INCENDIO = [
        ('A', 'Classe A'), ('B', 'Classe B'), ('C', 'Classe C'), 
        ('D', 'Classe D'), ('K', 'Classe K'), 
        ('BC', 'Classes B/C'), ('ABC', 'Classes A/B/C')
    ]
    AGENTES = [
        ('AGUA', 'Água Pressurizada'), ('PQS', 'Pó Químico Seco (PQS)'), 
        ('CO2', 'Gás Carbônico (CO2)'), ('ESPUMA', 'Espuma Mecânica'), 
        ('ACETATO', 'Acetato de Potássio')
    ]
    SITUACAO = [
        ('ATIVO', 'Ativo'), ('MANUTENCAO', 'Em Manutenção'), 
        ('RESERVA', 'Reserva'), ('CONDENADO', 'Condenado')
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    
    # Identificação
    codigo_patrimonial = models.CharField(max_length=50, verbose_name="Cód. Patrimonial", help_text="Ex: EXT-01")
    numero_serie = models.CharField(max_length=100, verbose_name="Nº de Série Cilindro")
    classe = models.CharField(max_length=5, choices=CLASSES_INCENDIO, verbose_name="Classe")
    agente = models.CharField(max_length=20, choices=AGENTES, verbose_name="Agente Extintor")
    capacidade = models.IntegerField(verbose_name="Capacidade (kg/L)")
    
    # Localização
    localizacao = models.ForeignKey(Localizacao, on_delete=models.PROTECT, verbose_name="Local Físico")
    classe_risco = models.CharField(max_length=100, verbose_name="Risco do Local", help_text="Ex: Risco Leve, Risco de Elétrica")

    # Manutenção
    data_ultima_manutencao = models.DateField(verbose_name="Última Recarga")
    data_proxima_manutencao = models.DateField(verbose_name="Vencimento Recarga")
    data_teste_hidrostatico = models.DateField(verbose_name="Vencimento Teste Hidrostático (5 anos)")
    empresa_mantenedora = models.CharField(max_length=200, blank=True)
    numero_lacre = models.CharField(max_length=50, blank=True)

    # Operacional
    situacao = models.CharField(max_length=20, choices=SITUACAO, default='ATIVO', verbose_name="Situação Atual")
    altura_instalacao = models.DecimalField(max_digits=4, decimal_places=2, verbose_name="Altura (m)")
    sinalizacao_ok = models.BooleanField(default=True, verbose_name="Sinalização OK?")
    acesso_livre = models.BooleanField(default=True, verbose_name="Acesso Desobstruído?")

    qrcode_imagem = models.ImageField(upload_to='qrcodes_extintores/', blank=True, null=True, verbose_name="QR Code Registrado")

    def __str__(self):
        return f"{self.codigo_patrimonial} ({self.get_agente_display()})"

    @property
    def alerta_manutencao(self):
        """Retorna True se faltar 30 dias ou menos para recarga"""
        if not self.data_proxima_manutencao: return False
        return (self.data_proxima_manutencao - date.today()).days <= 30

    @property
    def alerta_hidrostatico(self):
        """Retorna True se faltar 30 dias ou menos para teste hidrostático"""
        if not self.data_teste_hidrostatico: return False
        return (self.data_teste_hidrostatico - date.today()).days <= 30

# 11. HISTÓRICO DE INSPEÇÕES MENSAIS
class InspecaoExtintor(models.Model):
    extintor = models.ForeignKey(Extintor, on_delete=models.CASCADE, related_name='inspecoes')
    data_inspecao = models.DateField(default=timezone.now)
    responsavel = models.CharField(max_length=150)
    
    # Itens do Checklist Simplificado
    lacre_intacto = models.BooleanField(default=True, verbose_name="Lacre Intacto?")
    manometro_pressao_ok = models.BooleanField(default=True, verbose_name="Pressão OK?")
    sinalizacao_visivel = models.BooleanField(default=True, verbose_name="Sinalização Visível?")
    acesso_livre = models.BooleanField(default=True, verbose_name="Acesso Livre?")
    mangueira_integra = models.BooleanField(default=True, verbose_name="Mangueira Íntegra?")
    
    observacoes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Inspeção {self.extintor.codigo_patrimonial} em {self.data_inspecao}"
    
class FotoInspecao(models.Model):
    inspecao = models.ForeignKey(InspecaoExtintor, on_delete=models.CASCADE, related_name='fotos')
    imagem = models.ImageField(upload_to='inspecoes_extintores/', verbose_name="Foto")
    data_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Foto da inspeção {self.inspecao.id}"